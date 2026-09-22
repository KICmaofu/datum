# Ant Design 组件库接入 + Axios 封装与拦截器

> 
> 基于 **React 18 + Ant Design 5.x + Axios 最新版**，实战向配置，可直接复用到项目中

---

## 一、Ant Design 5.x 组件库接入

Ant Design 是阿里开源的企业级 React UI 组件库，5.x 版本采用 CSS-in-JS 方案，**默认支持按需加载**，无需额外配置按需插件。

### 1. 安装

```
npm install antd
# 或
yarn add antd
```

### 2. 全局配置：ConfigProvider

用于统一配置**主题、国际化、组件默认属性**，一般包裹在应用最外层，和路由配合使用。

```
// main.jsx 入口文件
import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { ConfigProvider } from 'antd'
// 引入中文语言包
import zhCN from 'antd/locale/zh_CN'
import App from './App'

ReactDOM.createRoot(document.getElementById('root')).render(
  <ConfigProvider
    locale={zhCN}
    theme={{
      // 全局主题令牌，定制设计风格
      token: {
        colorPrimary: '#1677ff', // 主色调
        borderRadius: 6,         // 统一圆角
        fontSize: 14             // 基础字号
      }
    }}
  >
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </ConfigProvider>
)
```

> 
> ✅ 5.x 核心优势：无需引入全量 CSS、无需配置 `babel-plugin-import`，组件自动按需加载样式。

### 3. 常用组件实战示例

#### （1）表单组件（替代原生受控表单，自带校验+状态管理）

```
import { Form, Input, Button, message } from 'antd'

export default function LoginForm() {
  // 获取表单实例，用于手动控制表单
  const [form] = Form.useForm()

  // 校验通过后的提交回调
  const onFinish = (values) => {
    console.log('收集的表单数据：', values)
    message.success('提交成功')
  }

  return (
    <Form
      form={form}
      onFinish={onFinish}
      layout="vertical"
      style={{ width: 400, margin: '100px auto' }}
    >
      <Form.Item
        name="username"
        label="用户名"
        rules={[{ required: true, message: '请输入用户名' }]}
      >
        <Input placeholder="请输入用户名" />
      </Form.Item>

      <Form.Item
        name="password"
        label="密码"
        rules={[{ required: true, message: '请输入密码' }]}
      >
        <Input.Password placeholder="请输入密码" />
      </Form.Item>

      <Form.Item>
        <Button type="primary" htmlType="submit" block>
          登录
        </Button>
      </Form.Item>
    </Form>
  )
}
```

#### （2）表格 + 分页组件

```
import { Table, Tag } from 'antd'

const dataSource = [
  { id: 1, name: '张三', role: '管理员', status: 'active' },
  { id: 2, name: '李四', role: '普通用户', status: 'disabled' }
]

export default function UserTable() {
  const columns = [
    { title: 'ID', dataIndex: 'id', key: 'id' },
    { title: '用户名', dataIndex: 'name', key: 'name' },
    { title: '角色', dataIndex: 'role', key: 'role' },
    {
      title: '状态',
      key: 'status',
      render: (_, record) => (
        <Tag color={record.status === 'active' ? 'green' : 'red'}>
          {record.status === 'active' ? '启用' : '禁用'}
        </Tag>
      )
    }
  ]

  return (
    <Table
      rowKey="id"
      dataSource={dataSource}
      columns={columns}
      pagination={{ pageSize: 10, showTotal: total => `共 ${total} 条` }}
    />
  )
}
```

### 4. 核心注意点

- 5.x 移除了 less 依赖，改用 CSS-in-JS，无需配置样式加载器
- 组件无需全量引入，直接 `import { Button } from 'antd'` 自动按需加载
- `Form.useForm()` 管理表单状态，无需手写 `useState` 绑定每个输入框
- 全局提示、弹窗通过 `message`、`Modal` 等 API 直接调用

---

## 二、Axios 封装与拦截器

Axios 是基于 Promise 的 HTTP 客户端，项目中通常会**统一封装**，实现请求头注入、统一错误处理、token 管理、接口重试等通用能力。

### 1. 安装与封装目的

```
npm install axios
```

**为什么要封装？**

- 统一配置 baseURL、超时时间、跨域凭证
- 请求拦截：统一注入 token、签名、请求头
- 响应拦截：统一处理返回格式、业务错误码、登录失效跳转
- 统一错误提示、loading 状态、重复请求取消
- 接口模块化管理，与业务组件解耦

