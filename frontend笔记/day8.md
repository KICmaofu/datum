# TypeScript 进阶：泛型、接口、类型断言与类型封装

> 
> 基于 TypeScript 5.x，全程结合 React + Antd + Axios 业务场景，与前文技术栈完全衔接，兼顾语法原理与工程实战。

---

## 一、接口（Interface）

接口是 TypeScript 最核心的特性之一，用于**定义对象的形状（结构契约）**，对对象、函数、类进行类型约束，实现契约式编程。

### 1. 基础定义

```
// 定义用户对象的结构
interface UserInfo {
  id: number
  username: string
  email: string
  avatar?: string // 可选属性
}

// 使用：变量必须严格符合结构
const user: UserInfo = {
  id: 1,
  username: 'admin',
  email: 'admin@example.com'
}
```

### 2. 进阶属性

```
interface UserInfo {
  readonly id: number       // 只读属性，初始化后不可修改
  username: string
  email: string
  [key: string]: any        // 索引签名：允许任意额外字符串属性
}

// 接口继承：扩展已有接口
interface AdminUser extends UserInfo {
  role: string
  permissions: string[]
}
```

### 3. 函数类型接口

定义函数的参数和返回值形状：

```
interface ApiRequest {
  (url: string, params?: object): Promise<any>
}

const get: ApiRequest = (url, params) => {
  return axios.get(url, { params })
}
```

### 4. interface vs type 核心区别与选型

| 特性 | interface | type |
| --- | --- | --- |
| 定义对象 | ✅ 首选 | ✅ 可以 |
| 联合类型/交叉类型 | ❌ | ✅ 支持 |
| 继承扩展 | extends 关键字 | & 交叉类型 |
| 声明合并 | ✅ 同名接口自动合并 | ❌ 同名会报错 |
| 映射类型、条件类型 | ❌ | ✅ 支持 |

**选型原则**：

- 定义对象结构、类契约优先用 `interface`，可扩展性好
- 定义联合类型、工具类型、元组用 `type`
- 业务领域模型（用户、商品等）推荐 interface

---

## 二、泛型（Generics）—— TS 进阶核心

### 1. 本质：类型的参数化

泛型解决**类型复用 + 类型安全**的矛盾。不使用泛型时只能用 `any` 放弃类型检查；泛型把类型作为参数传入，既灵活又保留类型推导。

**对比示例**：

```
// 不好：any 丢失所有类型安全
function identity(arg: any): any {
  return arg
}

// 好：泛型，传入什么类型返回什么类型
function identity<T>(arg: T): T {
  return arg
}

// 使用
const num = identity<number>(10)  // 显式指定类型
const str = identity('hello')     // 自动类型推导
```

### 2. 泛型接口

```
// 统一 API 响应结构（结合之前 Axios 封装）
interface ApiResponse<T = any> {
  code: number
  msg: string
  data: T  // 业务数据泛型，由调用方传入
}

// 使用：指定 data 的具体类型
const res: ApiResponse<UserInfo> = {
  code: 200,
  msg: 'success',
  data: { id: 1, username: 'admin', email: 'a@b.com' }
}
```

### 3. 泛型约束（extends）

限制泛型必须符合某些结构，避免任意类型导致的属性访问错误。

```
interface HasLength {
  length: number
}

// 约束 T 必须拥有 length 属性
function getLength<T extends HasLength>(arg: T): number {
  return arg.length
}

getLength('hello') // ✅ 字符串有 length
getLength([1,2,3]) // ✅ 数组有 length
getLength(123)     // ❌ 数字没有 length，编译报错
```

### 4. React 全场景泛型实战

#### （1）useState 泛型

状态初始值为 null/空数组时，显式指定状态类型：

```
const [user, setUser] = useState<UserInfo | null>(null)
const [list, setList] = useState<UserInfo[]>([])
```

#### （2）useRef 泛型

获取 DOM 时指定元素类型，获得完整的 DOM 类型提示：

```
const inputRef = useRef<HTMLInputElement>(null)
const timerRef = useRef<number | null>(null)
```

#### （3）Axios 封装类型化（重点）

改造之前的 Axios 封装，让请求返回强类型数据：

```
// src/utils/request.ts
import axios from 'axios'
import type { AxiosRequestConfig } from 'axios'

const service = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  timeout: 10000
})

// 封装 get 方法，传入数据类型返回对应 Promise
export const get = <T = any>(url: string, params?: object): Promise<T> => {
  return service.get(url, { params }).then(res => res.data)
}

export const post = <T = any>(url: string, data?: object): Promise<T> => {
  return service.post(url, data).then(res => res.data)
}
```

业务 API 层使用：

```
// src/api/user.ts
import { get, post } from '@/utils/request'

interface LoginParams {
  username: string
  password: string
}

interface LoginResult {
  token: string
}

// 传入参数类型和返回类型
export const loginApi = (data: LoginParams) => post<LoginResult>('/user/login', data)
export const getUserInfoApi = () => get<UserInfo>('/user/info')
```

#### （4）Zustand Store 类型化

```
// src/store/userStore.ts
import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface UserState {
  token: string
  userInfo: UserInfo | null
  isLogin: boolean
  login: (form: LoginParams) => Promise<void>
  logout: () => void
}

const useUserStore = create<UserState>()(
  persist(
    (set, get) => ({
      token: '',
      userInfo: null,
      isLogin: false,
      login: async (form) => {
        const res = await loginApi(form)
        set({ token: res.token, isLogin: true })
      },
      logout: () => set({ token: '', userInfo: null, isLogin: false })
    }),
    { name: 'user-store' }
  )
)
```

