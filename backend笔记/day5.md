# SQLAlchemy ORM 接入 + 实体映射 + 单表CRUD封装
> 承接 FastAPI 技术栈体系，基于 **SQLAlchemy 2.0 最新语法**（类型安全的声明式ORM），结合依赖注入、Pydantic校验、统一响应做完整工程化示例。

## 一、SQLAlchemy ORM 基础概述
SQLAlchemy 是 Python 最主流的 ORM 框架，通过对象操作数据库，无需手写原生SQL。
### 核心组件
| 组件 | 作用 |
|---|---|
| **Engine（引擎）** | 数据库连接池 + SQL 方言，程序启动时创建一次 |
| **Session（会话）** | 数据库操作的上下文，管理事务、ORM对象，**每个请求一个** |
| **Declarative Base** | ORM模型基类，所有数据表实体类继承它 |
| **Model（实体类）** | Python类 ↔ 数据库表 的映射关系 |

### 版本说明
本文使用 **SQLAlchemy 2.0+** 语法，采用 `Mapped + mapped_column` 类型安全写法，废弃旧版 `session.query()`，统一使用 `select()` 语句。

安装依赖：
```bash
pip install sqlalchemy fastapi uvicorn pydantic
```

---

## 二、实体类与表映射
### 1. 创建基类
所有数据表模型都继承这个基类，用于统一管理映射关系。
```python
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Integer, DateTime, Boolean
from datetime import datetime

# ORM 基类
class Base(DeclarativeBase):
    pass
```

### 2. 定义实体类（表映射）
一个类对应一张表，类属性对应表字段，`Mapped[类型]` 标注字段类型，`mapped_column` 定义约束。
```python
class User(Base):
    # 数据库表名
    __tablename__ = "sys_user"

    # 主键，自增
    id: Mapped[int] = mapped_column(
        primary_key=True, 
        autoincrement=True, 
        comment="用户ID"
    )
    username: Mapped[str] = mapped_column(
        String(20), 
        unique=True, 
        nullable=False, 
        comment="用户名"
    )
    age: Mapped[int] = mapped_column(Integer, comment="年龄")
    email: Mapped[str | None] = mapped_column(String(50), comment="邮箱")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, comment="是否激活")
    create_time: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.now, 
        comment="创建时间"
    )
```

### 常用字段类型
- 数值：`Integer`、`BigInteger`、`Float`
- 字符串：`String(长度)`、`Text`
- 时间：`DateTime`、`Date`
- 布尔：`Boolean`
- 可空：`Mapped[类型 | None]`

---

## 三、数据库连接与会话管理
### 1. 创建引擎（Engine）
程序启动时初始化一次，负责连接池和SQL生成。
```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# SQLite 数据库（无需额外驱动，直接使用）
DATABASE_URL = "sqlite:///./app.db"

# MySQL 写法（需安装 pymysql）
# DATABASE_URL = "mysql+pymysql://root:password@127.0.0.1:3306/test_db"

engine = create_engine(
    DATABASE_URL,
    echo=True,  # 控制台打印SQL语句，开发调试用，生产环境关闭
    connect_args={"check_same_thread": False}  # SQLite 专属配置，MySQL不需要
)
```

### 2. 会话工厂（SessionLocal）
用于创建数据库会话，配置事务行为。
```python
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,  # 不自动刷新
    autocommit=False  # 关闭自动提交，手动控制事务
)
```

### 3. FastAPI 依赖注入：每个请求一个Session
最佳实践：**每个请求创建一个Session，请求结束自动关闭**，通过依赖注入复用。
```python
from fastapi import Depends

def get_db():
    db = SessionLocal()
    try:
        yield db  # 把会话交给路由函数使用
    finally:
        db.close()  # 请求结束后关闭会话

# 路由中使用：db: Session = Depends(get_db)
```

---

## 四、单表 CRUD 基础操作
以 `User` 表为例，演示标准增删改查写法。

### 1. 新增（Create）
```python
def create_user(db, username: str, age: int, email: str):
    # 1. 创建ORM对象
    user = User(username=username, age=age, email=email)
    # 2. 添加到会话
    db.add(user)
    # 3. 提交事务
    db.commit()
    # 4. 刷新对象（获取数据库生成的id、create_time）
    db.refresh(user)
    return user
```

### 2. 查询（Retrieve）
```python
from sqlalchemy import select

# 根据ID查询单条
def get_user_by_id(db, user_id: int):
    stmt = select(User).where(User.id == user_id)
    # scalar_one_or_none：有则返回对象，无则返回None
    return db.execute(stmt).scalar_one_or_none()

# 查询列表（分页）
def get_user_list(db, skip: int = 0, limit: int = 10):
    stmt = select(User).offset(skip).limit(limit)
    # scalars().all()：返回对象列表
    return db.execute(stmt).scalars().all()

# 条件查询
def get_user_by_name(db, username: str):
    stmt = select(User).where(User.username == username)
    return db.execute(stmt).scalar_one_or_none()
```

### 3. 更新（Update）
```python
def update_user(db, user_id: int, age: int = None, email: str = None):
    user = get_user_by_id(db, user_id)
    if not user:
        return None
    
    # 逐个修改属性
    if age is not None:
        user.age = age
    if email is not None:
        user.email = email
    
    db.commit()
    db.refresh(user)
    return user
```

