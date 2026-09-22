# FastAPI 文件上传/下载 + 静态资源托管
> 承接前面学的：Pydantic校验、统一响应、全局异常、依赖注入、中间件、CORS。下面是基础知识点 + 完整可运行示例。

## 一、知识点梳理
### 1. 文件上传
FastAPI 使用 `UploadFile` 接收文件，底层是 starlette 的文件封装。
- `UploadFile` 属性：
  - `filename`：原始文件名
  - `content_type`：MIME类型
  - `file`：类文件对象（spooled临时文件，小文件内存，大文件落盘）
- 两种接收方式：
  1. `UploadFile`：推荐，支持大文件、异步、获取元信息
  2. `bytes`：一次性读入内存，只适合小文件

> 校验要点：文件大小限制、后缀白名单、MIME校验、文件名防注入。

### 2. 文件下载接口
两种方案：
1. `FileResponse`：本地文件返回，自动识别MIME，支持断点续传
2. `StreamingResponse`：流式返回（内存文件、大文件分片下载，不一次性加载进内存）

### 3. 静态资源托管
`StaticFiles`，starlette内置中间件，把目录下文件直接HTTP访问，适合图片、前端打包产物。
> 注意：生产环境推荐 nginx 托管静态资源，FastAPI仅用于开发。

---

## 二、完整代码示例
```python
from fastapi import FastAPI, UploadFile, File, Query, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
import os
import uuid

app = FastAPI(title="文件上传下载&静态资源")

# 目录初始化
UPLOAD_DIR = "./uploads"
STATIC_DIR = "./static"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)

# ====================== 静态资源托管 ======================
# 挂载静态目录，访问：[http://127.0.0.1:8000/static/xxx.jpg](http://127.0.0.1:8000/static/xxx.jpg)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# ====================== 文件上传接口 ======================
@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    # 后缀白名单校验
    allow_suffix = {"jpg", "jpeg", "png", "pdf"}
    suffix = file.filename.split(".")[-1].lower()
    if suffix not in allow_suffix:
        raise HTTPException(status_code=400, detail="不允许上传该类型文件")
    
    # 生成唯一文件名，防止重名覆盖
    new_filename = f"{uuid.uuid4()}.{suffix}"
    save_path = os.path.join(UPLOAD_DIR, new_filename)

    # 写入文件
    with open(save_path, "wb") as f:
        f.write(await file.read())

    return {
        "code": 200,
        "msg": "上传成功",
        "data": {
            "origin_name": file.filename,
            "save_name": new_filename,
            "url": f"/static/{new_filename}"
        }
    }

# ====================== 文件下载接口 FileResponse ======================
@app.get("/download")
async def download(file_name: str = Query(...)):
    file_path = os.path.join(UPLOAD_DIR, file_name)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="文件不存在")
    # media_type 指定返回类型，filename 是浏览器下载显示名称
    return FileResponse(
        path=file_path,
        filename=file_name,
        media_type="application/octet-stream"
    )

# ====================== 流式下载 StreamingResponse（大文件） ======================
def iter_file(path: str):
    with open(path, "rb") as f:
        while chunk := f.read(1024 * 1024):  # 每次读取1MB
            yield chunk

@app.get("/stream-download")
async def stream_download(file_name: str = Query(...)):
    file_path = os.path.join(UPLOAD_DIR, file_name)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="文件不存在")
    return StreamingResponse(
        iter_file(file_path),
        media_type="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{file_name}"'}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
```

## 三、重点细节与坑点
### ✅ 文件上传
1. **大文件**：不要一次性 `await file.read()`，会爆内存；可以分块读取 `await file.read(1024)` 循环写入
2. **文件名安全**：不要直接使用前端传来的`filename`保存，容易路径穿越攻击（`../../etc/passwd`），必须重命名
3. **大小限制**：uvicorn 默认无限制，可以在中间件校验请求体大小；nginx层也可以限制

### ✅ 静态资源
- `app.mount` 是挂载子应用，顺序有影响：路由写在 mount **前面**
- `StaticFiles` 默认不列出目录，访问文件夹会404，安全
- 生产：静态文件交给 Nginx / Caddy，FastAPI只负责业务接口

### ✅ 下载两种响应对比
| 类型 | 适用场景 | 优点 |
|---|---|---|
| FileResponse | 本地磁盘文件 | 自动处理断点、ETag，代码简单 |
| StreamingResponse | 超大文件、内存文件、数据库二进制 | 流式输出，不占用大量内存 |

## 四、扩展：多文件上传
```python
@app.post("/upload-multi")
async def upload_multi(files: list[UploadFile] = File(...)):
    result = []
    for file in files:
        new_name = f"{uuid.uuid4()}.{file.filename.split('.')[-1]}"
        with open(os.path.join(UPLOAD_DIR, new_name), "wb") as f:
            f.write(await file.read())
        result.append({"origin": file.filename, "saved": new_name})
    return {"code":200, "data": result}
```

## 五、配套前面知识
- 可以把**文件大小、后缀校验**封装成【依赖注入】，所有上传接口复用
- 文件不存在、文件过大异常，接入【全局异常处理器】统一返回JSON格式
- 跨域继续使用 `CORSMiddleware`

---

要不要我继续下一节：**数据库会话管理、ORM模型（SQLAlchemy）基础**，继续保持这种知识点+可运行代码的学习节奏？