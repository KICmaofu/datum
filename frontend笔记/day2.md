# React 核心 Hooks + 表单绑定、事件处理

> 
> 基于 React 18+，只讲 `useState` / `useEffect` / `useRef`，配套表单与事件，带可直接运行示例

## 一、三大核心 Hooks

### 1. useState —— 状态管理（组件内响应式数据）

作用：**在函数组件创建状态变量，状态更新触发组件重渲染**

```
import { useState } from 'react'

function Counter() {
  // [当前状态, 更新状态函数] = useState(初始值)
  const [count, setCount] = useState(0)

  return (
    <div>
      <p>计数：{count}</p>
      {/* 事件：更新状态 */}
      <button onClick={() => setCount(count + 1)}>+1</button>
    </div>
  )
}
```

关键点：

1. `setCount` 是**异步批量更新**，连续调用不会立刻拿到最新值；
2. 如果新值依赖旧值，推荐函数写法：`setCount(prev => prev + 1)`
3. 状态是**不可变**，对象/数组不能直接修改，必须重新生成新引用。

### 2. useEffect —— 副作用处理（代替类组件生命周期）

副作用：网络请求、DOM操作、定时器、订阅、监听事件等。

```
import { useState, useEffect } from 'react'

function Demo() {
  const [count, setCount] = useState(0)

  useEffect(() => {
    // 执行副作用：组件挂载 + 依赖项变化时执行
    console.log('count更新：', count)

    // 清理函数：组件卸载 / 下次effect执行前执行
    return () => {
      console.log('清理')
    }
  }, [count]) // 依赖数组

  return <button onClick={() => setCount(c => c + 1)}>{count}</button>
}
```

依赖数组规则：

- `[]`：空依赖 → **仅挂载执行一次，卸载清理**（模拟 componentDidMount + willUnmount）
- `[a,b]`：依赖 a,b → a或b变化才执行
- 不写依赖数组：每次渲染都执行（慎用，容易死循环）

> 
> ❗ 坑：依赖项必须包含 effect 内部用到的 state / props，否则会拿到旧闭包值。

### 3. useRef —— 获取DOM、保存可变值（**不会触发重渲染**）

两种用途：

1. 获取真实 DOM 元素
2. 存一个可变容器，值改变**不引起组件刷新**（保存定时器id、上一次状态等）

```
import { useRef } from 'react'

function InputFocus() {
  // 创建ref对象
  const inputRef = useRef(null)

  const handleFocus = () => {
    // .current 访问DOM
    inputRef.current.focus()
  }

  return (
    <div>
      <input ref={inputRef} type="text" />
      <button onClick={handleFocus}>聚焦输入框</button>
    </div>
  )
}
```

> 
> 区分：`useState` 更新 → 重渲染；`useRef.current` 修改 → **不会重渲染**

---

## 二、React 事件处理

React事件是**合成事件（SyntheticEvent）**，封装原生事件，跨浏览器兼容。

### 基础写法

```
// 1. 无参数
<button onClick={handleClick}>点击</button>

// 2. 传参：箭头函数
<button onClick={() => handleClick('hello')}>传参</button>

function handleClick(e) {
  // e 是合成事件对象
  e.preventDefault() // 阻止默认行为，和原生event一样
  console.log(e.target)
}
```

要点：

- 事件名小驼峰：`onClick`、`onChange`、`onSubmit`（不是 onclick）
- 不要写 `onClick={handleClick()}`，会直接执行，要传函数引用
- 合成事件对象在事件回调结束后会被**池化复用**，异步里拿不到 e，要用 `e.persist()` 或者提前取值。

## 三、表单绑定（受控组件 vs 非受控组件）

### ✅ 受控组件（推荐，useState）

表单数据**由 React state 管理**，输入框的值绑定 state，`onChange` 更新状态。

> 
> 适合：实时校验、多字段联动、动态修改表单值

```
import { useState } from 'react'

function ControlledForm() {
  const [form, setForm] = useState({
    username: '',
    password: ''
  })

  // 通用onChange，一个函数处理多个输入框
  const handleChange = (e) => {
    const { name, value } = e.target
    setForm(prev => ({
      ...prev,
      [name]: value
    }))
  }

  const handleSubmit = (e) => {
    e.preventDefault() // 阻止表单默认提交刷新页面
    console.log('表单数据：', form)
  }

  return (
    <form onSubmit={handleSubmit}>
      <input
        name="username"
        value={form.username}
        onChange={handleChange}
        placeholder="用户名"
      />
      <input
        name="password"
        type="password"
        value={form.password}
        onChange={handleChange}
        placeholder="密码"
      />
      <button type="submit">提交</button>
    </form>
  )
}
```

### ✅ 非受控组件（useRef）

表单数据交给 DOM 自身管理，React 只在提交时通过 ref 获取 DOM 值。

> 
> 适合：简单一次性表单，不需要实时校验

```
import { useRef } from 'react'

function UnControlledForm() {
  const usernameRef = useRef(null)
  const pwdRef = useRef(null)

  const handleSubmit = (e) => {
    e.preventDefault()
    const username = usernameRef.current.value
    const password = pwdRef.current.value
    console.log({ username, password })
  }

  return (
    <form onSubmit={handleSubmit}>
      <input ref={usernameRef} name="username" placeholder="用户名"/>
      <input ref={pwdRef} type="password" placeholder="密码"/>
      <button type="submit">提交</button>
    </form>
  )
}
```

> 
> 对比一句话：
> 
> 
> - **受控组件：state 是数据源**，实时同步；
> - **非受控组件：DOM 是数据源**，提交才读取。

## 四、综合小案例（三合一 Hooks + 表单）

需求：输入用户名，输入框获得焦点，输入变化实时打印，挂载时自动聚焦

```
import { useState, useEffect, useRef } from 'react'

function FormDemo() {
  const [name, setName] = useState('')
  const inputRef = useRef(null)

  // 挂载时自动聚焦输入框
  useEffect(() => {
    inputRef.current.focus()
  }, [])

  const handleChange = (e) => {
    setName(e.target.value)
  }

  return (
    <div>
      <input
        ref={inputRef}
        value={name}
        onChange={handleChange}
        placeholder="请输入名字"
      />
      <p>你输入：{name}</p>
    </div>
  )
}
export default FormDemo
```

## 五、高频面试简答总结

1. **useState**：函数组件状态，更新触发重渲染；更新是异步批量更新。
2. **useEffect**：处理副作用，依赖数组控制执行时机；返回清理函数。
3. **useRef**：访问DOM，保存可变值；修改current不会触发重渲染。
4. **受控组件**：value绑定state + onChange更新，React管理表单数据。
5. **非受控组件**：useRef获取DOM值，DOM管理表单数据。
6. React事件是合成事件，小驼峰命名，`e.preventDefault()`阻止默认行为。

如果你需要，我可以：

- 整理成**面试背诵精简版**；
- 或者出一套练习题（含答案）巩固这部分知识点。