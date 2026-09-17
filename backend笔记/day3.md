# FastAPI：依赖注入 + 中间件基础 + CORS跨域配置
> 承接上一节：Pydantic校验、统一响应、全局异常，这三块是FastAPI后端工程必备基础，下面讲概念+完整可运行代码。

## 一、依赖注入（Depends）
### 概念
依赖注入：把**可复用逻辑**抽成函数/类，路由函数通过`Depends()`声明依赖，FastAPI自动执行、传参。
适用场景：
- 获取当前登录用户
- 获取数据库会话
- 请求参数公共校验
- 权限校验

### 基础示例
```python
from fastapi import FastAPI, Depends, Header

app = FastAPI()

# 1. 普通函数依赖
def get_token(authorization: str | None = Header(default=None)):
    if not authorization:
        return None
    return authorization.replace("Bearer ", "")

# 路由注入依赖
@app.get("/api/user/info")
def user_info(token: str | None = Depends(get_token)):
    return {"token": token, "msg": "获取用户信息"}


# 2. 类依赖（适合需要实例的场景）
class CommonQuery:
    def __init__(self, page: int = 1, size: int = 10):
        self.page = page
        self.size = size

@app.get("/api/list")
def get_list(common: CommonQuery = Depends()):
    return {"page": common.page, "size": common.size}
```

> 特性：依赖可以嵌套（依赖里面再Depends别的依赖）；可缓存（同一个请求内多次调用同一个依赖只执行一次）

---

## 二、中间件基础（Middleware）
### 概念
中间件：**请求到达路由之前、响应返回客户端之前**的拦截层，对request/response做统一处理。
执行顺序：
`客户端请求 → 中间件(接收请求) → 路由处理 → 中间件(拿到响应) → 返回客户端`

常用场景：
- 请求耗时统计
- 统一添加响应头
- 请求日志打印
- 全局请求修改

```python
import time
from fastapi import FastAPI, Request

app = FastAPI()

# 自定义中间件
@app.middleware("http")
async def log_request_time(request: Request, call_next):
    start_time = time.time()
    # 执行后续逻辑（路由/其他中间件）
    response = await call_next(request)
    # 路由处理完之后执行
    duration = time.time() - start_time
    print(f"path: {request.url.path}, cost: {duration:.4f}s")
    # 添加自定义响应头
    response.headers["X-Process-Time"] = str(duration)
    return response

@app.get("/api/hello")
async def hello():
    return {"msg": "hello middleware"}
```

> 注意：中间件是全局的，所有路由都会经过；尽量不要在中间件里抛业务异常，推荐交给全局异常处理器。

---

## 三、CORS跨域配置
### 概念
浏览器同源策略：前端域名/端口和后端不一致时，浏览器拦截ajax请求。
CORS（跨域资源共享）：后端返回指定响应头，告诉浏览器允许跨域访问。

FastAPI内置`CORSMiddleware`，本质就是封装好的中间件。

### 完整配置
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# CORS设置
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "[http://localhost:3000](http://localhost:3000)",
        "[http://127.0.0.1:5173](http://127.0.0.1:5173)"
    ],  # 允许的前端域名，*代表允许所有（生产不要用*）
    allow_credentials=True,  # 是否允许携带cookie
    allow_methods=["*"],     # 允许请求方法 GET/POST/PUT/DELETE
    allow_headers=["*"],     # 允许请求头
)

@app.get("/api/cors-test")
def cors_test():
    return {"msg": "跨域成功"}
```

> ⚠️生产环境要点：
> 1. `allow_origins`不要写`["*"]`同时开启`allow_credentials=True`，会报错；
> 2. 生产写固定前端域名列表；
> 3. 预检OPTIONS请求由CORSMiddleware自动处理，不用自己写路由。

---

# 整合：全套合并代码（包含上一节：统一响应+全局异常 + 本节DI、中间件、CORS）
```python
import time
from typing import Any
from fastapi import FastAPI, Depends, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="FastAPI基础合集")

# ---------------------- CORS ----------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["[http://localhost:5173](http://localhost:5173)"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------- 自定义中间件 ----------------------
@app.middleware("http")
async def cost_middleware(request: Request, call_next):
    s = time.time()
    resp = await call_next(request)
    resp.headers["X-Cost"] = f"{time.time()-s:.4f}"
    return resp

# ---------------------- 统一响应模型 ----------------------
class ResponseModel(BaseModel):
    code: int
    msg: str
    data: Any | None = None

# ---------------------- 全局异常捕获 ----------------------
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return ResponseModel(code=exc.status_code, msg=exc.detail, data=None)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return ResponseModel(code=500, msg="服务器内部错误", data=str(exc))

# ---------------------- 依赖注入 ----------------------
def get_common_params(page: int = 1, size: int = 10):
    return {"page": page, "size": size}

# ---------------------- 路由 ----------------------
@app.get("/api/list", response_model=ResponseModel)
def get_list(params: dict = Depends(get_common_params)):
    return ResponseModel(code=200, msg="success", data=params)

@app.get("/api/error")
def test_error():
    raise HTTPException(status_code=400, detail="参数错误")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", reload=True)
```

## 学习思考题（方便自测）
1. 依赖注入和中间件的区别？什么时候选Depends，什么时候写middleware？
2. CORS预检请求是什么，什么时候浏览器会发OPTIONS请求？
3. 同一个请求多次使用同一个Depends，会执行多次吗？

要不要继续往下学：**APIRouter路由拆分、数据库会话依赖、生命周期事件 startup/shutdown**？