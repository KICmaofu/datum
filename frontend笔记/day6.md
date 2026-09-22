# Zustand 轻量状态管理 + 全局用户状态实战

> 
> 基于 **Zustand v4**，对比 Redux 无样板代码、无需 Provider 包裹、体积极小，是目前 React 生态最主流的轻量状态管理方案。结合全局用户状态场景，串联之前的 Axios、路由守卫形成完整闭环。

---

## 一、Zustand 核心概述

### 1. 是什么 & 核心优势

Zustand 是一款极简的 React 状态管理库，解决跨组件、跨页面共享状态的需求。对比 Redux：

- **零样板代码**：不需要 action、reducer、dispatch、type 常量
- **无需 Provider 包裹**：直接导入即可使用，不嵌套组件树
- **天然支持异步**：store 里直接写 async 方法
- **精确更新**：支持选择器，只订阅需要的状态，减少无效重渲染
- **体积极小**：不到 1KB，对包体积几乎无影响

适用场景：中小项目全局状态、复杂组件间状态共享、替代 Context 避免层层透传。

### 2. 安装

```
npm install zustand
```

---

## 二、基础使用

### 1. 创建 Store

使用 `create` 函数创建 store，内部通过 `set` 更新状态，`get` 获取当前状态。

```
// src/store/counterStore.js
import { create } from 'zustand'

const useCounterStore = create((set, get) => ({
  // 状态
  count: 0,
  
  // 同步方法：更新状态
  increment: () => set(state => ({ count: state.count + 1 })),
  
  // 直接赋值式更新（浅层合并）
  decrement: () => set({ count: get().count - 1 }),
  
  // 重置
  reset: () => set({ count: 0 })
}))

export default useCounterStore
```

### 2. 组件中使用

直接导入 hook，**可直接解构，也可通过选择器精确订阅**。

```
import useCounterStore from '@/store/counterStore'

export default function Counter() {
  // 方式1：选择器精确取值（推荐，减少重渲染）
  const count = useCounterStore(state => state.count)
  const increment = useCounterStore(state => state.increment)

  // 方式2：一次性解构（不推荐，状态全量订阅，任何变化都重渲染）
  // const { count, increment } = useCounterStore()

  return (
    <div>
      <p>计数：{count}</p>
      <button onClick={increment}>+1</button>
    </div>
  )
}
```

### 3. 核心 API

| API | 作用 |
| --- | --- |
| `set(partial)` | 更新状态，支持对象或函数，默认浅层合并 |
| `get()` | 同步获取当前最新状态，用于方法内部取值 |
| `useStore(selector)` | 组件订阅状态，返回 selector 的结果 |
| `useStore.getState()` | **非组件环境获取状态**（重点，拦截器/工具函数中用） |
| `useStore.setState()` | 非组件环境更新状态 |

---

## 三、进阶核心能力

### 1. 渲染优化：选择器 + 浅层比较

当选择器返回对象时，使用 `shallow` 浅层比较，避免因引用变化导致的无效重渲染。

```
import { shallow } from 'zustand/shallow'

// 返回对象时，必须加 shallow，否则每次渲染都是新对象
const { userInfo, token } = useUserStore(
  state => ({ userInfo: state.userInfo, token: state.token }),
  shallow
)
```

### 2. 非组件中调用 Store（实战必备）

在 Axios 拦截器、工具函数等非 React 组件中，**不能使用 hook**，通过 `getState()` 直接读取状态。

```
import useUserStore from '@/store/userStore'

// 读取token
const token = useUserStore.getState().token

// 更新状态
useUserStore.setState({ token: 'new-token' })
```

### 3. 持久化中间件 persist

自动将状态同步到 localStorage / sessionStorage，刷新页面不丢失，是全局用户状态的核心依赖。

```
import { create } from 'zustand'
import { persist } from 'zustand/middleware'

const useStore = create(
  persist(
    (set) => ({ /* 状态和方法 */ }),
    {
      name: 'store-key',       // 存储在 localStorage 的 key 名
      partialize: (state) => ({ // 只持久化指定字段，敏感字段可排除
        token: state.token
      })
    }
  )
)
```

---

## 四、实战：全局用户状态管理（完整方案）

这是 Zustand 最常用的场景：统一管理 token、用户信息、登录/登出逻辑，联动 Axios 拦截器和路由守卫。

### 1. 创建用户 Store

```
// src/store/userStore.js
import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { loginApi, getUserInfoApi } from '@/api/user'

const useUserStore = create(
  persist(
    (set, get) => ({
      // 状态
      token: '',
      userInfo: null,
      isLogin: false,

      // 登录方法：调用接口 + 存状态
      login: async (loginForm) => {
        const res = await loginApi(loginForm)
        set({
          token: res.token,
          isLogin: true
        })
        // 登录成功后拉取用户详情
        await get().fetchUserInfo()
        return res
      },

      // 获取用户信息
      fetchUserInfo: async () => {
        const res = await getUserInfoApi()
        set({ userInfo: res })
      },

      // 登出：清空状态 + 清除持久化
      logout: () => {
        set({ token: '', userInfo: null, isLogin: false })
        // 可选：跳转登录页
        window.location.href = '/login'
      },

      // 更新部分用户信息
      updateUserInfo: (partialInfo) => {
        set(state => ({
          userInfo: { ...state.userInfo, ...partialInfo }
        }))
      }
    }),
    {
      name: 'user-store',
      // 只持久化 token，用户信息刷新后重新拉取（更安全）
      partialize: (state) => ({ token: state.token })
    }
  )
)

export default useUserStore
```

