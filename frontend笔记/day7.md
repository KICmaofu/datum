# Vite 打包构建 + 环境变量 + 前端代理 完整配置
> 基于 **Vite 5.x + React 18** 技术栈，与前文 Axios、路由、状态管理完全联动，覆盖开发/测试/生产全流程工程化配置。

---

## 一、打包构建配置
Vite 底层基于 Rollup 实现生产构建，通过 `vite.config.js` 统一配置构建行为，可自定义输出目录、资源路径、代码压缩、拆包策略等。

### 1. 核心构建命令
在 `package.json` 中定义脚本：
```json
{
  "scripts": {
    "dev": "vite",                // 启动开发服务器
    "build": "vite build",         // 生产环境打包
    "build:test": "vite build --mode test",  // 测试环境打包
    "preview": "vite preview"      // 本地预览打包后的产物
  }
}
```

### 2. 常用构建配置项
新建项目根目录 `vite.config.js`，核心构建相关配置如下：
```js
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],

  // 1. 项目部署基础路径（重要！部署到子目录必须配置）
  // 例如部署在 [https://domain.com/admin/](https://domain.com/admin/) 则 base: '/admin/'
  base: './',

  // 构建相关配置
  build: {
    outDir: 'dist',           // 打包输出目录，默认 dist
    assetsDir: 'static',      // 静态资源（js/css/img）输出目录
    sourcemap: false,         // 生产环境关闭 sourcemap，避免泄露源码
    minify: 'esbuild',        // 压缩工具，esbuild 速度快；terser 压缩率更高
    target: 'es2015',         // 兼容目标浏览器版本

    // Rollup 自定义拆包（性能优化核心）
    rollupOptions: {
      output: {
        // 静态资源文件名哈希，利用浏览器缓存
        chunkFileNames: 'static/js/[name]-[hash].js',
        entryFileNames: 'static/js/[name]-[hash].js',
        assetFileNames: 'static/[ext]/[name]-[hash].[ext]',

        // 手动代码分割：第三方库单独打包，不常变更，利用长期缓存
        manualChunks: {
          'react-vendor': ['react', 'react-dom'],
          'antd-vendor': ['antd'],
          'axios-vendor': ['axios']
        }
      }
    },

    // 构建时清除 console 和 debugger
    esbuild: {
      drop: ['console', 'debugger']
    }
  }
})
```

### 3. 常见构建优化点
1. **代码分割**：将第三方依赖、公共组件单独拆包，避免单个文件过大，利用浏览器缓存
2. **按需加载**：配合路由懒加载 `React.lazy`，拆分页面代码，首屏只加载必要资源
3. **静态资源压缩**：图片压缩、SVG 优化、Gzip/Brotli 压缩（需 Nginx 配合）
4. **移除无用代码**：Tree Shaking 自动剔除未使用的代码
5. **关闭生产 sourcemap**：减小包体积，提升安全性

---

## 二、环境变量区分（多环境配置）
解决开发、测试、生产环境接口地址、开关配置不一致的问题，不同环境加载对应配置，无需修改代码。

### 1. 环境变量文件规则
Vite 根据 `--mode` 加载对应环境文件，文件放在项目根目录：
| 文件名 | 加载时机 | 说明 |
|--------|----------|------|
| `.env` | 所有环境通用 | 基础配置，特定环境会覆盖同名变量 |
| `.env.development` | `npm run dev` | 开发环境专属 |
| `.env.production` | `npm run build` | 生产环境专属 |
| `.env.test` | `npm run build --mode test` | 自定义测试环境 |

> 加载优先级：特定环境文件 > 通用 `.env` 文件

### 2. 变量命名与读取
- **强制规则**：只有以 `VITE_` 开头的变量才会暴露到前端代码中，防止敏感配置泄露
- 读取方式：代码中通过 `import.meta.env.VITE_XXX` 读取

### 3. 多环境文件示例
#### 开发环境 `.env.development`
```env
# 接口前缀（开发环境走代理，写相对路径）
VITE_API_BASE_URL = /api
# 应用标题
VITE_APP_TITLE = 管理系统-开发版
```

#### 生产环境 `.env.production`
```env
# 生产环境真实接口地址
VITE_API_BASE_URL = [https://api.yourdomain.com](https://api.yourdomain.com)
VITE_APP_TITLE = 管理系统
```

#### 测试环境 `.env.test`
```env
VITE_API_BASE_URL = [https://test-api.yourdomain.com](https://test-api.yourdomain.com)
VITE_APP_TITLE = 管理系统-测试版
```

### 4. 与 Axios 联动实战
前文封装的 Axios 直接使用环境变量作为 baseURL，自动适配环境：
```js
// src/utils/request.js
const service = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  timeout: 10000
})
```

> ✅ 优势：切换环境只需要执行不同的打包命令，代码完全不用改。

### 5. TypeScript 类型补充（可选）
如果使用 TS，新建 `src/vite-env.d.ts` 补全环境变量类型提示：
```ts
interface ImportMetaEnv {
  readonly VITE_API_BASE_URL: string
  readonly VITE_APP_TITLE: string
}
interface ImportMeta {
  readonly env: ImportMetaEnv
}
```

