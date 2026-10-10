# FastAPI 三层架构重构 + 代码规范
> 承接前面的异步ORM、接口基础，将所有代码按**Controller控制层 / Service业务层 / DAO数据访问层**进行工程化拆分，明确职责边界，解决“所有逻辑堆在路由里”的维护问题。本文包含标准目录结构、每层职责、完整代码示例、企业级代码规范。

---

## 一、三层架构核心设计
### 1. 分层职责
| 层级 | 职责 | 禁止事项 |
|---|---|---|
| **Controller 控制层** | 接收HTTP请求、参数校验、调用Service、封装响应 | 编写业务逻辑、直接操作数据库 |
| **Service 业务层** | 核心业务逻辑、业务规则校验、事务控制、组合DAO | 处理HTTP请求、直接返回响应体 |
| **DAO 数据访问层** | 单表CRUD、SQL查询、纯数据操作 | 包含业务判断、事务控制 |

### 2. 标准工程目录结构
```
fastapi-project/
├── app/
│   ├── __init__.py
│   ├── main.py                  # 应用入口：注册路由、中间件、异常、启动事件
│   ├── config/                  # 配置层
│   │   ├── __init__.py
│   │   └── settings.py          # 环境变量、数据库配置、常量
│   ├── common/                  # 公共基础组件
│   │   ├── __init__.py
│   │   ├── response.py          # 统一响应封装
│   │   ├── exception.py         # 自定义业务异常 + 全局异常处理器
│   │   └── database.py          # 数据库引擎、会话、ORM基类
│   ├── models/                  # ORM实体层（数据库表映射）
│   │   ├── __init__.py
│   │   └── user_model.py
│   ├── schemas/                 # DTO数据传输层（Pydantic请求/响应模型）
│   │   ├── __init__.py
│   │   └── user_schema.py
│   ├── daos/                    # 数据访问层
│   │   ├── __init__.py
│   │   ├── base_dao.py          # 通用CRUD基类
│   │   └── user_dao.py
│   ├── services/                # 业务逻辑层
│   │   ├── __init__.py
│   │   ├── base_service.py
│   │   └── user_service.py
│   └── controllers/             # 控制层（路由）
│       ├── __init__.py
│       └── user_controller.py
└── requirements.txt
```

### 3. 调用链路
```
HTTP请求 → Controller（参数校验） → Service（业务逻辑+事务） → DAO（数据库操作）
                                                                 ↓
HTTP响应 ← Controller（统一封装） ← Service（返回业务对象） ← DAO（返回ORM对象）
```

---

## 二、分层代码实现（全异步版）
### 1. 公共基础层
#### config/settings.py 配置管理
```python
class Settings:
    # 数据库配置
    DATABASE_URL = "sqlite+aiosqlite:///./app.db"
    DATABASE_ECHO = False
    
    # 服务配置
    APP_TITLE = "用户管理系统"
    APP_PORT = 8000

settings = Settings()
```

#### common/database.py 数据库基础设施
```python
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker
)
from sqlalchemy.orm import DeclarativeBase
from app.config.settings import settings

# 异步引擎
async_engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DATABASE_ECHO,
    connect_args={"check_same_thread": False}
)

# 异步会话工厂
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False
)

# ORM基类
class Base(DeclarativeBase):
    pass

# 依赖注入：每个请求一个数据库会话
async def get_db() -> AsyncSession:
    db = AsyncSessionLocal()
    try:
        yield db
    finally:
        await db.close()
```

#### common/response.py 统一响应
```python
from typing import Any
from pydantic import BaseModel

class ResponseModel(BaseModel):
    code: int
    msg: str
    data: Any | None = None

    @classmethod
    def success(cls, data: Any = None, msg: str = "操作成功"):
        return cls(code=200, msg=msg, data=data)

    @classmethod
    def fail(cls, code: int = 400, msg: str = "操作失败"):
        return cls(code=code, msg=msg)
```

#### common/exception.py 异常体系
```python
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from .response import ResponseModel

# 自定义业务异常
class BusinessException(Exception):
    def __init__(self, code: int, msg: str):
        self.code = code
        self.msg = msg

# 全局异常处理器
def register_exception_handler(app):
    @app.exception_handler(BusinessException)
    async def business_exception_handler(request: Request, exc: BusinessException):
        return JSONResponse(
            content=ResponseModel.fail(exc.code, exc.msg).model_dump()
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        return JSONResponse(
            content=ResponseModel.fail(exc.status_code, exc.detail).model_dump()
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        return JSONResponse(
            content=ResponseModel.fail(500, "服务器内部错误").model_dump()
        )
```

