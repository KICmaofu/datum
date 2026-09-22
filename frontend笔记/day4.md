# React Router v6 + 页面布局、导航栏 知识点

> 
> 配套代码示例，面试重点 + 实操要点，基于 `react-router-dom@6`

## 一、核心变化（v6 和 v5 最大区别，面试常问）

1. 移除 `<Switch>`，替换为 `<Routes>`
2. `<Route>` 必须写 `element={<组件 />}`，不再用 `component` / `render`
3. 路由匹配规则：**精确匹配默认开启**，不再需要 `exact`
4. 嵌套路由依靠 `<Outlet>` 渲染子页面
5. 编程式导航用 `useNavigate`，废弃 `useHistory`
6. 路由参数读取：`useParams()`
7. 相对路径：嵌套路由里的 path 是相对父路由

## 二、基础路由配置

### 1. 入口包裹 BrowserRouter

```
// main.jsx
import { BrowserRouter } from 'react-router-dom'
import App from './App'

ReactDOM.createRoot(document.getElementById('root')).render(
  <BrowserRouter>
    <App />
  </BrowserRouter>
)
```

### 2. Routes + Route 基础写法

```
import { Routes, Route } from 'react-router-dom'
import Home from './pages/Home'
import About from './pages/About'
import NotFound from './pages/NotFound'

function App() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/about" element={<About />} />
      {/* 404 页面，放在最后 */}
      <Route path="*" element={<NotFound />} />
    </Routes>
  )
}
```

## 三、嵌套路由 + 布局页面（Layout + 导航栏核心）

> 
> 业务最常用：**公共布局（侧边栏/顶部导航）不变，中间内容区域切换页面**
> `<Outlet>`：子路由渲染出口，相当于子页面占位符

```
// Layout.jsx 公共布局（包含导航栏）
import { Outlet, Link } from 'react-router-dom'

export default function Layout() {
  return (
    <div className="layout">
      {/* 导航栏 */}
      <nav className="navbar">
        <Link to="/">首页</Link>
        <Link to="/about">关于</Link>
        <Link to="/user">用户中心</Link>
      </nav>
      {/* 子页面渲染在这里 */}
      <main className="page-content">
        <Outlet />
      </main>
    </div>
  )
}
```

路由配置：

```
// App.jsx
<Routes>
  {/* 父布局路由 */}
  <Route path="/" element={<Layout />}>
    {/* 子路由，path 相对父路由 */}
    {/* index 路由：访问父路由 "/" 默认渲染的页面 */}
    <Route index element={<Home />} />
    <Route path="about" element={<About />} />
    <Route path="user" element={<User />} />
  </Route>
  <Route path="*" element={<NotFound />} />
</Routes>
```

> 
> ✅ 重点：`index` 路由，父路由 `/` 匹配时，默认展示 index 对应的组件

## 四、导航相关API

### 1. 声明式导航 `<Link>`

替代 a 标签，阻止页面刷新

```
<Link to="/about">关于页面</Link>
{/* 带参数跳转 */}
<Link to={`/user/${id}`}>用户详情</Link>
{/* 传 state 隐式参数 */}
<Link to="/user" state={{ name: 'test' }}>用户</Link>
```

`<NavLink>`：导航高亮，自带 `active` 类名

```
import { NavLink } from 'react-router-dom'
<NavLink to="/" className={({isActive}) => isActive ? 'active' : ''}>首页</NavLink>
```

### 2. 编程式导航 useNavigate

```
import { useNavigate } from 'react-router-dom'

function Demo() {
  const navigate = useNavigate()
  const goAbout = () => {
    navigate('/about') // 前进
    // navigate(-1) // 返回上一页
    // navigate('/user/100', { state: { msg: 'hello' } })
  }
  return <button onClick={goAbout}>跳转到关于</button>
}
```

## 五、路由参数获取

1. 路径参数 `/user/:id`

```
//路由配置
<Route path="user/:id" element={<UserDetail />}/>

// UserDetail.jsx
import { useParams } from 'react-router-dom'
export default function UserDetail(){
  const { id } = useParams()
  return <div>用户id：{id}</div>
}
```

2. state 参数（隐式传参，地址栏看不见）

```
import { useLocation } from 'react-router-dom'
const location = useLocation()
console.log(location.state)
```

## 六、路由懒加载（性能优化，面试加分）

```
import { lazy, Suspense } from 'react'
const Home = lazy(() => import('./pages/Home'))

<Route path="/" element={
  <Suspense fallback={<div>加载中...</div>}>
    <Layout />
  </Suspense>
}>
```

## 七、路由守卫（v6没有内置守卫，两种实现方案）

1. 封装高阶组件 HOC 包装路由组件（权限校验）
2. 在 Layout 组件中 `useEffect` + `useNavigate` 判断登录状态跳转

示例简易权限路由：

```
import { Navigate, Outlet } from 'react-router-dom'
export function AuthRoute() {
  const isLogin = false
  if (!isLogin) {
    return <Navigate to="/login" replace />
  }
  return <Outlet />
}
```

使用：

```
<Route path="/admin" element={<AuthRoute />}>
  <Route index element={<Admin />}/>
</Route>
```

> 
> `Navigate`：v6 重定向组件，`replace` 替换历史栈，无法回退

## 八、面试精简背诵版

1. React Router v6 使用 `BrowserRouter` 包裹应用入口，`<Routes>` 替代 Switch
2. `<Route>` 通过 `element` 渲染组件，嵌套路由配合 `<Outlet>` 实现公共布局（导航栏+侧边栏）
3. `index` 路由用于父路由默认渲染页面；`<NavLink>` 实现导航菜单高亮
4. 声明导航 `<Link>`，编程导航 `useNavigate`（v5 useHistory废弃）
5. `useParams` 获取路径参数；`useLocation` 获取地址、state参数
6. 权限路由：使用 `<Navigate>` 做重定向，自行封装权限组件实现路由守卫
7. 路由懒加载：`React.lazy + Suspense`，拆分代码包优化首屏加载

## 九、实操验收目标

✅ 搭建带顶部导航栏的 Layout 公共布局
✅ 实现嵌套路由，导航切换，公共布局不刷新
✅ NavLink 菜单选中高亮
✅ 路由传参（params / state）
✅ 404页面 + 权限路由拦截
✅ 路由懒加载

---

要不要我给你出一套**练习题**（含需求描述，你来写路由代码），或者把这部分整理成一页可直接复制的面试问答清单？