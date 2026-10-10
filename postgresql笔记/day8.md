# PostgreSQL 用户权限表设计 + 外键机制 + 关联查询
采用工业标准 **RBAC（基于角色的访问控制）** 模型设计，兼顾规范性、可扩展性与 PostgreSQL 原生特性；同时详解外键的原理、用法、性能坑点与生产最佳实践。

---

## 一、权限模型选型
### 1. 两种主流方案
| 模型 | 结构 | 适用场景 |
|---|---|---|
| 用户-权限 直连 | 用户表 + 权限表 + 用户权限中间表 | 极简系统、角色极少、权限直接分配给用户 |
| **RBAC 标准模型** | 用户表 + 角色表 + 权限表 + 用户角色中间表 + 角色权限中间表 | 绝大多数业务系统，通过角色批量分配权限，解耦用户与权限 |

> 生产推荐 **RBAC 三级模型**：用户 ⇄ 角色 ⇄ 权限，均为多对多关系；新增权限只需要分配给角色，用户自动继承。

### 2. 核心表关系
- 1个用户可以有多个角色
- 1个角色可以分配给多个用户
- 1个角色可以有多个权限
- 1个权限可以属于多个角色

---

## 二、完整表结构设计（PostgreSQL 原生语法）
所有表遵循：主键用 `IDENTITY`、时间用 `timestamptz`、状态用数字枚举、唯一约束明确、外键按需配置。

### 1. 用户表 `sys_user`
存储系统用户基础信息
```sql
CREATE TABLE sys_user (
    id bigint PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    username varchar(64) NOT NULL,
    password_hash varchar(255) NOT NULL,
    nickname varchar(64),
    email varchar(128),
    phone varchar(32),
    status smallint NOT NULL DEFAULT 1, -- 1:启用 0:禁用
    create_time timestamptz NOT NULL DEFAULT now(),
    update_time timestamptz NOT NULL DEFAULT now(),
    ext_info jsonb, -- 扩展属性，如头像、部门等非核心字段
    -- 唯一约束：用户名全局唯一
    CONSTRAINT uk_sys_user_username UNIQUE (username)
);

-- 索引：按状态筛选用户
CREATE INDEX idx_sys_user_status ON sys_user(status);
```

### 2. 角色表 `sys_role`
角色是权限的集合载体
```sql
CREATE TABLE sys_role (
    id bigint PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    role_code varchar(64) NOT NULL, -- 角色编码，如 admin、editor
    role_name varchar(64) NOT NULL,
    status smallint NOT NULL DEFAULT 1,
    sort int NOT NULL DEFAULT 0,
    remark varchar(255),
    create_time timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT uk_sys_role_code UNIQUE (role_code)
);
```

### 3. 权限表 `sys_permission`
支持菜单权限 + 按钮权限，树形结构
```sql
CREATE TABLE sys_permission (
    id bigint PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    perm_code varchar(128) NOT NULL, -- 权限标识，如 user:add、order:export
    perm_name varchar(64) NOT NULL,
    type smallint NOT NULL, -- 1:菜单 2:按钮
    parent_id bigint DEFAULT 0, -- 父级ID，顶级为0
    sort int NOT NULL DEFAULT 0,
    url varchar(255),
    status smallint NOT NULL DEFAULT 1,
    remark varchar(255),
    CONSTRAINT uk_sys_perm_code UNIQUE (perm_code)
);

-- 索引：树形查询按父ID查
CREATE INDEX idx_sys_perm_parent ON sys_permission(parent_id);
```

### 4. 用户-角色关联表 `sys_user_role`
用户与角色多对多中间表
```sql
CREATE TABLE sys_user_role (
    id bigint PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    user_id bigint NOT NULL,
    role_id bigint NOT NULL,
    create_time timestamptz NOT NULL DEFAULT now(),
    -- 联合唯一：一个用户不能重复分配同一个角色
    CONSTRAINT uk_user_role UNIQUE (user_id, role_id),
    -- 外键：关联用户表，删除用户级联删除关联
    CONSTRAINT fk_user_role_user FOREIGN KEY (user_id) 
        REFERENCES sys_user(id) ON DELETE CASCADE,
    -- 外键：关联角色表，删除角色级联删除关联
    CONSTRAINT fk_user_role_role FOREIGN KEY (role_id) 
        REFERENCES sys_role(id) ON DELETE CASCADE
);

-- 【重要】外键字段必须手动建索引，PostgreSQL 不会自动创建
CREATE INDEX idx_user_role_user_id ON sys_user_role(user_id);
CREATE INDEX idx_user_role_role_id ON sys_user_role(role_id);
```

### 5. 角色-权限关联表 `sys_role_permission`
角色与权限多对多中间表
```sql
CREATE TABLE sys_role_permission (
    id bigint PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    role_id bigint NOT NULL,
    permission_id bigint NOT NULL,
    create_time timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT uk_role_perm UNIQUE (role_id, permission_id),
    CONSTRAINT fk_role_perm_role FOREIGN KEY (role_id) 
        REFERENCES sys_role(id) ON DELETE CASCADE,
    CONSTRAINT fk_role_perm_perm FOREIGN KEY (permission_id) 
        REFERENCES sys_permission(id) ON DELETE CASCADE
);

CREATE INDEX idx_role_perm_role_id ON sys_role_permission(role_id);
CREATE INDEX idx_role_perm_perm_id ON sys_role_permission(permission_id);
```

---

## 三、外键机制详解
外键是数据库层面保证**参照完整性**的约束，确保子表外键列的值在父表主键中一定存在。