### 2. models  ORM实体层
#### models/user_model.py
```python
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Integer, Boolean, DateTime
from datetime import datetime
from app.common.database import Base

class User(Base):
    __tablename__ = "sys_user"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, comment="主键ID")
    username: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, comment="用户名")
    age: Mapped[int] = mapped_column(Integer, comment="年龄")
    email: Mapped[str | None] = mapped_column(String(50), comment="邮箱")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, comment="是否激活")
    create_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, comment="创建时间")
```

### 3. schemas 数据传输层（DTO）
#### schemas/user_schema.py
```python
from pydantic import BaseModel, Field
from datetime import datetime

# 创建请求
class UserCreateReq(BaseModel):
    username: str = Field(min_length=3, max_length=20, description="用户名")
    age: int = Field(ge=18, le=100, description="年龄")
    email: str | None = Field(default=None, description="邮箱")

# 更新请求
class UserUpdateReq(BaseModel):
    age: int | None = None
    email: str | None = None

# 响应对象
class UserResp(BaseModel):
    id: int
    username: str
    age: int
    email: str | None
    is_active: bool
    create_time: datetime

    model_config = {"from_attributes": True}  # 支持ORM对象直接转换
```

### 4. DAO 数据访问层
#### daos/base_dao.py 通用CRUD基类
```python
from typing import TypeVar, Type
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.common.database import Base

ModelType = TypeVar("ModelType", bound=Base)

class BaseDAO:
    def __init__(self, model: Type[ModelType]):
        self.model = model

    # 根据ID查询
    async def get_by_id(self, db: AsyncSession, pk: int):
        result = await db.execute(select(self.model).where(self.model.id == pk))
        return result.scalar_one_or_none()

    # 分页查询列表
    async def get_list(self, db: AsyncSession, skip: int = 0, limit: int = 10):
        result = await db.execute(select(self.model).offset(skip).limit(limit))
        return result.scalars().all()

    # 新增
    async def create(self, db: AsyncSession, obj_in: dict):
        db_obj = self.model(**obj_in)
        db.add(db_obj)
        await db.flush()  # 刷入数据库，获取自增ID，不提交事务
        return db_obj

    # 更新
    async def update(self, db: AsyncSession, pk: int, obj_in: dict):
        stmt = update(self.model).where(self.model.id == pk).values(**obj_in)
        await db.execute(stmt)
        await db.flush()
        return await self.get_by_id(db, pk)

    # 删除
    async def delete(self, db: AsyncSession, pk: int):
        stmt = delete(self.model).where(self.model.id == pk)
        await db.execute(stmt)
        await db.flush()
        return True
```

#### daos/user_dao.py 用户数据访问
```python
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from .base_dao import BaseDAO
from app.models.user_model import User

class UserDAO(BaseDAO):
    def __init__(self):
        super().__init__(User)

    # 自定义查询：根据用户名查询
    async def get_by_username(self, db: AsyncSession, username: str):
        result = await db.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()
```

### 5. Service 业务逻辑层
#### services/base_service.py 业务基类
```python
from sqlalchemy.ext.asyncio import AsyncSession

class BaseService:
    def __init__(self, db: AsyncSession):
        self.db = db  # 接收上层传入的数据库会话
```

#### services/user_service.py 用户业务
```python
from app.common.exception import BusinessException
from app.daos.user_dao import UserDAO
from app.schemas.user_schema import UserCreateReq, UserUpdateReq
from .base_service import BaseService

class UserService(BaseService):
    def __init__(self, db):
        super().__init__(db)
        self.user_dao = UserDAO()

    # 新增用户业务
    async def create_user(self, req: UserCreateReq):
        # 业务校验：用户名重复
        exist = await self.user_dao.get_by_username(self.db, req.username)
        if exist:
            raise BusinessException(code=4001, msg="用户名已存在")

        # 事务控制：整个业务方法一个事务
        async with self.db.begin():
            user = await self.user_dao.create(self.db, req.model_dump())
        return user

    # 查询用户详情
    async def get_user(self, user_id: int):
        user = await self.user_dao.get_by_id(self.db, user_id)
        if not user:
            raise BusinessException(code=4004, msg="用户不存在")
        return user

    # 查询用户列表
    async def list_users(self, page: int, size: int):
        skip = (page - 1) * size
        return await self.user_dao.get_list(self.db, skip, size)

    # 更新用户
    async def update_user(self, user_id: int, req: UserUpdateReq):
        # 校验存在性
        await self.get_user(user_id)
        
        update_data = req.model_dump(exclude_none=True)
        async with self.db.begin():
            user = await self.user_dao.update(self.db, user_id, update_data)
        return user

    # 删除用户
    async def delete_user(self, user_id: int):
        await self.get_user(user_id)
        async with self.db.begin():
            await self.user_dao.delete(self.db, user_id)
        return True
```