---

## 三、前端代理配置（解决开发跨域）
### 1. 跨域问题成因
浏览器**同源策略**限制：协议、域名、端口三者有一个不同，就会拦截 AJAX 请求。开发环境前端跑在 `[http://localhost:5173](http://localhost:5173)`，后端接口在 `[http://localhost:8080](http://localhost:8080)`，端口不同，必然跨域。

> 开发代理仅在本地开发环境生效，生产环境跨域需要后端配置 CORS 或 Nginx 反向代理。

### 2. Vite 代理配置详解
在 `vite.config.js` 的 `server.proxy` 中配置，原理是**本地开发服务器作为中间层转发请求**，浏览器请求本地服务器，服务器再转发给后端，绕过浏览器同源限制。

```js
export default defineConfig({
  server: {
    port: 5173,         // 前端开发服务器端口
    open: true,         // 启动自动打开浏览器
    cors: true,         // 允许跨域

    // 代理配置
    proxy: {
      // 匹配 /api 开头的请求，转发到目标后端
      '/api': {
        target: '[http://localhost:8080](http://localhost:8080)',  // 后端接口地址
        changeOrigin: true,               // 修改请求头 host 为目标地址，避免后端校验拦截
        rewrite: (path) => path.replace(/^\/api/, '') // 路径重写：去掉 /api 前缀
      }
    }
  }
})
```

### 3. 配置说明与示例
#### 场景：后端接口没有前缀
后端真实接口：`[http://localhost:8080/user/list](http://localhost:8080/user/list)`
前端请求写法：`/api/user/list`
代理转发流程：
1. 浏览器请求 `[http://localhost:5173/api/user/list](http://localhost:5173/api/user/list)`（同源，不跨域）
2. Vite 服务器匹配到 `/api` 前缀
3. 路径重写去掉 `/api`，转发到 `[http://localhost:8080/user/list](http://localhost:8080/user/list)`
4. 后端返回数据，Vite 再返回给前端

### 4. 多后端代理配置
如果项目对接多个不同后端服务，配置多个代理项：
```js
proxy: {
  '/api': {
    target: '[http://localhost:8080](http://localhost:8080)',
    changeOrigin: true,
    rewrite: (path) => path.replace(/^\/api/, '')
  },
  // OSS 文件服务
  '/oss': {
    target: '[http://oss-cn-beijing.aliyuncs.com](http://oss-cn-beijing.aliyuncs.com)',
    changeOrigin: true,
    rewrite: (path) => path.replace(/^\/oss/, '')
  }
}
```

### 5. 生产环境跨域方案
开发代理只在本地生效，打包后不存在 devServer，生产环境两种主流方案：
1. **后端开启 CORS**：后端配置响应头 `Access-Control-Allow-Origin`，允许前端域名访问
2. **Nginx 反向代理**：前端和接口部署在同一个域名下，通过路径前缀区分，Nginx 转发 `/api` 到后端服务

---

## 四、完整 `vite.config.js` 参考
```js
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig(({ mode }) => {
  // 可根据 mode 动态返回不同配置
  return {
    plugins: [react()],
    base: './',

    // 路径别名：@ 指向 src 目录
    resolve: {
      alias: {
        '@': path.resolve(__dirname, 'src')
      }
    },

    // 开发服务器 + 代理
    server: {
      port: 5173,
      open: true,
      proxy: {
        '/api': {
          target: '[http://localhost:8080](http://localhost:8080)',
          changeOrigin: true,
          rewrite: (path) => path.replace(/^\/api/, '')
        }
      }
    },

    // 生产构建配置
    build: {
      outDir: 'dist',
      assetsDir: 'static',
      sourcemap: false,
      esbuild: {
        drop: mode === 'production' ? ['console', 'debugger'] : []
      },
      rollupOptions: {
        output: {
          manualChunks: {
            'react-core': ['react', 'react-dom'],
            'ui-lib': ['antd'],
            'http': ['axios']
          }
        }
      }
    }
  }
})
```

---

## 五、面试核心总结
1. **环境变量**
   - Vite 变量必须以 `VITE_` 开头，通过 `import.meta.env` 读取
   - 按 mode 加载对应 `.env.xxx` 文件，通用配置放 `.env`
   - 不同环境通过打包命令 `--mode` 切换，无需修改业务代码

2. **开发代理**
   - 解决开发环境浏览器同源策略跨域问题，仅开发环境生效
   - 原理：本地开发服务器作为转发中间层
   - 核心参数：`target` 目标地址、`changeOrigin` 修改请求头、`rewrite` 路径重写
   - 生产环境方案：后端 CORS 或 Nginx 反向代理

3. **构建优化**
   - `base` 配置部署子路径，解决静态资源 404
   - `manualChunks` 拆分第三方依赖，利用浏览器缓存
   - 生产环境关闭 sourcemap、移除 console，减小包体积提升安全性
   - 配合路由懒加载实现代码按页面拆分，优化首屏加载

---

需要我补充 **Nginx 生产环境部署配置**，或者更深入的**构建体积分析与优化方案**吗？