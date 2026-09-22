# PostgreSQL：JSONB操作与索引 + 全文检索基础 + 序列与视图
> 均为 PostgreSQL 核心特色功能，重点讲**生产常用语法、索引优化、踩坑点**，承接前面的执行计划与索引体系

---

## 一、JSONB 类型操作与索引
### 1. JSON 与 JSONB 的核心区别
PG 支持两种 JSON 类型，**99% 业务场景推荐 JSONB**

| 特性 | JSON | JSONB |
|---|---|---|
| 存储形式 | 原始文本字符串 | 解析后的二进制结构 |
| 写入速度 | 快（直接存文本） | 稍慢（需要解析、去重、排序键） |
| 查询速度 | 慢（每次都解析） | 快（预解析结构） |
| 索引支持 | 几乎无法有效索引 | 支持 GIN 索引，查询性能强 |
| 细节保留 | 保留空格、键顺序、重复键 | 不保留空格、键重排、去重重复键 |

### 2. JSONB 常用操作符
#### 取值操作
- `->`：按 key/索引取值，返回 `jsonb` 类型
- `->>`：按 key/索引取值，返回 `text` 字符串
```sql
-- data = '{"name":"tom","age":20,"tags":["db","pg"]}'
SELECT data->'name' FROM t;  -- "tom" (jsonb)
SELECT data->>'name' FROM t; -- tom (文本)
SELECT data->'tags'->0 FROM t; -- "db"
```

- `#>` / `#>>`：按路径数组取值，适合深层嵌套
```sql
SELECT data #> '{address,city}' FROM t;
```

#### 修改与删除
- `||`：合并两个 JSONB，覆盖重复键
- `-`：删除指定键/索引
- `#-`：按路径删除
```sql
SELECT data || '{"gender":"male"}' FROM t; -- 新增字段
SELECT data - 'age' FROM t; -- 删除age键
SELECT data #- '{tags,0}' FROM t; -- 删除数组第一个元素
```

#### 包含与存在判断（**可走 GIN 索引**）
- `@>`：左侧包含右侧
- `<@`：左侧被右侧包含
- `?`：是否存在指定键
- `?|`：是否存在任意一个指定键
- `?&`：是否存在所有指定键
```sql
SELECT * FROM t WHERE data @> '{"name":"tom"}'; -- 包含name=tom
SELECT * FROM t WHERE data ? 'tags'; -- 存在tags键
```

### 3. JSONB 索引优化
#### （1）GIN 通用倒排索引
JSONB 的主力索引，分两种算子类：
1. **默认 `jsonb_ops`**：支持上述所有 `@> / ? / ?| / ?&` 操作符，索引体积较大
2. **`jsonb_path_ops`**：仅支持 `@>` 包含操作，体积小 30%~50%，查询速度更快
> 业务如果只做包含匹配，优先选 `jsonb_path_ops`

```sql
-- 默认GIN索引
CREATE INDEX idx_t_data ON t USING GIN (data);
-- 仅包含查询优化
CREATE INDEX idx_t_data_path ON t USING GIN (data jsonb_path_ops);
```

#### （2）B树 表达式索引
如果固定查询某个顶层键的值，直接建 B 树表达式索引，比 GIN 更高效
```sql
-- 频繁查询 data->>'name' 等值
CREATE INDEX idx_t_data_name ON t ((data->>'name'));
-- 注意：表达式必须加双括号
```

#### （3）优化与坑点
- 大 JSONB 更新代价高：PG MVCC 是整行版本化，JSON 内一个字段更新也会生成整行新元组
- 避免深度嵌套频繁查询，尽量扁平化设计
- `like '%xxx%'` 无法命中 JSONB 的 GIN 索引，需要模糊匹配可结合 `pg_trgm`
- 不要用 JSONB 替代关系表，一对多、频繁关联的字段还是拆表更优

---

## 二、全文检索基础
PostgreSQL 原生支持**基于分词的全文检索**，依赖 `tsvector` / `tsquery` 体系，不需要额外搜索引擎即可实现轻量全文搜索。

### 1. 核心概念
- **tsvector**：文档向量，将文本按分词器拆分后的词条集合，附带位置权重
- **tsquery**：查询条件，支持 `&`（与）、`|`（或）、`!`（非）逻辑组合
- **分词字典**：决定分词规则，默认 `english`，中文需安装插件（zhparser / pg_jieba）
- **相关性排序**：`ts_rank` / `ts_rank_cd` 计算匹配度打分

### 2. 基础语法
```sql
-- 文本转向量
SELECT to_tsvector('english', 'PostgreSQL JSONB index optimization');

-- 构造查询条件
SELECT to_tsquery('english', 'postgresql & index');

-- 匹配查询
SELECT title, content
FROM article
WHERE to_tsvector('english', content) @@ to_tsquery('english', 'jsonb & gin');
```

### 3. 全文索引优化
#### 方式一：表达式索引（简单场景）
直接对 `to_tsvector` 结果建 GIN 索引
```sql
CREATE INDEX idx_article_content_fts 
ON article USING GIN (to_tsvector('english', content));
```