### 5. 进阶：条件类型与 infer

根据条件返回不同类型，是高级类型工具的基础：

```
// 如果 T 是数组，返回数组元素类型；否则返回 T 本身
type Unpack<T> = T extends (infer U)[] ? U : T

type A = Unpack<string[]> // string
type B = Unpack<number>   // number
```

---

## 三、类型断言

类型断言用于**手动指定值的类型**，告诉编译器「我比你更清楚这个值的类型」，只在编译时生效，运行时不做任何校验。

### 1. 两种语法

```
// 1. as 语法（推荐，JSX 中唯一可用）
const input = document.getElementById('input') as HTMLInputElement

// 2. 尖括号语法（JSX 中不可用，会与标签冲突）
const input = <HTMLInputElement>document.getElementById('input')
```

### 2. 非空断言运算符 `!`

断言某个值**一定不是 null / undefined**：

```
const inputRef = useRef<HTMLInputElement>(null)

// 确定运行时一定有值，用 ! 跳过空检查
inputRef.current!.value = ''
```

### 3. 使用场景

1. **DOM 操作**：`getElementById` 返回 `HTMLElement | null`，断言为具体元素类型
2. **类型收窄**：你确定类型比 TS 推断的更精确
3. **第三方库类型不完善**：临时修正类型

### 4. 重要原则

- **能不用就不用**，优先使用类型守卫、泛型、联合类型收窄
- 断言不是类型转换，不会改变运行时的值，只是编译时的类型标注
- 严禁用 `as any` 逃避类型检查，等于放弃 TS 所有保护

### 5. 更安全的替代：类型守卫

运行时判断类型，自动收窄类型，比断言更安全：

```
// typeof 基础类型
function isString(val: unknown): val is string {
  return typeof val === 'string'
}

// in 判断对象属性
function isAdmin(user: UserInfo | AdminUser): user is AdminUser {
  return 'permissions' in user
}

// 使用：自动类型收窄
if (isAdmin(user)) {
  console.log(user.permissions) // 自动识别为 AdminUser
}
```

---

## 四、类型封装与工程化技巧

### 1. 内置工具类型（必掌握）

TS 内置了一批常用类型转换工具，基于泛型和条件类型实现。

| 工具类型 | 作用 | 示例 |
| --- | --- | --- |
| `Partial<T>` | 所有属性变为可选 | `Partial<UserInfo>` |
| `Required<T>` | 所有属性变为必填 | `Required<UserInfo>` |
| `Pick<T, K>` | 选取 T 中的 K 属性 | `Pick<UserInfo, 'id' |
| `Omit<T, K>` | 排除 T 中的 K 属性 | `Omit<UserInfo, 'email'>` |
| `Exclude<T, U>` | 从联合类型 T 排除 U | `Exclude<'a' |
| `Extract<T, U>` | 提取联合类型交集 | `Extract<'a' |
| `ReturnType<T>` | 获取函数返回值类型 | `ReturnType<typeof loginApi>` |
| `Parameters<T>` | 获取函数参数类型元组 | `Parameters<typeof loginApi>` |

**业务示例**：

```
// 更新用户表单：只需要用户名和邮箱，id 不可改
type UpdateUserForm = Pick<UserInfo, 'username' | 'email'>

// 搜索参数：所有属性可选
type UserSearchParams = Partial<Pick<UserInfo, 'username' | 'email'>>
```

### 2. 业务类型封装实战

#### （1）统一 API 响应类型

```
// 基础响应结构
interface BaseResp<T = any> {
  code: number
  msg: string
  data: T
}

// 分页响应
interface PageResp<T> {
  records: T[]
  total: number
  page: number
  pageSize: number
}

// 列表接口返回类型
type UserListResp = BaseResp<PageResp<UserInfo>>
```

#### （2）Antd Form 类型提取

结合 `Form.useForm` 获取表单值类型：

```
import { Form } from 'antd'

interface LoginForm {
  username: string
  password: string
}

export default function Login() {
  // 泛型指定表单字段类型，获得完整类型提示
  const [form] = Form.useForm<LoginForm>()

  const onFinish = (values: LoginForm) => {
    console.log(values.username) // 类型安全
  }

  return <Form form={form} onFinish={onFinish}>...</Form>
}
```

### 3. 类型声明文件

- `.d.ts` 文件：只包含类型声明，不包含运行时代码
- 全局类型声明：`src/types/index.d.ts`，定义全局通用类型
- 模块补充：给无类型的第三方库补充类型

```
// src/types/index.d.ts
declare interface UserInfo {
  id: number
  username: string
}

// 补充 import.meta.env 类型
interface ImportMetaEnv {
  readonly VITE_API_BASE_URL: string
}
```

---

## 五、面试核心总结

1. **接口**：定义对象结构契约，支持继承、声明合并；与 type 互补，对象模型优先用 interface
2. **泛型**：类型参数化，实现类型复用与安全；核心场景：API 响应、组件状态、工具函数
3. **类型断言**：手动指定类型，只在编译时生效；优先用类型守卫替代，避免滥用 `as any`
4. **类型封装**：熟练使用 `Pick/Omit/Partial/ReturnType` 等内置工具，按业务模块拆分类型文件

---

需要我结合之前的后台管理项目，输出一份**完整的 TypeScript 类型定义文件**（用户、权限、API 响应、表单），可以直接复用吗？