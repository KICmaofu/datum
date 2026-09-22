# PostgreSQL 多表联查、子查询、聚合函数
> 承接前面 PG 事务/锁、索引的知识点，下面是原理 + 示例 + 坑点，适合面试和实操

## 一、多表联查（JOIN）
PG 支持标准 SQL 的 5 种 JOIN，底层执行器会根据统计信息选择：**Nested Loop / Hash Join / Merge Join**
### 1. JOIN 类型
假设有两张表：`user(id, name)`、`order(id, user_id, amount)`
1. **INNER JOIN 内连接**：只返回两边匹配上的数据
```sql
SELECT u.name, o.amount
FROM "user" u
INNER JOIN "order" o ON u.id = o.user_id;
```
等价于 `JOIN`，不写 INNER 默认就是内连接

2. **LEFT JOIN（LEFT OUTER JOIN）左外连接**：左表全部保留，右表匹配不到填 NULL
```sql
SELECT u.name, o.amount
FROM "user" u
LEFT JOIN "order" o ON u.id = o.user_id;
```
> ⚠️ 坑：`WHERE o.amount = 100` 会把 NULL 过滤掉，变成 INNER JOIN；过滤右表条件写在 ON 后面

3. **RIGHT JOIN 右外连接**：右表全部保留，左表无匹配为 NULL
4. **FULL OUTER JOIN 全外连接**：左右表全部保留，不匹配字段为 NULL（MySQL 不支持，PG原生支持）
```sql
SELECT u.name, o.amount
FROM "user" u
FULL OUTER JOIN "order" o ON u.id = o.user_id;
```
5. **CROSS JOIN 笛卡尔积**：没有 ON 条件，左表行数 × 右表行数，慎用！

### 2. PG 三种 JOIN 底层算法（面试高频）
1. **Nested Loop 嵌套循环**
小表驱动大表，循环遍历。适合驱动表数据量很小、被关联字段有索引。
`小表 → 循环每一行，去大表索引查找匹配行`
2. **Hash Join 哈希连接**
没有合适索引、数据量大时常用。把驱动表载入内存，构建 hash 表；扫描另一张表做 hash 匹配。
> 内存不够会溢写到磁盘，性能暴跌，可以调 `work_mem`
3. **Merge Join 归并连接**
两张表关联字段都有序（有索引或者排序后），两个有序列表类似归并排序逐行对比。适合大数据量且两边已经排序。

> EXPLAIN 可以看到实际选用的 join 类型

## 二、子查询
PG 子查询分为：标量子查询、列子查询、表子查询；还有相关子查询 vs 非相关子查询
### 1. 非相关子查询（子查询独立执行，只跑一次）
```sql
-- 标量子查询：返回单行单列
SELECT name FROM "user" WHERE id = (SELECT user_id FROM "order" WHERE id=100);

-- IN 子查询，返回多行单列
SELECT name FROM "user" WHERE id IN (SELECT user_id FROM "order" WHERE amount > 1000);
```

### 2. 相关子查询（依赖外层查询，外层每一行都会执行一次子查询，性能差）
```sql
-- 查询有订单的用户
SELECT u.name
FROM "user" u
WHERE EXISTS (
    SELECT 1 FROM "order" o WHERE o.user_id = u.id
);
```
✅ **EXISTS 推荐优先用**：找到第一条匹配就停止扫描，比 IN 好；数据量大时差距明显。
> 注意：`NOT IN` 如果子查询返回有 NULL，结果直接为空，是经典坑；优先用 `NOT EXISTS`

### 3. 表子查询（FROM 后面，也叫派生表）
```sql
SELECT t.name FROM (SELECT name,id FROM "user" WHERE id>100) AS t;
```
PG 还支持 **CTE（WITH）**，属于公用表表达式：
```sql
WITH user_order AS (
    SELECT user_id, sum(amount) AS total FROM "order" GROUP BY user_id
)
SELECT u.name,uo.total FROM "user" u LEFT JOIN user_order uo ON u.id=uo.user_id;
```
> PG 12 之前：WITH 是优化栅栏，不会被主查询下推；PG12+ CTE 可以内联优化，和派生表类似。

## 三、常用聚合函数
聚合函数对一组行计算，返回单行；**聚合函数会忽略 NULL 值**
|函数|作用|
| ---- | ---- |
|`COUNT(*)`|统计行数，不会忽略NULL|
|`COUNT(字段)`|统计该字段非NULL行数|
|`COUNT(DISTINCT col)`|去重计数|
|`SUM(col)`|求和，忽略NULL|
|`AVG(col)`|平均值，忽略NULL|
|`MAX(col)`|最大值|
|`MIN(col)`|最小值|
|`ARRAY_AGG(col)`|把多行合并成数组（PG特色）|
|`STRING_AGG(col, sep)`|多行拼接字符串（PG常用，替代MySQL group_concat）|

### 1. GROUP BY 分组
```sql
-- 统计每个用户订单总金额、订单数
SELECT user_id, SUM(amount) AS total, COUNT(*) AS cnt
FROM "order"
GROUP BY user_id;
```
> PG 严格模式：SELECT 里非聚合字段，**必须全部出现在 GROUP BY**，不能像MySQL宽松模式。

### 2. HAVING 分组后过滤
`WHERE`：分组**之前**过滤原始行；`HAVING`：GROUP BY **之后**过滤聚合结果
```sql
SELECT user_id, SUM(amount) AS total
FROM "order"
WHERE create_time > '2026-01-01' -- 先过滤订单
GROUP BY user_id
HAVING SUM(amount) > 1000; -- 过滤分组结果
```

### 3. 窗口函数（扩展，面试常连带问到）
不属于聚合，但经常一起考：聚合是多行合并一行；窗口函数保留原行数，附加计算结果
```sql
SELECT id,user_id,amount,
SUM(amount) OVER(PARTITION BY user_id) AS user_total
FROM "order";
```

## 四、多表&子查询优化要点（PG）
1. JOIN 尽量小表驱动大表，关联字段建立 B-Tree 索引；
2. 避免 `SELECT *`，只查需要字段，减少IO；
3. 相关子查询尽量改成 JOIN / EXISTS；大数据慎用 IN；
4. 笛卡尔积严禁出现；
5. GROUP BY 的字段、聚合计算字段，可考虑合适索引；
6. EXPLAIN ANALYZE 查看真实执行计划，看是否 Seq Scan 全表扫描、Hash Join 溢写磁盘；
7. 多表关联不要过多（一般建议不超过3~5张），关联越多优化器代价计算越容易选错执行计划。

## 五、面试题小清单（自测）
1. IN 和 EXISTS 的区别？PG 里什么时候选哪个？
2. LEFT JOIN 后 WHERE 过滤右表字段会发生什么？
3. COUNT(*) / COUNT(1) / COUNT(col) 在PG的区别？
4. 三种JOIN算法适用场景？
5. WHERE 和 HAVING 的区别？
6. CTE 在PG12前后优化行为差异？

要不要我把这块内容整理成一份**可直接在PG执行的完整SQL脚本**（建表+测试数据+各类join、子查询、聚合示例）？