#### 方式二：生成列 + 索引（大数据量推荐）
PG12+ 支持生成列，预计算并存储向量，查询时直接读取，性能更高
```sql
-- 新增存储生成列
ALTER TABLE article 
ADD COLUMN content_tsv tsvector 
GENERATED ALWAYS AS (to_tsvector('english', content)) STORED;

-- 建GIN索引
CREATE INDEX idx_article_content_tsv ON article USING GIN (content_tsv);
```

#### 相关性排序
```sql
SELECT title, ts_rank(content_tsv, query) AS rank
FROM article, to_tsquery('english', 'postgresql') query
WHERE content_tsv @@ query
ORDER BY rank DESC;
```

### 4. 中文与模糊检索补充
- **原生不支持中文分词**：默认英文分词器对中文只会按标点、空格拆分，必须安装 `zhparser` 或 `pg_jieba` 分词插件
- **短文本模糊匹配**：如果不需要语义分词，只需要 `like '%关键词%'`，推荐用 `pg_trgm` 插件 + GIN/GIST 索引，实现普通模糊查询加速
- **适用场景**：轻量站内搜索、日志检索；亿级海量复杂搜索仍建议上 Elasticsearch

---

## 三、序列与视图
### 1. 序列（Sequence）
序列是独立的数据库对象，用于生成全局唯一的递增/递减整数，是 PG 自增主键的底层实现。

#### 创建与使用
```sql
-- 创建序列
CREATE SEQUENCE seq_user_id 
START WITH 1 
INCREMENT BY 1 
NO CYCLE
CACHE 20;

-- 获取下一个值（消耗序号，事务回滚也不退还）
SELECT nextval('seq_user_id');
-- 当前会话最后一次取值
SELECT currval('seq_user_id');
```

#### 两种自增主键写法
1. **`serial`（旧兼容写法）**
```sql
CREATE TABLE "user" (id serial PRIMARY KEY);
```
自动创建关联序列，本质是 int + 默认值 `nextval`。

2. **`IDENTITY`（PG10+，SQL 标准，推荐）**
```sql
CREATE TABLE "user" (
    id int PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    name text
);
```
- `ALWAYS`：始终由数据库生成，禁止手动插入 ID，避免序列不同步
- `BY DEFAULT`：允许手动插入，但需要手动同步序列

#### 关键特性与坑点
- **序列不回滚**：事务回滚，`nextval` 消耗的序号不会回收，保证唯一、不保证连续
- **高并发调大 CACHE**：默认 cache=1，每次取号都读磁盘；高并发场景调大 cache 可大幅提升性能
- 序列和表是独立对象，删表不会自动删除独立序列（serial 关联的会自动删）

### 2. 视图（View）
视图是**虚拟表**，基于 SQL 查询定义，本身不存储数据，每次查询都执行底层 SQL。

#### 创建与作用
```sql
CREATE VIEW v_user_order AS
SELECT u.id, u.name, sum(o.amount) AS total_amount
FROM "user" u
LEFT JOIN "order" o ON u.id = o.user_id
GROUP BY u.id, u.name;
```

核心作用：
1. **权限隔离**：隐藏敏感字段，只给业务方开放视图权限
2. **逻辑复用**：封装复杂关联、聚合逻辑，避免重复写长 SQL
3. **兼容升级**：表结构变更时，通过视图保持对外接口不变

#### 物化视图（Materialized View）
和普通视图最大区别：**物理存储查询结果快照**，相当于预计算表，需要手动刷新。
```sql
-- 创建
CREATE MATERIALIZED VIEW mv_user_order AS
SELECT u.id, u.name, sum(o.amount) AS total_amount
FROM "user" u
LEFT JOIN "order" o ON u.id = o.user_id
GROUP BY u.id, u.name;

-- 全量刷新（会阻塞读）
REFRESH MATERIALIZED VIEW mv_user_order;

-- 并发刷新（PG9.4+，不阻塞读，需要唯一索引）
REFRESH MATERIALIZED VIEW CONCURRENTLY mv_user_order;
```

适用场景：报表统计、离线分析，数据允许分钟级/小时级延迟，避免重复执行大计算量 SQL。

#### 视图常见坑点
- 普通视图每次查询都执行底层 SQL，嵌套多层视图会导致优化器严重失准，性能不可控
- 普通视图默认不可直接 `INSERT/UPDATE/DELETE`，需要写 `INSTEAD OF` 触发器
- 物化视图存在数据延迟，需要制定刷新策略；并发刷新需要唯一索引

---

## 面试核心总结
1. JSONB 是二进制解析存储，支持 GIN 索引；`jsonb_path_ops` 只支持包含查询但性能更好；固定键查询优先用 B 树表达式索引。
2. PG 全文检索基于 tsvector + tsquery，GIN 索引加速；中文需要分词插件，轻量场景够用，海量搜索上 ES。
3. 序列不保证连续、事务不回滚；自增主键推荐用 IDENTITY 替代 serial。
4. 普通视图是虚拟表不存数据；物化视图存快照，适合非实时统计，需要手动刷新。

需要我补充一份可直接运行的**JSONB+全文检索+序列视图 实战SQL脚本**（建表+测试数据+索引+查询示例）吗？