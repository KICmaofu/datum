# React：组件通信 + 条件渲染 + 列表渲染

## 一、组件通信

### 1. 父 → 子：props

父组件传数据/函数给子组件，子组件只读 props，不可直接修改。

```
// 父组件
function Parent() {
  const msg = "来自父组件";
  return <Child text={msg} />;
}
// 子组件接收
function Child({ text }) {
  return <div>{text}</div>;
}
```

> 
> 要点：props 单向数据流；可以传递函数、状态、组件。

### 2. 子 → 父：回调函数

父传回调给子，子调用回调，把数据作为参数传回父。

```
function Parent() {
  const handleSend = (val) => {
    console.log("子传给父：", val);
  };
  return <Child onSend={handleSend} />;
}

function Child({ onSend }) {
  return <button onClick={() => onSend("子组件消息")}>发送</button>;
}
```

### 3. 兄弟组件通信

方案：**状态提升**，把共享状态放到共同父组件，通过 props + 回调中转。

### 4. 跨多层组件通信

- `Context`：适合全局/多层透传（主题、用户信息），不要滥用，会造成组件不必要重渲染
- 状态管理库：Redux、Zustand、Jotai（大型项目全局状态）

### 5. 组件实例通信（类组件为主，函数组件少用）

ref 获取子组件实例；函数组件需要 `useImperativeHandle` 暴露方法。

---

## 二、条件渲染

几种常用写法

1. **if-else**（适合大块逻辑）

```
function Demo() {
  const isLogin = true;
  if (isLogin) {
    return <div>欢迎回来</div>;
  } else {
    return <button>登录</button>;
  }
}
```

2. **三元表达式**（行内渲染，最常用）

```
return <div>{isLogin ? "已登录" : "请登录"}</div>;
```

3. **&& 短路运算**：条件为 true 才渲染，false 时渲染 nothing> 
> ⚠️ 坑：`{count && <Comp/>}`，count=0 会渲染出 0！布尔判断要写成 `{count > 0 && <Comp/>}`

```
return <div>{show && <Alert>提示</Alert>}</div>;
```

4. 元素变量：把JSX存变量，按需赋值

```
let content;
if (show) content = <div>内容</div>;
return <>{content}</>;
```

---

## 三、列表渲染

核心：`array.map()`，**必须加 key**

```
const list = [{id:1,name:"A"},{id:2,name:"B"}];

function ListDemo() {
  return (
    <ul>
      {list.map(item => (
        <li key={item.id}>{item.name}</li>
      ))}
    </ul>
  )
}
```

### key 要点

1. key 推荐用业务唯一id，**不要用 index 做 key**（列表增删排序会出现渲染错乱、状态错位）
2. key 只在同级列表中唯一，不需要全局唯一
3. key 不会传递给组件，是 React 内部 diff 使用

### 列表 + 条件渲染组合示例

```
function List() {
  const arr = [];
  return (
    <>
      {arr.length > 0 ? (
        arr.map(item => <div key={item.id}>{item.title}</div>)
      ) : (
        <div>暂无数据</div>
      )}
    </>
  )
}
```

---

## 面试简答版（背诵）

1. **组件通信**

- 父传子：props，单向数据流；
- 子传父：父传入回调函数，子调用回调传参；
- 兄弟：状态提升到共同父组件；
- 跨层级：Context API / 状态管理库。

2. **条件渲染**：if else、三元、&&短路、JSX变量；注意&&遇到数字0的渲染陷阱。
3. **列表渲染**：使用 map，必须提供key；优先使用数据唯一id，避免index作为key导致diff错误。

要不要我顺便出几道小题帮你巩固这几个React知识点？