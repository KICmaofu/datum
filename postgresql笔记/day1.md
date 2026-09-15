# PostgreSQL 基础：数据类型、表约束、DDL & DML
> 适合后端基础复习，重点区分 DDL（定义结构）、DML（操作数据），掌握常用类型 + 约束，可直接写建表CRUD。

## 一、PostgreSQL 常用基础数据类型
### 1. 数值类型
| 类型 | 说明 |
|---|---|
| `smallint` | 小整数，2字节，范围 ±32768 |
| `integer` / `int` | 整型，4字节（最常用） |
| `bigint` | 大整数，8字节，主键ID常用 |
| `numeric(p,s)` | 高精度小数，p总位数，s小数位，适合金额 |
| `real` | 单精度浮点数 |
| `double precision` | 双精度浮点数 |

> ✅ 金额**不要用float**，使用 `numeric`，避免浮点精度丢失。

### 2. 字符串类型
| 类型 | 说明 |
|---|---|
| `char(n)` | 定长字符串，不足补空格，很少用 |
| `varchar(n)` | 变长字符串，最多n字符 |
| `text` | 无限长文本，PostgreSQL推荐，性能很好 |

> PostgreSQL中 `text` 性能不输varchar，大文本直接用text。

### 3. 时间日期类型
| 类型 | 说明 |
|---|---|
| `date` | 日期：`2026-09-15` |
| `time` | 时间（不带日期） |
| `timestamp` | 时间戳（不带时区） |
| `timestamptz` / `timestamp with time zone` | **带时区时间戳，业务推荐**，自动转时区 |

### 4. 布尔类型
`boolean`，取值：`true` / `false` / `null`

### 5. 其他常用
- `uuid`：全局唯一ID，适合分布式主键
- `json`：json文本存储，查询性能弱
- `jsonb`：二进制JSON，支持索引，业务首选
- `array`：数组类型，如 `int[]` 整数数组

## 二、表约束 Constraints
约束用来保证数据完整性，在建表时定义。

1. **PRIMARY KEY 主键**
    - 唯一 + 非空；一张表只能一个主键，可以多列联合主键
2. **NOT NULL 非空**：字段不能为NULL
3. **UNIQUE 唯一**：字段值不能重复，允许多个null
4. **CHECK 检查约束**：自定义校验规则，如价格>0
5. **DEFAULT 默认值**：插入不填时自动填充
6. **FOREIGN KEY 外键**：引用另一张表主键，维护关联关系

示例建表，一次性演示多种约束：
```sql
CREATE TABLE users (
    id BIGINT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    age INT CHECK (age > 0 AND age < 150),
    status BOOLEAN DEFAULT true,
    create_at TIMESTAMPTZ DEFAULT NOW(),
    remark TEXT
);

-- 外键示例：订单表关联用户表
CREATE TABLE orders (
    id BIGINT PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id), -- 外键
    amount NUMERIC(10,2) NOT NULL CHECK(amount >= 0)
);
```

> 外键注意：外键引用的字段必须是主键/唯一键；可设置 `ON DELETE CASCADE` 级联删除。
```sql
user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE
```

## 三、DDL 数据定义语言（操作库、表结构）
DDL 改**表结构**，不是数据。关键字：`CREATE / ALTER / DROP / TRUNCATE`

### 1. 创建表
```sql
CREATE TABLE IF NOT EXISTS users (
    id BIGSERIAL PRIMARY KEY, -- BIGSERIAL 自增
    name VARCHAR(50) NOT NULL,
    email VARCHAR(100) UNIQUE,
    create_time TIMESTAMPTZ DEFAULT NOW()
);
```
> `BIGSERIAL` 是伪类型，自动创建自增序列；PG10+ 推荐标识列写法：`id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY`

### 2. 修改表 ALTER TABLE
```sql
-- 添加字段
ALTER TABLE users ADD COLUMN phone VARCHAR(20);
-- 删除字段
ALTER TABLE users DROP COLUMN phone;
-- 修改字段类型
ALTER TABLE users ALTER COLUMN name TYPE VARCHAR(80);
-- 添加约束
ALTER TABLE users ADD CONSTRAINT chk_age CHECK(age>0);
-- 删除约束
ALTER TABLE users DROP CONSTRAINT chk_age;
-- 重命名表
ALTER TABLE users RENAME TO member;
```

### 3. 删除表
```sql
DROP TABLE IF EXISTS users;
-- 级联删除（删除表+依赖该表的外键）
DROP TABLE IF EXISTS users CASCADE;
```

### 4. TRUNCATE 清空表
```sql
TRUNCATE TABLE users;
```
> TRUNCATE：清空全表，重置自增序列；不记录单行日志，速度远快于DELETE；属于DDL。

## 四、DML 数据操纵语言（操作表里**行数据**）
关键字：`INSERT / SELECT / UPDATE / DELETE`

### 1. INSERT 插入
```sql
-- 指定字段插入
INSERT INTO users (name, email)
VALUES ('张三','zhangsan@test.com');

-- 一次性插入多行
INSERT INTO users(name)
VALUES ('李四'),('王五');
```

### 2. SELECT 查询
```sql
-- 查询全部列
SELECT * FROM users;
-- 指定列 + 条件
SELECT id,name FROM users WHERE id > 10;
-- 排序、分页
SELECT * FROM users ORDER BY id DESC LIMIT 10 OFFSET 0;
```

### 3. UPDATE 更新
```sql
UPDATE users
SET name = '新名字'
WHERE id = 1;
```
⚠️ **不加WHERE会更新整张表！非常危险**

### 4. DELETE 删除行
```sql
DELETE FROM users WHERE id = 1;
```
> DELETE属于DML，删除行，不会重置自增，可回滚；TRUNCATE是DDL。

## 五、DCL（顺带区分，面试常问）
DCL：权限管理 `GRANT / REVOKE`
```sql
-- 给用户授权表查询权限
GRANT SELECT ON users TO test_user;
```

## 六、核心对比 & 面试考点
1. DDL：改结构，隐式提交事务，执行完自动commit；DML：操作数据，事务可控，可以rollback
2. SERIAL / IDENTITY：Postgres自增方案；SERIAL不是真实类型，是序列的语法糖
3. `UNIQUE` 允许null，`PRIMARY KEY` 不允许null
4. CHECK约束：PG原生支持，mysql8.0前忽略check
5. JSON vs JSONB：json仅存储，jsonb支持索引，生产推荐jsonb
6. TRUNCATE vs DELETE
    - DELETE：DML，逐行删除，可回滚，不重置自增
    - TRUNCATE：DDL，快速清空，重置自增，可加CASCADE

## 七、完整练习脚本，直接复制运行
```sql
-- 创建用户表
CREATE TABLE IF NOT EXISTS users (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    age INT CHECK (age > 0),
    is_active BOOLEAN DEFAULT true,
    create_at TIMESTAMPTZ DEFAULT NOW(),
    info JSONB
);

-- DML插入
INSERT INTO users(username, age, info)
VALUES ('zhangsan',20, '{"city":"beijing"}'::jsonb);

-- 查询
SELECT * FROM users;

-- 更新
UPDATE users SET age=21 WHERE username='zhangsan';

-- 删除
DELETE FROM users WHERE username='zhangsan';
```

要不要继续往下学 PostgreSQL 索引、事务、子查询/联表查询？

> 当前你已经学习了 PyTorch、React、FastAPI、PostgreSQL，这一套刚好是AI应用后端全栈技术栈。
> 接下来可以继续：SQL联表、索引、事务，或者FastAPI + PostgreSQL项目整合。