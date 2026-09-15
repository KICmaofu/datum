# FastAPI：路由定义、参数解析、Swagger自动文档
> 核心：**Python类型注解 + Pydantic**，自动参数解析、自动校验、自动生成OpenAPI规范，Swagger UI交互式文档开箱即用，无需手动写文档。
> 安装依赖：
> ```bash
> pip install fastapi uvicorn pydantic
> ```

## 一、路由定义（路径操作）
`@app.get` / `@app.post` / `@app.put` / `@app.delete` 称为**路径操作装饰器**
- `async def`：异步接口，推荐IO密集场景；普通`def`同步函数也支持
- `summary`：接口简短标题；`description`：详细说明，会展示在Swagger文档

```python
from fastapi import FastAPI

app = FastAPI(title="商品API", version="1.0")

# GET根路由
@app.get("/", summary="首页", description="欢迎页面")
async def root():
    return {"msg": "Hello FastAPI"}

# GET查询接口
@app.get("/items")
async def list_items():
    return {"items": ["A","B"]}

# POST新增接口
@app.post("/items", summary="创建商品")
async def create_item():
    return {"code": 200, "msg": "创建成功"}
```

### 路由匹配规则
1. 精确路由优先于动态路由；
2. `{param}`动态路由，**路径参数必须匹配**，否则404；
3. 支持路由拆分`APIRouter`（大型项目模块化）

```python
from fastapi import APIRouter

user_router = APIRouter(prefix="/user", tags=["用户模块"])
@user_router.get("/{uid}")
async def get_user(uid:int):
    return {"uid":uid}
app.include_router(user_router)
```

## 二、参数解析（4大类参数）
FastAPI**自动识别参数来源**，依据：
- 在路由`{}`中 → **路径参数 Path**
- 普通基础类型（int/str/bool），不在路由{}内 → **查询参数 Query**
- Pydantic模型类型 → **请求体 Body（JSON）**
- Form、File：表单/文件上传参数

### 1）路径参数 Path（写在URL路径里）
URL：`/item/100`，`100`就是item_id
```python
from fastapi import Path

@app.get("/item/{item_id}")
async def get_item(
    item_id: int = Path(gt=0, description="商品ID，大于0")
):
    return {"item_id": item_id}
```
✅ 特点：**必填**；类型自动转换；校验失败返回`422 Unprocessable Entity`，返回详细错误信息

### 2）查询参数 Query（URL `?key=val&a=1`）
URL：`/search?keyword=phone&page=1`
```python
from fastapi import Query

@app.get("/search")
async def search(
    keyword: str = Query(min_length=2, max_length=20, description="搜索关键词"),
    page: int = Query(default=1, ge=1, description="页码，默认1"),
    limit: int | None = Query(None, le=100) # 可选参数
):
    return {"keyword": keyword, "page": page, "limit": limit}
```
- 带`default=xxx` → 可选参数；无默认值则必填

### 3）请求体参数 Body（POST/PUT JSON，Pydantic BaseModel）
复杂结构化数据，前端传JSON，**仅POST/PUT推荐使用**
```python
from pydantic import BaseModel, Field

# 定义模型，自动校验 + 自动生成Swagger schema
class ItemCreate(BaseModel):
    name: str = Field(..., description="商品名称")
    price: float = Field(gt=0, description="价格，必须大于0")
    desc: str | None = Field(None, description="商品描述，可选")

@app.post("/item")
async def add_item(item: ItemCreate):
    # item是Pydantic对象，item.model_dump()转为字典
    return {"data": item.model_dump(), "msg":"新增成功"}
```
> 关键：`Field`用于模型字段校验，会同步展示在Swagger文档。

### 4）混合参数（路径+查询+请求体一起用）
```python
@app.put("/item/{item_id}")
async def update_item(
    item_id: int = Path(gt=0),        # 路径参数
    item: ItemCreate,                 # 请求体JSON
    q: str | None = Query(None)       # 查询参数
):
    res = {"item_id": item_id, **item.model_dump()}
    if q:
        res["q"] = q
    return res
```

## 三、Swagger自动文档（OpenAPI）
FastAPI内置OpenAPI规范，**零配置自动生成**


启动服务：
```bash
uvicorn main:app --reload
```
访问地址：
1. Swagger UI（交互式，可在线调试接口）：`[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)`
2. ReDoc（静态文档）：`[http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)`
3. OpenAPI原始JSON：`[http://127.0.0.1:8000/openapi.json](http://127.0.0.1:8000/openapi.json)`

### Swagger文档特性
1. 自动读取类型注解、`summary`、`description`、`Query/Path/Field`的描述；
2. 自动识别请求参数、请求体JSON结构、返回示例；
3. **Try it out**：网页直接填参数、发送请求、看响应，前后端联调非常方便；
4. 代码改动后`--reload`自动刷新文档；
5. tags分组：给接口分类，文档上按模块折叠。

```python
# tags分组示例
@app.get("/item", tags=["商品管理"], summary="获取商品列表")
async def get_list():
    return []
```

## 四、核心原理与面试考点
1. FastAPI依靠**Pydantic**做数据校验，**Starlette**做Web路由；类型注解不是单纯注释，运行期生效。
2. 校验失败返回`422`，返回结构化错误信息，包含错误字段、原因。
3. 参数识别优先级：**路径参数 > 查询参数 > 请求体**
4. Swagger底层是OpenAPI标准，不是第三方插件，**代码即文档**，避免文档和接口不一致。
5. `Path/Query/Field`作用：增加校验规则 + 给文档添加描述。

### 参数对比汇总
| 参数类型 | 位置 | 使用场景 | 声明方式 |
|---|---|---|---|
| Path路径参数 | URL路径`/{id}` | 资源唯一标识 | `Path()` |
| Query查询参数 | URL`?a=1` | 分页、过滤关键词 | `Query()` |
| Body请求体 | Request JSON | 提交复杂对象（新增/修改） | Pydantic BaseModel |

## 完整可运行整合代码
```python
from fastapi import FastAPI, Path, Query
from pydantic import BaseModel, Field

app = FastAPI(title="FastAPI演示接口", version="1.0", description="路由+参数+Swagger示例")

class Item(BaseModel):
    name: str = Field(..., description="商品名称")
    price: float = Field(gt=0, description="价格>0")
    description: str | None = Field(None, description="描述信息")

@app.get("/item/{item_id}", tags=["商品"], summary="获取单个商品")
async def get_item(
    item_id: int = Path(gt=1, description="商品ID必须大于1"),
    q: str | None = Query(None, description="查询附加参数")
):
    return {"item_id": item_id, "query": q, "data": {"name":"测试商品"}}

@app.post("/item", tags=["商品"], summary="新建商品")
async def create_item(item: Item):
    return {"msg": "创建成功", "item": item.model_dump()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", reload=True)
```
运行后打开 `[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)`，直接在线测试接口。


要不要继续学习FastAPI响应模型、异常处理、依赖注入？或者写一套前后端联调完整案例（React前端调用FastAPI）。