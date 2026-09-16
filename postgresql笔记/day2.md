# PostgreSQL：B树索引原理 + EXPLAIN 执行计划 + 单表查询优化
> 重点区分：**PostgreSQL 表是堆表（Heap），没有聚簇索引**；默认索引叫 `btree`，内部实现是B+树变体（Lehman-Yao），文档统一叫B-Tree索引，面试直接说PG B树索引即可

## 一、PostgreSQL 索引基础 & B树索引原理
### 1. 核心架构区别（对比MySQL InnoDB）
- MySQL InnoDB：**聚簇索引**，主键索引就是表本身，二级索引叶子存主键
- PostgreSQL：**堆表Heap**，表数据无序存放在堆里；**所有索引都是二级索引**，索引独立于表存储
- B树索引叶子节点：存储 `索引键 + TID（Tuple ID，(页号+行内偏移)，指向堆里的行）`，查到TID后去堆读取完整行（回表）
- 页大小默认：**8KB**（MySQL是16KB）

### 2. PG B树（B+变体）结构
三层结构：元数据页 → 根节点 → 内部节点 → 叶子节点
1. **内部节点**：只存分隔key + 子页指针，不存行数据，用于路由查找
2. **叶子节点**：索引key + TID；**叶子节点双向链表有序串联**，支持范围扫描、order by
3. 树高度很低：千万级数据一般3~4层，每次查询最多3~4次磁盘IO
4. 特性：
    - 支持等值 `=`、范围 `> < >= <= between`、前缀like、排序、group by
    - 支持**索引仅扫描 Index Only Scan**（覆盖索引，不需要回堆表），但有MVCC可见性校验（Heap Fetch，PG特殊点）
    - 联合索引遵守**最左前缀原则**

> PG B树不会自动合并页（删除后页不会合并），大量删除会产生索引空洞，需要VACUUM清理死元组，防止索引膨胀

### 3. 索引仅扫描 Index Only Scan（覆盖索引）
查询所有字段都在索引中，理论上不需要访问堆表。
⚠️ PG MVCC机制：索引里没有行版本可见性信息，PG需要检查堆页面的**可见性映射VM**；如果VM标记页面全部可见，就完全不访问堆；否则依然要回堆校验（这是和MySQL覆盖索引最大差异）。

### 4. PG其他索引类型（顺带了解）
- B-Tree：默认，等值/范围/排序
- Hash：仅等值查询，不支持范围排序
- GIN：倒排索引，数组、jsonb、全文检索
- GiST：几何、距离查询
- BRIN：超大时序表，块级索引，占用极小

## 二、EXPLAIN 执行计划分析（PostgreSQL）
### 基础命令
```sql
EXPLAIN SELECT ...; -- 只预估，不执行
EXPLAIN ANALYZE SELECT ...; -- 真实执行，输出预估+真实行数、耗时（生产谨慎，会跑SQL）
EXPLAIN (ANALYZE, BUFFERS) SELECT ...; -- 额外看缓存命中、磁盘读
```
> 可视化工具：explain.depesz.com，粘贴计划看树状图

### 扫描算子（最重要，优先级从好到差）
1. **Index Only Scan**：索引仅扫描（覆盖索引，最优，尽量追求）
2. **Index Scan**：B树索引扫描，拿到TID回堆表取数据
3. **Bitmap Index Scan + Bitmap Heap Scan**：位图索引扫描
    - 先索引匹配，收集满足条件的TID，排序后批量访问堆表，减少随机IO；适合多条件组合、多行命中场景
4. **Seq Scan（Sequential Scan）**：顺序扫描 = 全表扫描，最差
> PG优化器会自动选择：如果预估返回行数占表比例很高（>20%左右），直接选Seq Scan，不走索引，这是合理选择，不是bug

### 计划节点关键字段含义
```
Index Scan using idx_name on t  (cost=0.43..8.45 rows=1 width=44) (actual time=0.02..0.04 rows=1 loops=1)
```
- `cost`：预估代价，启动代价..总代价（单位是随机IO成本，不是毫秒）
- `rows`：**预估返回行数**，统计信息不准时这个值偏差很大
- `width`：预估单行字节大小
- `actual time`：真实执行耗时（EXPLAIN ANALYZE才有）
- `actual rows`：真实返回行数
- `loops`：循环次数

### 常见额外节点
- Sort：内存排序；如果数据量大内存不够，会落盘做外部排序（代价很高），对应MySQL的Using filesort
- HashAggregate：分组聚合，内存哈希
- GroupAggregate：利用索引有序做分组，性能更好，避免排序
- Filter：读取行之后再过滤（不是索引过滤）

### 优化器坑点
PG优化器依赖**统计信息pg_statistic**；大批量导入/删除数据后，统计信息过时，会选错执行计划。
```sql
ANALYZE table_name; -- 更新表统计信息
```

## 三、PostgreSQL 单表查询优化
### 1. B树索引设计原则
1. where、order by、group by字段优先建索引；**联合索引：等值字段放前面，范围字段放后面**
    ```sql
    -- where a=1 and b>2 and c=3
    create index idx_t_a_b on t(a,b); -- c无法使用索引，范围后失效
    ```
