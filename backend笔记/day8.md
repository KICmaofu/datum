# JWT用户认证 + 接口权限校验 + 登录注册（三层架构异步版）

> 
> 基于前序三层架构体系，集成 JWT 无状态认证、密码安全哈希、接口鉴权，完全遵循分层规范，全异步非阻塞实现。

---

## 一、核心概念与依赖

### 1. 完整认证流程

1. **注册**：用户提交账号密码 → 密码哈希后存入数据库
2. **登录**：验证账号密码 → 签发 JWT 访问令牌
3. **鉴权**：请求携带 Token → 依赖注入解析校验 → 获取当前用户 → 权限校验
4. **业务**：校验通过后进入对应业务逻辑

### 2. 所需依赖

```
pip install python-jose[cryptography] passlib[bcrypt]
```

- `python-jose`：JWT 生成、解析、签名校验
- `passlib`：密码哈希与验证，使用行业标准 bcrypt 算法

### 3. 配置新增（config/settings.py）

```
class Settings:
    # ... 原有数据库、服务配置
    # JWT 配置
    JWT_SECRET_KEY = "你的强随机密钥"  # 生产环境必须从环境变量读取
    JWT_ALGORITHM = "HS256"
    JWT_ACCESS_EXPIRE_MINUTES = 30  # 访问令牌有效期30分钟
```

> 
> 密钥生成命令：`openssl rand -hex 32`，禁止使用简单字符串作为密钥

---

## 二、安全工具层（common/security.py）

封装密码安全、JWT 能力，全局统一复用，符合异步非阻塞规范。

```
import asyncio
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.config.settings import settings

# 密码哈希上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ---------------------- 密码安全 ----------------------
# bcrypt是CPU密集型，异步场景丢线程池执行，避免阻塞事件循环
async def hash_password(password: str) -> str:
    """密码哈希：单向加密，不可逆"""
    return await asyncio.to_thread(pwd_context.hash, password)

async def verify_password(plain_password: str, hashed_password: str) -> bool:
    """密码校验：明文与哈希比对"""
    return await asyncio.to_thread(pwd_context.verify, plain_password, hashed_password)

# ---------------------- JWT 工具 ----------------------
def create_access_token(user_id: int, role: str = "user") -> str:
    """生成访问令牌
    payload: sub(用户ID), role(角色), exp(过期时间)
    """
    expire = datetime.utcnow() + timedelta(minutes=settings.JWT_ACCESS_EXPIRE_MINUTES)
    payload = {
        "sub": str(user_id),
        "role": role,
        "exp": expire
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

def parse_token(token: str) -> dict | None:
    """解析令牌，签名无效/过期返回None"""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError:
        return None
```

---

## 三、模型与DTO更新

### 1. ORM模型更新（models/user_model.py）

新增密码哈希、角色字段，存储安全凭证与权限标识

```
class User(Base):
    __tablename__ = "sys_user"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, comment="主键ID")
    username: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, comment="用户名")
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False, comment="密码哈希")
    age: Mapped[int] = mapped_column(Integer, comment="年龄")
    email: Mapped[str | None] = mapped_column(String(50), comment="邮箱")
    role: Mapped[str] = mapped_column(String(20), default="user", comment="角色：user普通用户/admin管理员")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, comment="是否激活")
    create_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, comment="创建时间")
```

### 2. DTO新增（schemas/auth_schema.py）

注册、登录请求与令牌响应结构，与业务实体隔离

```
from pydantic import BaseModel, Field

# 注册请求
class RegisterReq(BaseModel):
    username: str = Field(min_length=3, max_length=20)
    password: str = Field(min_length=6, max_length=32)
    age: int = Field(ge=18)
    email: str | None = None

# 登录请求
class LoginReq(BaseModel):
    username: str
    password: str

# 令牌响应
class TokenResp(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    expires_in: int  # 有效期秒数
```

---

## 四、业务层实现（services/auth_service.py）

处理注册、登录核心业务逻辑，事务控制、业务校验全部收敛在 Service 层。

```
from app.common.exception import BusinessException
from app.common.security import hash_password, verify_password, create_access_token
from app.config.settings import settings
from app.daos.user_dao import UserDAO
from app.schemas.auth_schema import RegisterReq, LoginReq, TokenResp
from .base_service import BaseService

class AuthService(BaseService):
    def __init__(self, db):
        super().__init__(db)
        self.user_dao = UserDAO()

    # 用户注册
    async def register(self, req: RegisterReq):
        # 1. 校验用户名唯一性
        exist = await self.user_dao.get_by_username(self.db, req.username)
        if exist:
            raise BusinessException(code=4001, msg="用户名已被注册")

        # 2. 密码哈希转换
        hashed_pwd = await hash_password(req.password)

        # 3. 创建用户（事务控制）
        user_data = req.model_dump(exclude={"password"})
        user_data["password_hash"] = hashed_pwd
        
        async with self.db.begin():
            user = await self.user_dao.create(self.db, user_data)
        
        return user

    # 用户登录
    async def login(self, req: LoginReq) -> TokenResp:
        # 1. 查询用户
        user = await self.user_dao.get_by_username(self.db, req.username)
        if not user:
            raise BusinessException(code=4002, msg="用户名或密码错误")

        # 2. 校验密码
        pwd_ok = await verify_password(req.password, user.password_hash)
        if not pwd_ok:
            raise BusinessException(code=4002, msg="用户名或密码错误")

        # 3. 校验账号状态
        if not user.is_active:
            raise BusinessException(code=4003, msg="账号已被禁用")

        # 4. 生成访问令牌
        token = create_access_token(user.id, user.role)
        
        return TokenResp(
            access_token=token,
            expires_in=settings.JWT_ACCESS_EXPIRE_MINUTES * 60
        )
```

