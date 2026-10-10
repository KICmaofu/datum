# PostgreSQL：常用系统函数 + 窗口函数入门 + 执行计划进阶

> 
> 承接前序 PG 技术体系，全部基于 PostgreSQL 原生语法，标注**PG 特有特性**与生产高频踩坑点，兼顾开发实操与面试考点。

---

## 一、常用系统函数

按生产使用频率分类，覆盖开发、报表、运维三大场景。

### 1. 字符串函数（开发高频）

| 函数 | 作用 | 示例与说明 |
| --- | --- | --- |
| `char_length(s)` | 字符数（中文按1个算） | `char_length('你好pg')` → 4   ⚠️ `length()` 返回字节数，中文场景慎用 |
| `concat(s1,s2...)` | 拼接字符串，自动忽略 NULL | `concat('a', null, 'b')` → `ab` |
| `concat_ws(sep, s1...)` | 带分隔符拼接 | `concat_ws('-', '2026', '09')` → `2026-09` |
| `split_part(s, sep, n)` | 按分隔符取第N段 | `split_part('a-b-c', '-', 2)` → `b`，日志/路径解析极常用 |
| `string_agg(col, sep)` | 多行字符串聚合 | 配合 GROUP BY 使用，替代 MySQL 的 `group_concat` |
| `regexp_replace(s, pat, rep)` | 正则替换 | `regexp_replace('abc123', '\d+', '')` → `abc` |
| `coalesce(col, default)` | 空值替换 | `coalesce(amount, 0)`，空值转默认值，全场景通用 |

### 2. 日期时间函数（报表必备）

PG 时间体系丰富，**区分事务级/语句级/实时时间**是核心考点。

```
-- 1. 时间获取
SELECT now();                  -- 事务开始时间（同事务内多次调用值不变）
SELECT current_timestamp;      -- 等价于 now()
SELECT statement_timestamp();  -- 语句开始时间
SELECT clock_timestamp();      -- 实时时间（同一条SQL内多次调用都不同）

-- 2. 时间截断（统计最常用）
SELECT date_trunc('month', create_time) FROM t;  -- 截断到月初
-- 支持粒度：year / month / day / hour / minute / week

-- 3. 字段提取
SELECT extract(year from create_time) AS year FROM t;

-- 4. 时间间隔运算
SELECT create_time + interval '7 days' FROM t;   -- 加7天
SELECT age(now(), birthday) FROM user;           -- 返回年龄间隔（x岁x月x天）
```

### 3. 数值与类型转换

```
-- 数值
round(3.1415, 2);   -- 四舍五入保留2位 → 3.14
trunc(3.99, 1);     -- 截断小数 → 3.9
ceil(3.1);          -- 向上取整 → 4
floor(3.9);         -- 向下取整 → 3
random();           -- 0~1 随机浮点数

-- 类型转换（PG特有 :: 语法，简洁高效）
SELECT '123'::int;
SELECT cast('2026-09-23' AS date);  -- 标准SQL写法
SELECT 100::text::jsonb;            -- 支持链式转换
```

### 4. 系统运维函数（排查必备）

```
-- 表/索引大小（人类可读格式）
SELECT pg_size_pretty(pg_relation_size('t'));          -- 仅表数据大小
SELECT pg_size_pretty(pg_total_relation_size('t'));    -- 表+所有索引总大小
SELECT pg_size_pretty(pg_database_size('dbname'));     -- 整个数据库大小

-- 连接与会话
SELECT current_user;       -- 当前用户名
SELECT current_schema;     -- 当前 schema
SELECT inet_server_addr(); -- 数据库服务端IP
```

---

## 二、窗口函数入门

窗口函数是 SQL 进阶的核心标志，**解决「跨行计算但保留原行」的问题**，是排名、累计、同环比等业务场景的最优解。

### 1. 核心概念：和聚合函数的区别

- **普通聚合（GROUP BY）**：多行合并为一行，输出行数 = 分组数
- **窗口函数**：每行都保留，额外追加计算结果，输出行数 = 原表行数
- 本质：按规则划分「窗口」，在窗口内逐行计算

### 2. 基础语法结构

```
窗口函数名(参数) OVER (
  [PARTITION BY 分区字段]    -- 分组，类似 GROUP BY
  [ORDER BY 排序字段]        -- 窗口内排序
  [ROWS/RANGE 帧范围]        -- 窗口内计算的行范围
)
```

### 3. 三类必学窗口函数（附场景）

#### （1）排名类：分组内排序取名次

最常用的三种排名，区别在于同分处理：

- `row_number()`：连续不重复排名 1,2,3,4（同分也按顺序排）
- `rank()`：跳跃排名 1,1,3,4（同分同名，下一名跳过）
- `dense_rank()`：密集排名 1,1,2,3（同分同名，下一名连续）

```
-- 示例：按部门分组，按薪资降序排名
SELECT 
  dept, name, salary,
  row_number() OVER (PARTITION BY dept ORDER BY salary DESC) AS rn
FROM employee;
```

#### （2）聚合窗口类：累计计算 / 分区内全量统计

聚合函数都可以加 `OVER()` 变成窗口函数，最典型是**累计求和**。

```
-- 示例：每个用户的订单金额累计求和
SELECT 
  user_id, create_time, amount,
  SUM(amount) OVER (
    PARTITION BY user_id 
    ORDER BY create_time
  ) AS cumulative_amount
FROM orders;
```