### 2. 联动 Axios 拦截器

改造之前的 Axios 封装，从 Store 统一获取 token，登录失效时调用登出方法。

```
// src/utils/request.js
import axios from 'axios'
import { message } from 'antd'
import useUserStore from '@/store/userStore'

const service = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  timeout: 10000
})

// 请求拦截：注入 token
service.interceptors.request.use(config => {
  // 非组件中通过 getState() 取 token
  const token = useUserStore.getState().token
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// 响应拦截：401 统一登出
service.interceptors.response.use(
  response => {
    const res = response.data
    if (res.code === 200) return res.data
    
    message.error(res.msg)
    if (res.code === 401) {
      // token 失效，调用登出清空状态
      useUserStore.getState().logout()
    }
    return Promise.reject(new Error(res.msg))
  },
  error => {
    message.error('网络异常')
    return Promise.reject(error)
  }
)

export default service
```

### 3. 联动路由守卫

改造之前的权限路由组件，从 Store 读取登录状态。

```
// src/components/AuthRoute.jsx
import { Navigate, Outlet } from 'react-router-dom'
import useUserStore from '@/store/userStore'

export default function AuthRoute() {
  const isLogin = useUserStore(state => state.isLogin)
  const token = useUserStore(state => state.token)

  // 有 token 视为已登录，渲染子路由
  if (token) {
    return <Outlet />
  }
  
  // 未登录重定向到登录页
  return <Navigate to="/login" replace />
}
```

路由配置中使用：

```
<Routes>
  <Route path="/login" element={<Login />} />
  
  {/* 需要登录的路由 */}
  <Route element={<AuthRoute />}>
    <Route path="/" element={<Layout />}>
      <Route index element={<Home />} />
      <Route path="user" element={<User />} />
    </Route>
  </Route>
</Routes>
```

### 4. 组件中使用

#### 登录页

```
import { Form, Input, Button, message } from 'antd'
import useUserStore from '@/store/userStore'
import { useNavigate } from 'react-router-dom'

export default function Login() {
  const login = useUserStore(state => state.login)
  const navigate = useNavigate()

  const onFinish = async (values) => {
    try {
      await login(values)
      message.success('登录成功')
      navigate('/')
    } catch (err) {
      console.error('登录失败', err)
    }
  }

  return (
    <Form onFinish={onFinish}>
      <Form.Item name="username" rules={[{ required: true }]}>
        <Input placeholder="用户名" />
      </Form.Item>
      <Form.Item name="password" rules={[{ required: true }]}>
        <Input.Password placeholder="密码" />
      </Form.Item>
      <Button type="primary" htmlType="submit" block>登录</Button>
    </Form>
  )
}
```

#### 导航栏显示用户信息

```
import { Avatar, Dropdown } from 'antd'
import useUserStore from '@/store/userStore'

export default function Header() {
  const userInfo = useUserStore(state => state.userInfo)
  const logout = useUserStore(state => state.logout)

  const items = [
    { key: 'logout', label: '退出登录', onClick: logout }
  ]

  return (
    <div className="header">
      <Dropdown menu={{ items }}>
        <Avatar src={userInfo?.avatar}>
          {userInfo?.username?.charAt(0)}
        </Avatar>
      </Dropdown>
    </div>
  )
}
```

---

## 五、最佳实践 & 面试要点

### 1. 最佳实践

- **按模块拆分 Store**：用户、应用配置、购物车等各自独立，不要写一个大 Store
- **持久化按需开启**：敏感信息不要存在 localStorage，token 可加密存储
- **优先使用选择器**：精确订阅需要的状态，减少组件重渲染
- **业务逻辑下沉 Store**：接口调用、数据处理放在 store 里，组件只负责渲染和交互
- **初始化数据放在 useEffect**：页面刷新后，在根组件 useEffect 中重新拉取用户信息

### 2. 面试高频总结

1. **Zustand 对比 Redux**：无样板代码、无需 Provider、体积小、上手快，适合中小项目；Redux 适合大型项目、严格数据流、时间旅行调试
2. **Zustand 原理**：发布订阅模式，set 触发通知，订阅了对应状态的组件重新渲染
3. **非组件中如何使用**：通过 `store.getState()` 和 `store.setState()`
4. **持久化实现**：`persist` 中间件，默认存 localStorage，可自定义存储引擎
5. **如何避免重渲染**：使用选择器精确取值，返回对象时配合 `shallow` 浅层比较

---

需要我补充 **多模块 Store 拆分示例**，或者实现一个带刷新 token、接口防抖的完整用户状态方案吗？