> 
> 安全规范：用户名不存在和密码错误返回统一提示，防止攻击者枚举有效用户名

---

## 五、认证与权限依赖（dependencies/auth.py）

封装成可注入依赖，所有需要认证的接口一行代码复用，符合开闭原则。

```
from fastapi import Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession
from app.common.database import get_db
from app.common.exception import BusinessException
from app.common.security import parse_token
from app.daos.user_dao import UserDAO

# 获取当前登录用户（基础认证校验）
async def get_current_user(
    authorization: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db)
):
    # 1. 校验请求头格式
    if not authorization or not authorization.startswith("Bearer "):
        raise BusinessException(code=401, msg="未提供有效认证令牌")
    
    token = authorization.replace("Bearer ", "")
    
    # 2. 解析令牌有效性
    payload = parse_token(token)
    if not payload:
        raise BusinessException(code=401, msg="令牌无效或已过期")
    
    # 3. 查询用户实体
    user_id = int(payload["sub"])
    user = await UserDAO().get_by_id(db, user_id)
    if not user or not user.is_active:
        raise BusinessException(code=401, msg="用户不存在或已被禁用")
    
    return user

# 角色权限校验工厂（生成指定角色的依赖）
def require_role(*required_roles: str):
    """
    用法：Depends(require_role("admin"))
    支持多个角色：Depends(require_role("admin", "operator"))
    """
    async def role_checker(current_user = Depends(get_current_user)):
        if current_user.role not in required_roles:
            raise BusinessException(code=403, msg="权限不足，无法执行此操作")
        return current_user
    return role_checker
```

---

## 六、控制层接口

### 1. 认证控制器（controllers/auth_controller.py）

注册、登录接口，无需认证即可访问

```
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.common.database import get_db
from app.common.response import ResponseModel
from app.schemas.auth_schema import RegisterReq, LoginReq, TokenResp
from app.schemas.user_schema import UserResp
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["认证授权"])

# 用户注册
@router.post("/register", response_model=ResponseModel)
async def register(
    req: RegisterReq,
    db: AsyncSession = Depends(get_db)
):
    auth_service = AuthService(db)
    user = await auth_service.register(req)
    return ResponseModel.success(UserResp.model_validate(user), msg="注册成功")

# 用户登录
@router.post("/login", response_model=ResponseModel)
async def login(
    req: LoginReq,
    db: AsyncSession = Depends(get_db)
):
    auth_service = AuthService(db)
    token = await auth_service.login(req)
    return ResponseModel.success(token, msg="登录成功")
```

### 2. 接口权限示例（改造用户控制器）

给不同接口按需添加认证/权限依赖

```
from app.dependencies.auth import get_current_user, require_role
from app.models.user_model import User

# 查询个人信息（所有登录用户均可访问）
@router.get("/me", response_model=ResponseModel)
async def get_my_info(current_user: User = Depends(get_current_user)):
    return ResponseModel.success(UserResp.model_validate(current_user))

# 删除用户（仅管理员可操作）
@router.delete("/{user_id}", response_model=ResponseModel)
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role("admin"))
):
    user_service = UserService(db)
    await user_service.delete_user(user_id)
    return ResponseModel.success(msg="删除成功")
```

### 3. 注册路由（main.py）

```
from app.controllers.auth_controller import router as auth_router
app.include_router(auth_router)
```

---

## 七、核心规范与最佳实践

### 1. 安全规范

- **密码安全**：绝对不存储明文密码，使用 bcrypt 哈希算法，禁止自行加密
- **JWT 安全**：
  - payload 不存敏感信息（密码、身份证等），base64 可直接解码，签名仅防篡改
  - 签名密钥足够复杂，生产环境通过环境变量注入，禁止硬编码
  - 访问令牌有效期建议 15-30 分钟，降低泄露后的风险窗口
- **防枚举攻击**：登录失败统一返回“用户名或密码错误”，不区分具体失败原因
- **权限最小化**：接口按需添加认证，普通接口用 `get_current_user`，管理接口叠加角色校验

### 2. 架构规范

- 认证逻辑抽成依赖，避免每个接口重复编写校验代码
- 安全工具统一放在 common 层，全局复用，统一升级
- 业务逻辑保留在 Service 层，Controller 不处理任何认证细节
- 认证失败抛出业务异常，由全局异常处理器统一返回标准格式

### 3. 异步优化

- bcrypt 是 CPU 密集型操作，必须丢到线程池执行，避免阻塞事件循环
- JWT 编解码是轻量操作，同步执行即可，无需异步包装
- 高并发场景可将用户信息缓存至 Redis，减少每次解析都查数据库的开销

---

## 八、常见坑点

1. **Token 格式错误**：必须放在 `Authorization` 请求头，格式为 `Bearer <token>`，注意中间空格
2. **时区问题**：JWT 过期时间必须使用 UTC 时间，避免时区差导致令牌提前/延后过期
3. **字段长度不足**：bcrypt 哈希结果约 60 位，数据库字段建议设为 255 预留冗余
4. **敏感字段泄露**：返回用户信息时禁止返回 `password_hash`，通过 DTO 层自动过滤
5. **异常未捕获**：确保 `BusinessException` 被全局异常处理器捕获，否则认证失败会返回 500 错误

---

需要我继续补充 **刷新令牌机制、Redis 令牌黑名单、多端登录管控** 这些进阶认证功能吗？