### 4. 删除（Delete）
```python
def delete_user(db, user_id: int):
    user = get_user_by_id(db, user_id)
    if not user:
        return False
    db.delete(user)
    db.commit()
    return True
```

---

## 五、通用 CRUD 封装（工程化写法）
把通用增删改查封装成基类，所有表都可以复用，避免重复代码。
```python
from typing import Any, TypeVar, Type
from sqlalchemy import select, update, delete
from sqlalchemy.orm import Session

ModelType = TypeVar("ModelType", bound=Base)

class BaseCRUD:
    def __init__(self, model: Type[ModelType]):
        self.model = model

    # 根据ID查询
    def get(self, db: Session, pk: int):
        return db.execute(select(self.model).where(self.model.id == pk)).scalar_one_or_none()

    # 查询全部
    def list(self, db: Session, skip: int = 0, limit: int = 10):
        return db.execute(select(self.model).offset(skip).limit(limit)).scalars().all()

    # 新增
    def create(self, db: Session, obj_in: dict):
        db_obj = self.model(**obj_in)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    # 更新
    def update(self, db: Session, pk: int, obj_in: dict):
        stmt = update(self.model).where(self.model.id == pk).values(**obj_in)
        db.execute(stmt)
        db.commit()
        return self.get(db, pk)

    # 删除
    def delete(self, db: Session, pk: int):
        stmt = delete(self.model).where(self.model.id == pk)
        db.execute(stmt)
        db.commit()
        return True

# 使用：实例化User表的CRUD
user_crud = BaseCRUD(User)
```

---

## 六、完整整合 FastAPI 示例
结合 Pydantic 校验、统一响应、依赖注入，形成完整接口层。

```python
from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

# ========== 1. 初始化 ==========
app = FastAPI(title="SQLAlchemy CRUD示例")

# ========== 2. Pydantic 请求/响应模型 ==========
class UserCreateReq(BaseModel):
    username: str = Field(min_length=3, max_length=20)
    age: int = Field(ge=18)
    email: str | None = None

class UserUpdateReq(BaseModel):
    age: int | None = None
    email: str | None = None

class UserResp(BaseModel):
    id: int
    username: str
    age: int
    email: str | None
    is_active: bool
    create_time: datetime

    # 支持ORM对象直接转Pydantic
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

# ========== 3. 数据库初始化（创建所有表） ==========
def init_db():
    Base.metadata.create_all(bind=engine)

# 启动时执行
@app.on_event("startup")
def startup_event():
    init_db()

# ========== 4. 接口层 ==========
# 新增用户
@app.post("/users", response_model=ResponseModel)
def add_user(
    req: UserCreateReq,
    db: Session = Depends(get_db)
):
    # 用户名重复校验
    if user_crud.get_by_username(db, req.username):
        raise HTTPException(status_code=400, detail="用户名已存在")
    
    user = user_crud.create(db, req.model_dump())
    return ResponseModel.success(UserResp.model_validate(user))

# 查询用户详情
@app.get("/users/{user_id}", response_model=ResponseModel)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = user_crud.get(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return ResponseModel.success(UserResp.model_validate(user))

# 查询用户列表
@app.get("/users", response_model=ResponseModel)
def list_users(
    page: int = 1,
    size: int = 10,
    db: Session = Depends(get_db)
):
    skip = (page - 1) * size
    users = user_crud.list(db, skip, size)
    data = [UserResp.model_validate(u) for u in users]
    return ResponseModel.success(data)

# 更新用户
@app.put("/users/{user_id}", response_model=ResponseModel)
def update_user(
    user_id: int,
    req: UserUpdateReq,
    db: Session = Depends(get_db)
):
    if not user_crud.get(db, user_id):
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 排除None值，只更新传入的字段
    update_data = req.model_dump(exclude_none=True)
    user = user_crud.update(db, user_id, update_data)
    return ResponseModel.success(UserResp.model_validate(user))

# 删除用户
@app.delete("/users/{user_id}", response_model=ResponseModel)
def del_user(user_id: int, db: Session = Depends(get_db)):
    if not user_crud.get(db, user_id):
        raise HTTPException(status_code=404, detail="用户不存在")
    user_crud.delete(db, user_id)
    return ResponseModel.success()
```

---

## 七、常见坑点与最佳实践
1. **Session 线程不安全**：绝对不要全局共享一个 Session，必须每个请求创建一个。
2. **事务提交**：`add`/`delete` 只是修改会话缓存，必须 `commit()` 才会写入数据库。
3. **flush vs commit**：`flush()` 把SQL发到数据库但不提交事务；`commit()` 提交并持久化。
4. **ORM 对象转字典**：不要用 `user.__dict__`，会包含内部字段，用 Pydantic 的 `model_validate` 转换。
5. **SQLite 自增主键**：Integer 主键 + autoincrement=True 即可，无需额外配置。
6. **生产环境**：`echo=True` 必须关闭，避免泄露SQL日志；连接池大小按需配置。

---

要不要继续深入：**多表关联查询（一对多/多对多）、事务管理、悲观锁/乐观锁**？