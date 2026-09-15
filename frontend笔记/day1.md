# React 核心基础：JSX、函数组件、Props、State

> 
> 目标：掌握 React 最核心的4块知识，理解单向数据流，区分 Props 和 State，可直接上手写简单组件。

## 一、JSX

JSX 是 JavaScript 的语法糖，**不是 HTML**，最终会被编译成 `React.createElement`。

### 核心规则

1. 只能有**一个根节点**（可以用 `<>` 空 fragment，不渲染 DOM）
2. 类名用 `className`，不是 `class`；`for` 写成 `htmlFor`
3. 内联样式是**对象**，属性用小驼峰：`style={{ color: 'red', fontSize: '20px' }}`
4. JS 表达式用 `{ }` 包裹，内部只能写表达式，不能写 if/for（可用三元、map）
5. 注释写法：`{/* 注释内容 */}`

```
import React from 'react'

function DemoJSX() {
  const name = "小明"
  const flag = true
  const list = ['苹果','香蕉']

  return (
    <>
      <h1 className="title">Hello {name}</h1>
      <p style={{color:'blue'}}>{ flag ? '显示' : '隐藏' }</p>
      <ul>
        {list.map(item => <li key={item}>{item}</li>)}
      </ul>
    </>
  )
}
export default DemoJSX
```

> 
> 重点：`{}` 里面放 JS 表达式；`key` 在 map 渲染列表时必须加，用来标记节点，提升 diff 性能，不要用 index 当 key（有坑）

## 二、函数组件

函数组件就是**返回 JSX 的普通 JS 函数**。
✅ 特点：

- 函数名大写开头（React 约定，区分原生 HTML 标签）
- 入参接收 props 对象
- 没有 `this`，简洁；配合 Hooks 拥有状态和副作用能力
- 是现在 React 官方推荐写法（替代 Class 类组件）

```
// 函数组件基础
function Hello() {
  return <h2>Hello React</h2>
}

// 使用组件
function App() {
  return (
    <div>
      <Hello />
    </div>
  )
}
export default App
```

## 三、Props（属性）

Props 是**父组件传递给子组件的数据**，**单向数据流：父 → 子**。
✅ 核心特性：

1. **只读**：子组件不能修改 props，只能读取
2. 可以传字符串、数字、布尔、对象、数组、函数
3. 可以解构简化写法；支持默认值
4. 传递函数 props：实现子组件向父组件通信（回调）

```
// 子组件：接收 props
function Card(props) {
  // 解构写法：function Card({ title, count })
  console.log(props)
  return (
    <div>
      <h3>{props.title}</h3>
      <p>{props.count}</p>
    </div>
  )
}
// props 默认值
Card.defaultProps = {
  count: 0
}

// 父组件：传 props
function App() {
  return (
    <div>
      {/* 字符串直接写，JS表达式用{} */}
      <Card title="卡片标题" count={100} />
    </div>
  )
}
```

> 
> 易错点：props 只读，子组件写 `props.title = 'xxx'` 会报错！

### 子传父（props传回调函数）

```
function Child({ onSend }) {
  const msg = "来自子组件消息"
  return <button onClick={()=>onSend(msg)}>发送消息给父</button>
}

function Parent() {
  const handleReceive = (val) => {
    console.log("父收到：", val)
  }
  return <Child onSend={handleReceive} />
}
```

## 四、State（状态）

状态是**组件内部自己维护的数据**，状态改变 → 组件自动重新渲染。
函数组件使用 `useState` Hook 创建状态。

✅ 核心要点：

1. `useState` 返回：`[状态变量, 更新函数]`
2. **不能直接修改 state**，必须调用 set函数：`setXXX(newVal)`
3. state 更新是**异步**，连续多次 set 会合并
4. state 更新会触发组件重渲染

```
import { useState } from 'react'

function Counter() {
  // 定义状态：初始值0
  const [count, setCount] = useState(0)

  const add = () => {
    // 更新状态，不要写 count++
    setCount(count + 1)
  }

  return (
    <div>
      <p>计数：{count}</p>
      <button onClick={add}>+1</button>
    </div>
  )
}
export default Counter
```

### 对象类型 state 更新（必须传新对象，不要原地修改）

```
function UserDemo() {
  const [user, setUser] = useState({name:"张三", age:18})

  const changeAge = () => {
    // ✅ 正确：展开旧对象，生成新对象
    setUser({...user, age: user.age + 1})
    // ❌ 错误：user.age++ 原地修改，不会触发渲染
  }
  return <div>{user.name} - {user.age}</div>
}
```

## 五、Props vs State 对比

|  | Props | State |
| --- | --- | --- |
| 来源 | 父组件传入 | 组件内部自己定义 |
| 是否可修改 | 只读，子组件不能改 | 可以通过 set函数更新 |
| 作用 | 组件外部传入数据 | 保存组件内部可变状态 |
| 更新后 | 父组件更新 props，子组件重渲染 | setState触发当前组件重渲染 |

## 六、综合完整示例（整合 JSX + 函数组件 + Props + State）

```
import { useState } from 'react'

// 子组件：接收 props
function GoodItem({ name, price }) {
  return (
    <div className="good">
      <p>商品：{name}</p>
      <p>价格：{price}</p>
    </div>
  )
}

// 父组件：拥有state
function Shop() {
  const [goodsList, setGoodsList] = useState([
    {name:'手机', price:2999},
    {name:'耳机', price:299}
  ])

  return (
    <>
      <h2>商品列表</h2>
      { goodsList.map((item, idx)=>
          <GoodItem key={idx} name={item.name} price={item.price}/>
        )
      }
    </>
  )
}

export default Shop
```

## 七、常见面试考点

1. JSX 和 HTML 的区别？className、htmlFor、单根节点、表达式 `{}`
2. 函数组件和类组件区别，现在推荐函数组件+Hooks
3. Props 为什么只读？单向数据流思想，方便调试追踪数据来源
4. useState 更新为什么是异步？批量更新优化渲染性能
5. state 修改为什么不能直接赋值？React 无法感知原地修改，不会触发重渲染

如果你需要，我可以继续拓展：事件绑定、useEffect、组件生命周期、受控组件。
这个知识点可以用来写前端页面组件，工作任务模式可以帮你生成可预览的React页面，要不要用它继续？