2. 联合索引最左前缀：`(a,b,c)`，支持 `where a` / `where a and b` / `where a and b and c`；**不能单独用b、c**
3. 覆盖索引：把查询字段包含进索引，开启Index Only Scan
    ```sql
    -- 原查询 select id,name from t where phone='123'
    create index idx_phone_covering on t(phone) include(id,name);
    ```
    ✅ PG 11+支持`INCLUDE`子句，把非索引键附加到索引叶子，不参与排序，减小索引体积（推荐，比写在索引列里好）
4. 低基数字段不要单独建索引（status 0/1）；高频查询固定值可以用**部分索引 Partial Index**
    ```sql
    create index idx_status_active on t(id) where status=1; -- 只给status=1建索引，索引体积小
    ```
5. 表达式索引：索引列需要函数运算时，不要在where里套函数，直接建表达式索引
    ```sql
    -- ❌ where lower(email)='xxx' 普通索引失效
    create index idx_email_lower on t(lower(email));
    ```
6. 索引不宜过多：写操作（insert/update/delete）维护B树，产生WAL日志，增加开销；PG还要维护索引TID。

### 2. B树索引失效场景（高频考点）
❌ 索引列做函数、运算、类型转换：`where id+1=100`、`where lower(col)='xx'`（普通索引无法使用，要用表达式索引）
❌ `like '%abc'` 前缀通配符，B树无法使用；`like 'abc%'` 可以走B树；模糊全文检索用pg_trgm索引
❌ 联合索引不满足最左前缀
❌ 选择性太差，返回大量行，优化器主动放弃索引，选择Seq Scan（合理行为）
❌ 统计信息过时，ANALYZE修复
❌ 排序方向、索引排序不一致（asc/desc不匹配）

> 注意：`!=`、`is not null` 不是绝对失效，取决于选择性，PG依然有可能走索引。

### 3. where 查询优化
1. 禁止`select *`，只取需要字段，方便构建覆盖索引（INCLUDE）
2. 尽量把计算放在常量侧，不要放在索引列侧
    ```sql
    -- ✅ 推荐
    where create_time >= '2026-01-01'
    -- ❌ 不推荐
    where date(create_time) = '2026-01-01'
    ```
3. in不要带超大集合，过多值优化器会放弃索引
4. 合理使用部分索引，减少索引大小

### 4. order by & group by 优化
核心：**利用索引天然有序，消除Sort节点**
- order by字段顺序、排序方向和B树索引完全一致，可直接读取有序索引，不需要Sort
- group by如果索引有序，会走GroupAggregate，避免Sort + HashAggregate的开销
> 多字段排序，索引的asc/desc必须匹配，否则无法利用索引排序

### 5. limit 大偏移分页优化
`offset 100000 limit 10`，PG会扫描并丢弃前面10w行，性能差
优化方案：书签分页（主键定位）
```sql
-- 假设id主键有序
select * from t where id > 100000 limit 10;
```
> 注意：主键id必须连续有序；如果存在删除空洞，需要业务兼容。

### 6. PG索引维护（很重要，MySQL没有这个痛点）
PG MVCC会产生大量死元组，索引保留旧TID，索引膨胀：
- `VACUUM t;`：清理死元组，标记索引死条目，减少回堆
- `VACUUM ANALYZE t;`：清理+更新统计信息
- `REINDEX INDEX idx_name;`：重建膨胀索引，回收空间

## 四、PG vs MySQL(InnoDB) 面试对比总结
| 项目 | PostgreSQL(B树) | MySQL InnoDB(B+树) |
|---|---|---|
| 表组织 | 堆表Heap，无聚簇索引 | 聚簇索引，主键就是表 |
| 索引叶子 | 索引key + TID(页+偏移) | 二级索引叶子存主键 |
| 回表 | TID去堆取行 | 拿到主键，回聚簇索引 |
| 覆盖索引 | Index Only Scan，需要VM可见性校验 | 直接读取索引，无需回表 |
| 联合索引 | 最左前缀，支持INCLUDE | 最左前缀，无INCLUDE |
| 页大小 | 默认8KB | 默认16KB |
| 索引删除 | 不自动合并页，容易膨胀，需要VACUUM | 页可合并 |

## 面试精简背诵版
1. PG默认B树索引，底层是B+变体；PG是堆表，没有聚簇索引，所有索引都是二级索引，叶子存TID，回表访问堆。
2. Index Only Scan是PG覆盖索引，但受MVCC可见性映射VM限制，不一定完全不访问堆。
3. EXPLAIN重点看扫描算子：Index Only Scan > Index Scan > Bitmap Scan > Seq Scan；Sort节点是性能隐患。EXPLAIN ANALYZE会真实执行SQL。
4. 联合索引遵守最左前缀，等值在前范围在后；表达式查询要建表达式索引，高频少量值用部分索引+INCLUDE做覆盖索引。
5. PG索引失效很多是函数包裹索引列、前缀like；还有一种情况：选择性差，优化器主动选顺序扫描，不是索引坏了；大批量变更后要ANALYZE更新统计信息，定期VACUUM防止索引膨胀。

如果你需要，我可以：
1. 写一套PG可直接执行的SQL，配合EXPLAIN ANALYZE演示 Index Only Scan、Bitmap Scan、Seq Scan、索引失效；
2. 整理成面试问答题库；
3. 给PG索引调优排查清单。