# FastAPI 异步接口 + 异步数据库操作（SQLAlchemy 2.0 原生异步）
> 承接上一节同步ORM体系，FastAPI 原生基于异步框架 Starlette，搭配 SQLAlchemy 2.0 官方异步 ORM，可实现**全链路非阻塞**，大幅提升高并发场景下的吞吐量。本文从基础概念到完整可运行代码，讲清异步写法、与同步的差异、常见坑点。

---

## 一、FastAPI 异步接口基础
### 1. 同步路由 vs 异步路由
FastAPI 路由函数支持两种写法，框架自动适配执行方式：

| 写法 | 执行方式 | 适用场景 |
|---|---|---|
| `def` 同步函数 | 自动丢到线程池执行 | CPU 密集型计算、调用同步库 |
| `async def` 异步函数 | 直接在事件循环中执行 | IO 密集型（数据库、外部接口调用） |

> 核心结论：**数据库操作是典型的 IO 密集型场景，必须搭配异步数据库驱动 + async 路由，才能真正发挥异步优势**。如果异步路由里调用同步数据库，反而会因阻塞事件循环降低性能。

### 2. 异步接口最简示例
```python
from fastapi import FastAPI
import asyncio

app = FastAPI()

# 异步路由
@app.get("/async/hello")
async def async_hello():
    # 模拟IO等待（比如数据库查询）
    await asyncio.sleep(0.1)
    return {"code": 200, "msg": "异步接口"}

# 同步路由（框架自动线程池调度）
@app.get("/sync/hello")
def sync_hello():
    import time
    time.sleep(0.1)
    return {"code": 200, "msg": "同步接口"}
```

---

## 二、异步数据库核心：SQLAlchemy 2.0 原生异步
SQLAlchemy 2.0 官方内置异步 ORM，无需第三方封装，核心是把同步的 `Engine` / `Session` 替换为异步版本，模型定义完全复用。

### 1. 核心组件对应关系
| 同步组件 | 异步组件 | 作用 |
|---|---|---|
| `create_engine` | `create_async_engine` | 异步数据库引擎，管理连接池 |
| `sessionmaker` | `async_sessionmaker` | 异步会话工厂 |
| `Session` | `AsyncSession` | 异步数据库会话，事务上下文 |
| `Base.metadata.create_all` | `conn.run_sync(Base.metadata.create_all)` | 异步建表（元数据方法为同步，需包装） |

### 2. 数据库异步驱动选择
不同数据库需要对应异步驱动，安装对应依赖：
| 数据库 | 异步驱动 | 安装命令 | URL 前缀 |
|---|---|---|---|
| SQLite | aiosqlite | `pip install aiosqlite` | `sqlite+aiosqlite:///` |
| MySQL | aiomysql / asyncmy | `pip install aiomysql` | `mysql+aiomysql://` |
| PostgreSQL | asyncpg | `pip install asyncpg` | `postgresql+asyncpg://` |

### 3. 异步引擎与会话创建
```python
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker
)

# 异步数据库地址（SQLite 示例）
DATABASE_URL = "sqlite+aiosqlite:///./async_app.db"

# 1. 创建异步引擎
async_engine = create_async_engine(
    DATABASE_URL,
    echo=True,  # 开发打印SQL，生产关闭
    connect_args={"check_same_thread": False}  # SQLite 专属
)

# 2. 创建异步会话工厂
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,  # 关键：提交后对象不过期，无需重复refresh
    autoflush=False,
    autocommit=False
)
```

> ⚠️ `expire_on_commit=False` 是高频坑点：默认 True 时，commit 后 ORM 对象属性会过期，访问就会触发额外查询，异步场景下极易报错，工程化项目统一设为 False。

---

## 三、异步数据库 CRUD 写法
### 1. 模型定义（和同步完全一致）
实体类、字段映射、表结构定义**零改动**，直接复用同步代码：
```python
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Integer, Boolean, DateTime
from datetime import datetime

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "sys_user"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    age: Mapped[int]
    email: Mapped[str | None] = mapped_column(String(50))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    create_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
```

### 2. 异步建表
元数据的 `create_all` 是同步方法，需要通过异步连接的 `run_sync` 包装执行：
```python
async def init_db():
    async with async_engine.begin() as conn:
        # 同步方法放到异步连接中执行
        await conn.run_sync(Base.metadata.create_all)
```

### 3. 异步依赖注入（每个请求一个会话）
和同步依赖逻辑一致，改为异步生成器，关闭会话需要 `await`：
```python
from fastapi import Depends

async def get_db() -> AsyncSession:
    db = AsyncSessionLocal()
    try:
        yield db
    finally:
        await db.close()  # 异步关闭会话
```

### 4. 异步 CRUD 基础操作
核心差异：**所有数据库交互方法都要加 `await`**，SQL 语句构造和同步完全一致。