### 2. 完整封装流程

新建 `src/utils/request.js`，作为全局请求工具：

```
import axios from 'axios'
import { message } from 'antd'

// 1. 创建 Axios 实例
const service = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL, // 从环境变量取接口前缀
  timeout: 10000,                            // 超时时间 10s
  withCredentials: true                      // 跨域携带 cookie
})

// 2. 请求拦截器
service.interceptors.request.use(
  (config) => {
    // 统一注入 token
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    // 统一设置请求体类型
    config.headers['Content-Type'] = 'application/json;charset=utf-8'
    return config
  },
  (error) => {
    // 请求错误处理
    return Promise.reject(error)
  }
)

// 3. 响应拦截器
service.interceptors.response.use(
  (response) => {
    const res = response.data
    // 假设后端统一返回格式：{ code: 200, data: ..., msg: '...' }
    if (res.code === 200) {
      return res.data // 直接返回业务数据，组件层不用再解构
    } else {
      // 业务错误：统一提示
      message.error(res.msg || '请求失败')
      // 登录失效：401 清除 token 跳登录
      if (res.code === 401) {
        localStorage.removeItem('token')
        window.location.href = '/login'
      }
      return Promise.reject(new Error(res.msg || '请求失败'))
    }
  },
  (error) => {
    // HTTP 状态码错误处理
    const status = error.response?.status
    switch (status) {
      case 400:
        message.error('请求参数错误')
        break
      case 403:
        message.error('无权限访问')
        break
      case 404:
        message.error('请求地址不存在')
        break
      case 500:
        message.error('服务器内部错误')
        break
      default:
        message.error('网络异常，请稍后重试')
    }
    return Promise.reject(error)
  }
)

// 4. 封装通用请求方法
export const get = (url, params) => {
  return service.get(url, { params })
}

export const post = (url, data) => {
  return service.post(url, data)
}

export const put = (url, data) => {
  return service.put(url, data)
}

export const del = (url) => {
  return service.delete(url)
}

export default service
```

### 3. API 模块化组织

建议按业务模块拆分接口，新建 `src/api/user.js`：

```
import { get, post } from '@/utils/request'

// 用户登录
export const loginApi = (data) => post('/user/login', data)

// 获取用户信息
export const getUserInfoApi = () => get('/user/info')

// 获取用户列表
export const getUserListApi = (params) => get('/user/list', params)
```

### 4. 组件中调用接口

结合 `useState + useEffect` 实现数据请求与渲染：

```
import { useState, useEffect } from 'react'
import { Table, Spin } from 'antd'
import { getUserListApi } from '@/api/user'

export default function UserList() {
  const [list, setList] = useState([])
  const [loading, setLoading] = useState(false)

  const fetchList = async () => {
    setLoading(true)
    try {
      const data = await getUserListApi({ page: 1, pageSize: 10 })
      setList(data.records)
    } catch (err) {
      console.error('获取列表失败', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchList()
  }, [])

  const columns = [
    { title: 'ID', dataIndex: 'id' },
    { title: '用户名', dataIndex: 'username' },
    { title: '邮箱', dataIndex: 'email' }
  ]

  return (
    <Spin spinning={loading}>
      <Table rowKey="id" dataSource={list} columns={columns} />
    </Spin>
  )
}
```

### 5. 进阶最佳实践

- **环境变量**：不同环境（开发/测试/生产）的接口前缀通过 `.env` 文件配置
- **取消重复请求**：通过 `AbortController` 实现短时间内相同请求的取消
- **接口重试**：对网络波动的请求自动重试 2-3 次
- **请求防抖**：搜索类接口防止频繁触发
- **loading 封装**：全局请求 loading，无需每个组件单独维护

---

## 三、核心面试总结

1. **Ant Design 5.x**
   - 采用 CSS-in-JS，默认按需加载，无需配置样式插件
   - `ConfigProvider` 统一管理主题、国际化、全局属性
   - `Form.useForm()` 接管表单状态与校验，无需手动受控绑定
2. **Axios 封装**
   - 创建实例统一配置 baseURL、超时、跨域属性
   - **请求拦截器**：注入 token、统一请求头、参数加密
   - **响应拦截器**：解构业务数据、统一错误处理、401 登录失效跳转
   - 按业务模块拆分 API，组件与网络层解耦

---

需要我补充**接口取消重复请求、自动重试**的进阶封装代码，或者整理一份完整的项目目录结构吗？