### 1. 外键核心语法
```sql
CONSTRAINT 约束名 FOREIGN KEY (子表字段) 
    REFERENCES 父表(父表字段) 
    [ON DELETE 动作]
    [ON UPDATE 动作]
```

### 2. 四种参照动作（ON DELETE / ON UPDATE）
| 动作 | 行为 | 适用场景 |
|---|---|---|
| `RESTRICT` / `NO ACTION`（默认） | 子表有匹配数据时，禁止删除/修改父表记录 | 核心业务表，防止误删 |
| `CASCADE` 级联 | 删除/修改父表记录时，自动删除/修改子表对应记录 | 中间关联表、附属数据 |
| `SET NULL` | 父表记录删除时，子表外键字段设为 NULL | 子表允许外键为空，数据保留 |
| `SET DEFAULT` | 父表记录删除时，子表外键设为默认值 | 有默认值的场景 |

> ⚠️ 生产警示：**谨慎对核心业务表使用 CASCADE**，误删父表一条记录可能级联清空大量子表数据；中间关联表可以放心用。

### 3. 外键的常见坑点
1. **不会自动创建索引**：这是 PostgreSQL 最高发的性能坑。删除父表记录时，数据库需要扫描子表检查关联，外键列无索引会触发全表扫描，大表直接锁表。
2. **写入性能损耗**：每次插入/更新子表，都会校验父表是否存在对应记录，高并发场景有累积开销。
3. **死锁风险**：两个事务按相反顺序操作父子表，可能触发死锁。
4. **分库分表不兼容**：分布式架构、水平分表场景无法使用数据库外键。

---

## 四、常用关联查询示例
### 1. 查询指定用户拥有的所有角色
```sql
SELECT r.id, r.role_code, r.role_name
FROM sys_user u
INNER JOIN sys_user_role ur ON u.id = ur.user_id
INNER JOIN sys_role r ON ur.role_id = r.id
WHERE u.username = 'admin' AND r.status = 1;
```

### 2. 查询用户拥有的所有权限（权限校验核心SQL）
```sql
SELECT DISTINCT p.perm_code, p.perm_name, p.type
FROM sys_user u
INNER JOIN sys_user_role ur ON u.id = ur.user_id
INNER JOIN sys_role_permission rp ON ur.role_id = rp.role_id
INNER JOIN sys_permission p ON rp.permission_id = p.id
WHERE u.id = 1001 
  AND u.status = 1 
  AND p.status = 1;
```
> 优化点：`DISTINCT` 去重多个角色重复的权限；生产环境可构建覆盖索引实现 Index Only Scan。

### 3. 查询某个角色下的所有用户
```sql
SELECT u.id, u.username, u.nickname
FROM sys_role r
INNER JOIN sys_user_role ur ON r.id = ur.role_id
INNER JOIN sys_user u ON ur.user_id = u.id
WHERE r.role_code = 'editor';
```

### 4. 递归查询树形权限（PostgreSQL 递归CTE）
查询某个菜单下的所有子权限（含多级）
```sql
WITH RECURSIVE perm_tree AS (
    -- 根节点
    SELECT id, perm_code, perm_name, parent_id, 1 AS level
    FROM sys_permission WHERE id = 1
    
    UNION ALL
    
    -- 递归关联子节点
    SELECT p.id, p.perm_code, p.perm_name, p.parent_id, pt.level + 1
    FROM sys_permission p
    INNER JOIN perm_tree pt ON p.parent_id = pt.id
)
SELECT * FROM perm_tree ORDER BY level, sort;
```

### 5. 统计每个角色的用户数
```sql
SELECT r.role_name, COUNT(ur.user_id) AS user_count
FROM sys_role r
LEFT JOIN sys_user_role ur ON r.id = ur.role_id
GROUP BY r.id, r.role_name;
```

---

## 五、查询优化与最佳实践
### 1. 索引设计原则
- 所有外键列必须单独建索引，避免删除父表时全表扫描子表
- 多对多中间表的联合唯一索引，同时可满足左前缀查询（如 `(user_id, role_id)` 可加速按用户查角色）
- 高频权限校验查询，可构建联合覆盖索引，减少回表

### 2. 外键的生产权衡
| 方案 | 优点 | 缺点 | 适用场景 |
|---|---|---|---|
| **使用数据库外键** | 强一致性、级联操作方便、应用层代码少 | 写入有校验开销、死锁风险、分库不支持 | 中小系统、数据一致性要求高、并发量一般 |
| **应用层维护关联** | 性能高、灵活、适配分布式架构 | 可能产生脏数据、代码量增加 | 高并发大表、微服务架构、分库分表 |

### 3. 落地建议
1. 中间关联表推荐用外键 + `ON DELETE CASCADE`，保证清理干净，避免孤儿数据
2. 核心业务主表（用户、订单等）建议用 `RESTRICT`，防止误删
3. 超高并发场景（每秒万级写入）可去掉外键，由应用层保证一致性
4. 无论是否用外键，关联字段都必须建索引

---

## 核心总结
1. 标准 RBAC 采用 5 张表结构，通过角色解耦用户与权限，是权限系统的工业标准。
2. PostgreSQL 外键保证参照完整性，支持级联、限制等动作，但**不会自动创建索引**，必须手动添加。
3. 关联查询优先用 INNER JOIN，关联字段建索引；多角色权限去重用 DISTINCT，树形结构用递归 CTE。
4. 外键不是银弹，中小系统放心用，高并发分布式场景可由应用层替代。

需要我补充一份**权限校验的最佳实践SQL+索引优化方案**，或者补充数据权限、部门级权限的扩展设计吗？