```python
from sqlalchemy import select, delete, update

# 新增
async def create_user(db: AsyncSession, username: str, age: int, email: str):
    user = User(username=username, age=age, email=email)
    db.add(user)
    await db.commit()       # 异步提交
    await db.refresh(user)  # 异步刷新
    return user

# 根据ID查询
async def get_user_by_id(db: AsyncSession, user_id: int):
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)  # 异步执行
    return result.scalar_one_or_none()

# 查询列表
async def get_user_list(db: AsyncSession, skip: int = 0, limit: int = 10):
    stmt = select(User).offset(skip).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()

# 更新
async def update_user(db: AsyncSession, user_id: int, data: dict):
    stmt = update(User).where(User.id == user_id).values(**data)
    await db.execute(stmt)
    await db.commit()
    return await get_user_by_id(db, user_id)

# 删除
async def delete_user(db: AsyncSession, user_id: int):
    stmt = delete(User).where(User.id == user_id)
    await db.execute(stmt)
    await db.commit()
    return True
```

---

## 四、完整全异步工程示例
整合：异步接口 + 异步ORM + Pydantic校验 + 统一响应 + 全局异常 + 启动建表

```python
from typing import Any
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

# ========== 1. 初始化 ==========
app = FastAPI(title="全异步FastAPI示例")

# ========== 2. Pydantic 模型 ==========
class UserCreateReq(BaseModel):
    username: str = Field(min_length=3, max_length=20)
    age: int = Field(ge=18)
    email: str | None = None

class UserResp(BaseModel):
    id: int
    username: str
    age: int
    email: str | None
    is_active: bool
    create_time: datetime
    model_config = {"from_attributes": True}

class ResponseModel(BaseModel):
    code: int
    msg: str
    data: Any | None = None
    @classmethod
    def success(cls, data=None):
        return cls(code=200, msg="success", data=data)
    @classmethod
    def fail(cls, code=400, msg="fail"):
        return cls(code=code, msg=msg)

# ========== 3. 全局异常（异步兼容） ==========
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        ResponseModel.fail(exc.status_code, exc.detail).model_dump()
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        ResponseModel.fail(500, "服务器内部错误").model_dump()
    )

# ========== 4. 数据库启动初始化 ==========
@app.on_event("startup")
async def startup():
    await init_db()

# ========== 5. 异步接口层 ==========
@app.post("/users", response_model=ResponseModel)
async def add_user(
    req: UserCreateReq,
    db: AsyncSession = Depends(get_db)
):
    # 用户名重复校验
    exist = await get_user_by_name(db, req.username)
    if exist:
        raise HTTPException(status_code=400, detail="用户名已存在")
    
    user = await create_user(db, **req.model_dump())
    return ResponseModel.success(UserResp.model_validate(user))

@app.get("/users/{user_id}", response_model=ResponseModel)
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return ResponseModel.success(UserResp.model_validate(user))

@app.get("/users", response_model=ResponseModel)
async def list_users(
    page: int = 1,
    size: int = 10,
    db: AsyncSession = Depends(get_db)
):
    skip = (page - 1) * size
    users = await get_user_list(db, skip, size)
    data = [UserResp.model_validate(u) for u in users]
    return ResponseModel.success(data)
```

---

## 五、关键注意事项与高频坑点
### 1. 不要阻塞事件循环
异步路由中**禁止执行长时间同步操作**，比如：
- 同步数据库查询（`pymysql`、`requests` 同步请求）
- 大量 CPU 计算
- `time.sleep()`

如果必须调用同步方法，用 `asyncio.to_thread` 丢到线程池：
```python
import asyncio
result = await asyncio.to_thread(sync_long_function, param1, param2)
```

### 2. 会话生命周期
- `AsyncSession` 线程不安全，**绝对不能全局共享**，必须每个请求一个
- 会话用完必须 `await db.close()`，否则连接池会耗尽
- 不要跨请求持有 ORM 对象，不同会话的对象无法直接关联

### 3. 事务处理
异步事务默认隐式开启，执行 SQL 时自动创建；也可以手动控制事务边界：
```python
async with db.begin():
    db.add(user1)
    db.add(user2)
# 退出with块自动commit，异常自动rollback
```

### 4. 并发查询优化
多个独立查询可以用 `asyncio.gather` 并发执行，大幅减少总耗时：
```python
async def get_user_and_orders(db, user_id):
    # 两个查询并发执行，总耗时 = 最慢的那个
    user, orders = await asyncio.gather(
        get_user_by_id(db, user_id),
        get_orders_by_user(db, user_id)
    )
    return user, orders
```

---

## 六、适用场景总结
| 场景 | 推荐方案 |
|---|---|
| 低并发、业务简单、内部系统 | 同步写法，开发简单、调试方便 |
| 高并发、IO密集型、对外接口 | 全异步写法，吞吐量更高 |
| 大量 CPU 计算 | 同步写法 + 多进程部署 |

---

要不要继续深入：**异步多表关联查询、事务隔离级别、连接池调优、异步并发锁**？