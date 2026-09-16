# Pydantic校验 + 统一响应封装 + 全局异常处理（FastAPI 基础）
> 这三块是 FastAPI 后端项目标配：**Pydantic负责入参/数据校验**，**统一响应封装规范返回体**，**全局异常处理捕获错误、统一报错格式**。下面分开讲基础概念 + 最简可运行代码。

## 一、Pydantic 数据校验基础
Pydantic 是 Python 数据验证库，基于类型注解，自动校验数据、抛出校验异常。FastAPI 默认集成 Pydantic v2。

### 核心要点
1. `BaseModel`：定义数据模型（请求体、响应体）
2. 类型提示：自动校验类型 `int`/`str`/`float`/`list`
3. 校验器：
   - 内置约束：`Field` 设置长度、范围、正则、默认值
   - `@field_validator` 自定义字段校验
4. 自动转换：能转就转（字符串数字转int），转换失败抛 `ValidationError`
5. 常用场景：POST 请求 body、查询参数、路径参数校验

### 简单示例
```python
from pydantic import BaseModel, Field, field_validator

class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=20, description="用户名")
    age: int = Field(ge=18, le=100, description="年龄≥18")
    email: str

    # 自定义字段校验
    @field_validator("email")
    def check_email(cls, v):
        if "@" not in v:
            raise ValueError("邮箱格式不正确")
        return v

# 测试
data = UserCreate(username="zhangsan", age=20, email="test@xxx.com")
print(data.model_dump()) # 转字典
```
> 校验失败会抛出 `pydantic.ValidationError`，这个异常后面交给全局异常处理器捕获。

## 二、统一响应格式封装
后端接口返回固定结构，前端解析逻辑统一，不要每个接口手写字典。

### 规范响应结构设计
```json
{
    "code": 200,      // 业务码：200成功，4xx客户端错误，5xx服务端错误
    "msg": "success", // 提示信息
    "data": {}        // 真实返回数据，成功才有，失败可为null
}
```

### 封装工具类
```python
from typing import Any
from pydantic import BaseModel

# 统一响应模型
class ResponseModel(BaseModel):
    code: int
    msg: str
    data: Any | None = None

    @classmethod
    def success(cls, data: Any = None, msg: str = "success"):
        return cls(code=200, msg=msg, data=data)

    @classmethod
    def fail(cls, code: int = 400, msg: str = "fail", data: Any = None):
        return cls(code=code, msg=msg, data=data)
```

### 在接口中使用
```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/user", response_model=ResponseModel)
def get_user():
    return ResponseModel.success(data={"id": 1, "name": "test"})
```

> 注意：`response_model` 会自动过滤返回字段，也可以不写，直接返回实例，FastAPI会自动转json。

## 三、全局异常处理基础
FastAPI 通过 `@app.exception_handler(异常类)` 注册全局异常捕获函数。
目标：**不管是业务异常、Pydantic校验异常、系统异常，全部包装成上面统一响应格式返回**。

### 常见需要捕获的异常
1. `RequestValidationError`：请求参数校验失败（Pydantic校验触发，FastAPI包装后的异常）
2. `ValidationError`：Pydantic 直接调用模型校验抛出的异常
3. 自定义业务异常（推荐自己定义，用来抛出业务错误，如：用户不存在）
4. `Exception`：兜底捕获所有未知服务异常

### 完整示例
```python
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError

app = FastAPI()

# 1. 自定义业务异常
class BusinessException(Exception):
    def __init__(self, code: int, msg: str):
        self.code = code
        self.msg = msg

# 2. 全局捕获：请求参数校验异常（Pydantic入参错误）
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # exc.errors() 里面是详细校验错误信息
    err_msg = exc.errors()[0]["msg"]
    return JSONResponse(
        content=ResponseModel.fail(code=400, msg=f"参数校验失败: {err_msg}").model_dump(),
        status_code=200 # HTTP状态码可以统一200，靠业务code区分，也可以用400
    )

# 3. 全局捕获自定义业务异常
@app.exception_handler(BusinessException)
async def business_exception_handler(request: Request, exc: BusinessException):
    return JSONResponse(
        content=ResponseModel.fail(code=exc.code, msg=exc.msg).model_dump(),
        status_code=200
    )

# 4. 兜底捕获所有未知异常
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        content=ResponseModel.fail(code=500, msg="服务器内部错误").model_dump(),
        status_code=200
    )

# 测试接口，抛业务异常
@app.get("/test")
def test():
    raise BusinessException(code=4001, msg="用户不存在")
```

## 四、三者联动完整流程
1. 前端发请求 → FastAPI接收
2. Pydantic模型校验请求参数（路径参数/query/body）
   - ✅校验通过：进入接口业务代码
   - ❌校验失败：抛出`RequestValidationError` → **全局异常处理器捕获** → 返回统一json
3. 业务代码正常执行：return `ResponseModel.success()`
4. 业务代码出错：主动 `raise BusinessException` → 全局异常捕获，返回统一错误结构
5. 未知代码bug：兜底`Exception`捕获，返回500

## 五、常见踩坑点
1. `RequestValidationError` vs `ValidationError`
    - 接口入参校验触发：`RequestValidationError`（FastAPI封装）
    - 代码里手动 `Model(**data)` 校验：抛出原始 `ValidationError`
2. HTTP状态码 和 业务code分离
    > 方案A：HTTP 200，全部用业务code区分（前端最方便）
    > 方案B：HTTP 400/500 + 业务code（REST风格）
3. 全局异常返回必须用 `JSONResponse`，否则不会按json返回
4. Pydantic v2 使用 `model_dump()`，v1是 `dict()`

## 六、完整整合可运行代码
```python
from typing import Any
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, Field

# ========== 1. 统一响应 ==========
class ResponseModel(BaseModel):
    code: int
    msg: str
    data: Any | None = None

    @classmethod
    def success(cls, data: Any = None, msg: str = "success"):
        return cls(code=200, msg=msg, data=data)

    @classmethod
    def fail(cls, code: int = 400, msg: str = "fail"):
        return cls(code=code, msg=msg, data=None)

# ========== 2. 自定义业务异常 ==========
class BusinessException(Exception):
    def __init__(self, code: int, msg: str):
        self.code = code
        self.msg = msg

# ========== 3. Pydantic校验模型 ==========
class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=20)
    age: int = Field(ge=18)

# ========== 4. 全局异常处理器 ==========
app = FastAPI()

@app.exception_handler(RequestValidationError)
async def param_error_handler(request: Request, exc: RequestValidationError):
    msg = exc.errors()[0]["msg"]
    return JSONResponse(ResponseModel.fail(400, f"参数错误：{msg}").model_dump())

@app.exception_handler(BusinessException)
async def biz_error_handler(request: Request, exc: BusinessException):
    return JSONResponse(ResponseModel.fail(exc.code, exc.msg).model_dump())

@app.exception_handler(Exception)
async def server_error_handler(request: Request, exc: Exception):
    return JSONResponse(ResponseModel.fail(500, "服务异常").model_dump())

# ========== 接口 ==========
@app.post("/user")
def create_user(user: UserCreate):
    # 模拟业务判断
    if user.username == "admin":
        raise BusinessException(code=4002, msg="用户名已存在")
    return ResponseModel.success(data=user.model_dump())
```

如果你需要，我可以继续：
1. 升级成工程化目录结构（单独放exception、response、schema）
2. 增加日志打印，异常时记录堆栈
3. Pydantic v2高级校验（嵌套模型、list校验、模式枚举）