> 
> ⚠️ 关键坑点：加 `ORDER BY` 后，默认帧范围是「分区开头到当前行」，结果是累计值；不加 `ORDER BY`，默认帧是「整个分区」，结果是分区内总和。

#### （3）偏移类：取前后行数据，实现同环比

- `lag(col, n, default)`：取当前行**往前第n行**的值
- `lead(col, n, default)`：取当前行**往后第n行**的值

```
-- 示例：月度销售额环比（本月和上月差值）
SELECT 
  month, sales,
  lag(sales, 1, 0) OVER (ORDER BY month) AS last_month_sales,
  sales - lag(sales, 1, 0) OVER (ORDER BY month) AS mom_diff
FROM monthly_sales;
```

### 4. 执行顺序与注意事项

1. 窗口函数在 `WHERE / GROUP BY / HAVING` 之后执行，**不能写在 WHERE 条件里**，需要过滤请套子查询
2. 窗口函数不影响原表行数，适合做明细+统计混合展示
3. 大表窗口函数开销较高，分区字段、排序字段建议配合索引

---

## 三、执行计划进阶

在基础扫描类型之上，深入讲解**读取规则、成本原理、JOIN 算法特征、性能红灯识别**，是 SQL 优化的核心能力。

### 1. 执行计划的正确读取顺序

很多人第一步就读反了，记住规则：

> 
> **缩进越深，执行越早；同一缩进，从上到下；最外层是最终输出。**

示例：

```
Nested Loop
  -> Seq Scan on t1  (先执行：驱动表全表扫)
  -> Index Scan on t2  (后执行：循环查索引)
```

内层缩进的节点先执行，外层后执行。

### 2. Cost 成本估算原理

执行计划里的 `cost=0.43..8.45` 不是毫秒，是**相对代价单位**，优化器永远选择总成本最低的方案。

- 格式：`启动成本..总成本`
- 核心基准参数（默认值）：
  - `seq_page_cost = 1.0`：顺序读取一页的代价
  - `random_page_cost = 4.0`：随机读取一页的代价
- 为什么优化器放弃索引选全表扫？
返回行数占比高时，索引扫描需要大量随机IO + 回表，总成本高于顺序全表扫描，属于**合理选择**，不是 bug。

### 3. 三大 JOIN 算法的计划特征

| 算法 | 计划节点名 | 特征与适用场景 | 性能标志 |
| --- | --- | --- | --- |
| 嵌套循环 | `Nested Loop` | 小表驱动大表，内表关联字段有索引；适合小结果集 | 内层是 Index Scan 为优 |
| 哈希连接 | `Hash Join` | 先构建小表哈希表，再扫描大表探测；大数据量无索引场景 | 看 `Hash Cond`，内存不足会溢写磁盘 |
| 归并连接 | `Merge Join` | 两边输入有序（索引或排序）；适合大数据量排序关联 | 配合 Index Scan 最佳，带 Sort 则有额外开销 |

### 4. 关键性能节点识别（红灯/绿灯）

#### 绿灯节点（性能良好）

- `Index Only Scan`：覆盖索引，无回表
- `GroupAggregate`：利用索引有序分组，无需额外排序
- `Sort Method: QuickSort Memory`：内存内排序

#### 红灯节点（性能瓶颈）

1. **`Seq Scan` 大表**：千万级表全表扫描，IO 爆炸
2. **`Sort Method: External Sort Disk`**：数据量超过 `work_mem`，落盘排序，性能暴跌
3. **Hash Join 出现 `Batches: > 1`**：哈希表溢写磁盘，多批次处理
4. **预估行数与实际行数差 10 倍以上**：统计信息过期，优化器选错计划
5. **`Nested Loop` 内层是 Seq Scan**：循环全表扫，时间复杂度 O(n*m)

### 5. EXPLAIN 高级参数用法

```
-- 最常用排查组合：真实执行 + 缓存统计
EXPLAIN (ANALYZE, BUFFERS)
SELECT ...;
```

- `ANALYZE`：真实执行 SQL，输出**实际行数/耗时**（生产环境慎跑大查询/写操作）
- `BUFFERS`：显示缓存命中块数、磁盘读取块数，定位 IO 瓶颈
- `FORMAT JSON`：输出 JSON 格式，可导入可视化工具分析
- `VERBOSE`：显示完整输出字段、表别名等细节

### 6. 常见执行计划异常与排查

1. **索引不生效**：检查索引列是否被函数包裹、隐式类型转换、条件选择性太差
2. **预估偏差大**：执行 `ANALYZE table_name;` 更新统计信息
3. **排序落盘**：临时调大 `work_mem`，或建立对应排序索引
4. **哈希溢写**：调大 `work_mem`，或拆分大查询
5. **选错 JOIN 类型**：确认统计信息，或临时用 `SET enable_hashjoin = off` 验证（不建议生产强制）

---

## 核心总结

1. 系统函数重点掌握：`date_trunc`、`split_part`、`string_agg`、`coalesce`、`pg_size_pretty`，覆盖 80% 开发场景。
2. 窗口函数入门三类必学：排名、累计聚合、前后偏移；核心是理解分区、排序、帧范围。
3. 执行计划进阶核心：会读顺序、懂成本、识红灯；`EXPLAIN (ANALYZE, BUFFERS)` 是排查性能的第一工具。

需要我补充一份**可直接运行的窗口函数+执行计划练习SQL脚本**（建表+测试数据+典型场景）吗？