> 关键规范：**事务边界在Service层**，一个业务方法对应一个事务；DAO层只做数据操作，不控制事务。

### 6. Controller 控制层
#### controllers/user_controller.py 用户路由
```python
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.common.database import get_db
from app.common.response import ResponseModel
from app.schemas.user_schema import UserCreateReq, UserUpdateReq, UserResp
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["用户管理"])

# 新增用户
@router.post("", response_model=ResponseModel)
async def create_user(
    req: UserCreateReq,
    db: AsyncSession = Depends(get_db)
):
    user_service = UserService(db)
    user = await user_service.create_user(req)
    return ResponseModel.success(UserResp.model_validate(user))

# 查询用户详情
@router.get("/{user_id}", response_model=ResponseModel)
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    user_service = UserService(db)
    user = await user_service.get_user(user_id)
    return ResponseModel.success(UserResp.model_validate(user))

# 查询用户列表
@router.get("", response_model=ResponseModel)
async def list_users(
    page: int = 1,
    size: int = 10,
    db: AsyncSession = Depends(get_db)
):
    user_service = UserService(db)
    users = await user_service.list_users(page, size)
    data = [UserResp.model_validate(u) for u in users]
    return ResponseModel.success(data)

# 更新用户
@router.put("/{user_id}", response_model=ResponseModel)
async def update_user(
    user_id: int,
    req: UserUpdateReq,
    db: AsyncSession = Depends(get_db)
):
    user_service = UserService(db)
    user = await user_service.update_user(user_id, req)
    return ResponseModel.success(UserResp.model_validate(user))

# 删除用户
@router.delete("/{user_id}", response_model=ResponseModel)
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    user_service = UserService(db)
    await user_service.delete_user(user_id)
    return ResponseModel.success(msg="删除成功")
```

### 7. 应用入口 main.py
```python
from fastapi import FastAPI
from app.config.settings import settings
from app.common.database import async_engine, Base
from app.common.exception import register_exception_handler
from app.controllers.user_controller import router as user_router

app = FastAPI(title=settings.APP_TITLE)

# 注册全局异常
register_exception_handler(app)

# 注册路由
app.include_router(user_router)

# 启动事件：创建数据表
@app.on_event("startup")
async def startup():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=settings.APP_PORT, reload=True)
```

---

## 三、企业级代码规范
### 1. 命名规范
| 类型 | 规范 | 示例 |
|---|---|---|
| 文件/包名 | 蛇形命名（小写+下划线） | `user_controller.py`、`user_service.py` |
| 类名 | 大驼峰命名 | `UserService`、`UserDAO` |
| 函数/方法名 | 蛇形命名 | `get_user_by_id`、`create_user` |
| 常量 | 全大写+下划线 | `DATABASE_URL`、`MAX_PAGE_SIZE` |
| 私有方法 | 下划线开头 | `_check_user_status` |

### 2. 分层边界规范
1. **单向依赖**：Controller → Service → DAO，禁止反向调用，禁止跨层直接访问（Controller不能直接调DAO）
2. **数据隔离**：层间传递使用Pydantic DTO，禁止将ORM对象直接返回到Controller层
3. **职责单一**：
   - Controller只处理HTTP协议相关逻辑
   - Service只处理业务逻辑，不出现Request、Response等HTTP对象
   - DAO只做数据读写，不包含业务判断

### 3. 事务规范
- 事务边界放在Service层，一个业务方法对应一个事务
- DAO层使用`flush()`刷入数据，不调用`commit()`
- 多个DAO操作必须放在同一个事务中，保证原子性

### 4. 异常处理规范
- DAO层不捕获异常，数据库异常向上抛出
- Service层抛出`BusinessException`业务异常，携带错误码和信息
- Controller层不捕获异常，统一交给全局异常处理器处理
- 禁止使用`try-except`吞掉异常不做处理

### 5. 其他工程规范
1. **配置分离**：所有常量、环境变量放到config目录，禁止硬编码
2. **依赖注入**：数据库会话通过依赖注入获取，禁止全局共享会话
3. **类型注解**：所有函数参数、返回值必须添加类型提示
4. **注释规范**：类、公共方法必须添加文档字符串，复杂逻辑添加行内注释
5. **导入顺序**：标准库 → 第三方库 → 项目内部模块，空行分隔

---

## 四、重构收益
1. **可维护性**：职责清晰，修改业务逻辑只动Service层，修改数据库只动DAO层
2. **可测试性**：每层可以独立单元测试，Mock依赖即可
3. **可复用性**：通用CRUD封装，业务逻辑可以被多个Controller调用
4. **可扩展性**：新增业务模块只需要新增对应三层文件，结构统一

---

需要我继续补充：**接口权限校验、日志链路追踪、单元测试编写**这三块工程化内容吗？