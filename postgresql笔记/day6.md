# PostgreSQL pgvector 扩展：安装 + 向量字段创建 + 数据写入
pgvector 是 PostgreSQL 开源向量扩展，专为向量存储、相似度检索设计，是 RAG、知识库、图像检索等 AI 场景的主流落地方案，完全兼容 PostgreSQL 原有事务、索引、权限体系。

---

## 一、pgvector 扩展安装
### 1. 环境要求
- PostgreSQL 12 及以上版本（推荐 14/15/16 稳定版）
- 操作系统：Linux/macOS/Windows 均可，生产推荐 Linux
- 编译依赖：gcc、make、对应版本的 PostgreSQL 开发包

### 2. 三种安装方式
#### 方式一：系统包管理器安装（生产推荐，最简单）
包名规则：`postgresql-你的PG版本号-vector`，必须和已安装的 PostgreSQL 主版本完全一致。

**Ubuntu/Debian**
```bash
# 以 PostgreSQL 16 为例
sudo apt update
sudo apt install -y postgresql-16-vector
```

**RHEL/CentOS（需先配置 PGDG 源）**
```bash
sudo yum install -y postgresql16-vector
```

#### 方式二：源码编译安装（自定义版本、特殊环境）
适合需要指定版本、或者系统没有对应包的场景。
```bash
# 安装依赖（以PG16为例）
sudo apt install -y postgresql-server-dev-16 build-essential git

# 拉取源码
git clone --branch v0.7.4 [https://github.com/pgvector/pgvector.git](https://github.com/pgvector/pgvector.git)
cd pgvector

# 编译安装
make
sudo make install
```

#### 方式三：Docker 一键启动
直接使用官方打包好的镜像，开箱即用。
```bash
# 基于PG16的pgvector镜像
docker run -d \
  --name pgvector \
  -e POSTGRES_PASSWORD=your_password \
  -e POSTGRES_DB=vector_db \
  -p 5432:5432 \
  pgvector/pgvector:pg16
```

### 3. 启用扩展
安装完成后，**需要在目标数据库内执行创建扩展**（不是全局生效，每个库单独创建），需要超级用户权限。
```sql
-- 进入目标数据库后执行
CREATE EXTENSION IF NOT EXISTS vector;

-- 验证安装成功，查看版本
SELECT vector_version();
```

---

## 二、向量字段创建
### 1. vector 数据类型
pgvector 新增 `vector` 数据类型，定义时必须指定**固定维度**，语法：
```sql
vector(维度数)
```
- 维度为正整数，同一个字段所有向量维度必须完全一致
- 内部采用 float32 单精度浮点数存储，兼顾精度和体积
- 单条向量占用空间：`4字节 × 维度 + 少量元数据开销`，例如 1536 维约 6KB

### 2. 建表示例
```sql
CREATE TABLE knowledge_base (
    id bigint PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    content text NOT NULL,                    -- 原始文本内容
    embedding vector(1536) NOT NULL,          -- 1536维向量，适配OpenAI text-embedding-ada-002
    metadata jsonb,                           -- 附属元数据
    create_time timestamptz DEFAULT now()
);
```

### 3. 维度选择注意事项
1. 必须和Embedding模型输出维度严格对应：
   - 768 维：BERT-base、通用中文模型
   - 1536 维：OpenAI text-embedding-ada-002
   - 3072 维：OpenAI text-embedding-3-large
2. 维度越高，存储体积越大、检索性能越低，业务够用前提下优先选择低维度
3. 字段维度定义后无法直接修改，只能新建字段或重建表
4. 不建议超过 2000 维，超高维度建议先做降维处理再入库

---

## 三、向量数据写入
### 1. 单行写入（字符串形式）
最常用的方式，用方括号包裹浮点数，逗号分隔，显式转换为 vector 类型。
```sql
INSERT INTO knowledge_base (content, embedding)
VALUES (
    'pgvector是PostgreSQL的向量检索扩展',
    '[0.012, -0.034, 0.125, 0.078, ..., 0.009]'::vector
);
```
> 注意：数组长度必须和字段定义的维度完全一致，否则会报错 `different vector dimensions`。

### 2. 数组类型转换写入
如果应用层传递的是浮点数组，可以通过 PostgreSQL 数组类型转换：
```sql
INSERT INTO knowledge_base (content, embedding)
VALUES (
    '向量检索支持余弦、欧氏距离等相似度计算',
    ARRAY[0.021, 0.053, -0.017, ...]::float4[]::vector
);
```
`float4[]` 对应 pgvector 内部的单精度类型，转换效率最高，避免精度损失。

### 3. 批量写入（生产推荐）
批量写入性能远高于逐行插入，适合初始化知识库、批量导入向量。
```sql
INSERT INTO knowledge_base (content, embedding)
VALUES
    ('文本片段1', '[0.1, 0.2, 0.3, ...]'::vector),
    ('文本片段2', '[0.3, 0.1, 0.8, ...]'::vector),
    ('文本片段3', '[-0.2, 0.5, 0.0, ...]'::vector);
```

十万级以上超大量数据，推荐使用 `COPY` 命令导入，性能是批量 INSERT 的数倍。

### 4. 常见注意事项
- **维度校验**：写入向量维度必须和字段定义完全一致，多一位少一位都会报错
- **精度特性**：输入 double 双精度浮点数会自动转为 float32 单精度，存在轻微精度损失，属于正常现象
- **事务兼容**：向量写入和普通字段完全一致，支持事务 ACID，回滚会同步撤销
- **空值限制**：不允许写入空向量，维度至少为 1；业务允许空的话字段设为 nullable
- **更新代价**：向量字段更新和普通字段一样，PG MVCC 会生成新行版本，大向量频繁更新开销较高

写入完成后，即可使用 `<->`（欧氏距离）、`<#>`（内积）、`<=>`（余弦距离）等运算符做相似度检索，数据量大时建议创建向量索引优化查询性能。

向量数据库的配置和数据导入实操性较强，工作任务模式可以帮你生成完整的部署脚本、批量导入方案和性能调优建议，要不要用它继续？