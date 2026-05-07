# 在Python中， ** 函数（Function） ** 是一段封装了特定功能的可重用代码块，通过函数名调用，可接收输入参数并返回处理结果。函数的核心作用是 ** 代码复用 **（避免重复编写相同逻辑）、 ** 模块化编程 **（将复杂问题拆解为小功能），以及提高代码的可读性和可维护性。
#
#
# ### 一、函数的基本定义与调用
# #### 1. 定义函数：`def` 关键字
# 函数通过
# `
#
#
# def ` 关键字定义
#
# ，基本语法如下：
# ```python
#

# def 函数名(参数列表):
#     """函数文档字符串（可选，用于说明函数功能）"""
#     函数体（实现功能的代码块）
#     [
#     return 返回值]  # 可选，返回处理结果
#     ```
#
#       - ** 函数名 **：遵循标识符规则（字母、数字、下划线，不能以数字开头），建议使用小写字母和下划线（如
#     `calculate_sum`）；
#     - ** 参数列表 **：可选，用于接收外部传入的数据（可无参数）；
#     - ** 文档字符串（docstring） ** ：可选，用三引号包裹，用于描述函数功能（通过
#     `help(函数名)`
#     可查看）；
#     - ** 函数体 **：缩进的代码块（通常4个空格），实现具体功能；
#     - ** return语句 **：可选，用于返回结果（若省略，函数默认返回
#     `None`）。
#
#
#     #### 2. 调用函数：函数名+括号
#     定义函数后，通过
#     `函数名(参数)`
#     调用，执行函数体并获取返回值。
#
#
#     #### 3. 示例：最简单的函数
#     ```python
#     # 定义无参数、无返回值的函数


def say_hello():
    """打印问候语"""
    print("Hello, Python!")


# 调用函数
say_hello()  # 输出：Hello, Python!
print(say_hello())  # 输出：Hello, Python!  None（函数无return，默认返回None）


# 定义有参数、有返回值的函数
def add(a, b):
    """计算两个数的和并返回"""
    return a + b


# 调用函数，接收返回值
result = add(3, 5)
print(result)  # 输出：8
# ```
#
# ### 二、函数的参数
# 函数参数用于接收外部输入，使函数更灵活（同一函数可处理不同数据）。Python的函数参数支持多种形式，按传递方式可分为：
#
#
# #### 1. 位置参数（Positional Arguments）
# 最基础的参数形式，调用时需按 ** 参数定义的顺序 ** 传递值，数量必须与定义一致。
#
# ```python


def greet(name, age):
    """向指定姓名和年龄的人问候"""
    print(f"Hello, {name}! You are {age} years old.")


# 按位置传递参数（name=Alice，age=18）
greet("Alice", 18)  # 输出：Hello, Alice! You are 18 years old.

# 错误：参数数量不符
# greet("Bob")  # 报错：TypeError（缺少age参数）
# ```
#
# #### 2. 关键字参数（Keyword Arguments）
# 调用函数时，通过
# `参数名 = 值
# ` 的形式传递参数， ** 无需严格按顺序 **（但建议保持可读性）。
#
# ```python
# 用关键字参数调用（顺序可换）
greet(age=20, name="Bob")  # 输出：Hello, Bob! You are 20 years old.

# 混合使用位置参数和关键字参数（位置参数必须在关键字参数前）
greet("Charlie", age=22)  # 正确：name是位置参数，age是关键字参数
# greet(name="Dave", 24)  # 错误：关键字参数不能在位置参数前
# ```
#
# #### 3. 默认参数（Default Arguments）
# 定义函数时，为参数指定默认值（`参数名 = 默认值
# `），调用时若不传递该参数，则使用默认值。
#
# ** 注意 **：默认参数必须放在 ** 位置参数之后 **（否则语法错误）。
#
# ```python


def greet(name, age=18):  # age有默认值18
    """向指定姓名的人问候，年龄默认18"""
    print(f"Hello, {name}! You are {age} years old.")


# 不传递age，使用默认值
greet("Eve")  # 输出：Hello, Eve! You are 18 years old.

# 传递age，覆盖默认值
greet("Frank", 25)  # 输出：Hello, Frank! You are 25 years old.
# ```
#
# #### 4. 不定长参数（可变参数）
# 当不确定参数数量时，可使用不定长参数接收任意数量的参数，分为两种：
# - `*args`：接收 ** 任意数量的位置参数 **，打包为一个元组（`tuple`）；
# - ` ** kwargs
# `：接收 ** 任意数量的关键字参数 **，打包为一个字典（`dict`）。
#
#
# ##### 示例：`*args` 接收位置参数
# ```python


def sum_numbers(*args):
    """计算任意数量数字的和（args是元组）"""
    print("参数列表：", args)  # 打印元组
    return sum(args)


# 传递3个位置参数
print(sum_numbers(1, 2, 3))  # 输出：参数列表：(1, 2, 3) → 6

# 传递1个参数
print(sum_numbers(10))  # 输出：参数列表：(10,) → 10

# 传递列表/元组（需在前面加*，解包为位置参数）
nums = [1, 2, 3, 4]
print(sum_numbers(*nums))  # 等价于 sum_numbers(1,2,3,4) → 10
# ```
#
# ##### 示例：`**kwargs` 接收关键字参数
# ```python


def print_info(**kwargs):
    """打印任意数量的关键字参数（kwargs是字典）"""
    print("关键字参数：", kwargs)  # 打印字典
    for key, value in kwargs.items():
        print(f"{key}: {value}")


# 传递2个关键字参数
print_info(name="Alice", age=18)
# 输出：
# 关键字参数： {'name': 'Alice', 'age': 18}
# name: Alice
# age: 18

# 传递字典（需在前面加**，解包为关键字参数）
info = {"city": "Beijing", "gender": "female"}
print_info(**info)  # 等价于 print_info(city="Beijing", gender="female")
# ```
#
# ##### 组合使用：位置参数 + `*args` + 默认参数 + `**kwargs`
# 参数定义顺序必须为： ** 位置参数 → `*args` → 默认参数 → ` ** kwargs
# ` **（否则语法错误）。
#
# ```python
#

def func(a, b, *args, c=0, **kwargs):
    print(f"a={a}, b={b}, args={args}, c={c}, kwargs={kwargs}")


func(1, 2, 3, 4, c=5, x=6, y=7)
# 输出：a=1, b=2, args=(3, 4), c=5, kwargs={'x': 6, 'y': 7}
# ```
#
# ### 三、函数的返回值（`return` 语句）
# `
# return ` 语句用于将函数的处理结果返回给调用者，执行到
# `
# return ` 时函数会立即结束（后续代码不再执行）。
#
#
# #### 1. 基本用法：返回单个值
# ```python


def square(x):
    return x ** 2  # 返回x的平方


print(square(5))  # 输出：25
# ```
#
# #### 2. 返回多个值（实际返回元组）
# 函数可通过
# `
# return 值1, 值2, ...
# ` 返回多个值，本质是返回一个元组，调用时可自动解包到多个变量。
#
# ```python


def get_name_and_age():
    return "Alice", 18  # 等价于 return ("Alice", 18)


# 调用：自动解包到两个变量
name, age = get_name_and_age()
print(name, age)  # 输出：Alice 18

# 也可接收为单个元组
result = get_name_and_age()
print(result)  # 输出：('Alice', 18)
# ```
#
# #### 3. 无 `return` 语句：默认返回 `None`
# ```python
#

def empty_func():
    pass  # 空语句，无任何操作


print(empty_func())  # 输出：None
# ```
#
# ### 四、函数的作用域（变量的可见范围）
# 函数内部定义的变量（ ** 局部变量 **）仅在函数内部可见；函数外部定义的变量（ ** 全局变量 **）在整个模块可见。
#
#
# #### 1. 局部变量 vs 全局变量
# ```python
# # 全局变量（函数外部定义）
global_var = "我是全局变量"


def my_func():
    # 局部变量（仅在函数内部可见）
    local_var = "我是局部变量"
    print(local_var)  # 正确：函数内可访问局部变量
    print(global_var)  # 正确：函数内可访问全局变量


my_func()
# 输出：
# 我是局部变量
# 我是全局变量

# 错误：函数外部无法访问局部变量
# print(local_var)  # 报错：NameError: name 'local_var' is not defined
# ```
#
# #### 2. `global` 关键字：在函数内修改全局变量
# 默认情况下，函数内不能直接修改全局变量（会被视为定义局部变量），需用
# `
# global
# ` 声明变量为全局变量。
#
# ```python
count = 0  # 全局变量


def increment():
    global count  # 声明count是全局变量
    count += 1  # 修改全局变量


increment()
print(count)  # 输出：1（全局变量被修改）
# ```
#
# #### 3. `nonlocal` 关键字：在嵌套函数中修改外层函数的变量
# 用于嵌套函数中，声明变量为外层函数的局部变量（非全局）。
#
# ```python


def outer():
    x = 10  # 外层函数的局部变量

    def inner():
        nonlocal x  # 声明x是外层函数的局部变量
        x += 5  # 修改外层变量

    inner()
    print(x)  # 输出：15（x被inner修改）


outer()
# ```
#
# ### 五、嵌套函数与闭包
# #### 1. 嵌套函数：函数内部定义另一个函数
# ```python


def outer_func():
    print("这是外层函数")

    def inner_func():  # 嵌套在outer_func内部
        print("这是内层函数")

    inner_func()  # 外层函数内调用内层函数


outer_func()
# 输出：
# 这是外层函数
# 这是内层函数

# 错误：外层函数外部无法调用内层函数
# inner_func()  # 报错：NameError
# ```
#
# #### 2. 闭包（Closure）：内层函数引用外层函数的变量，并被返回
# 闭包可“记住”外层函数的变量，即使外层函数已执行完毕。
#
# ```python


def make_greeter(prefix):
    def greeter(name):  # 内层函数引用外层变量prefix
        return f"{prefix}, {name}!"

    return greeter  # 返回内层函数


# 创建两个不同的greeter（记住不同的prefix）
hello_greeter = make_greeter("Hello")
hi_greeter = make_greeter("Hi")

print(hello_greeter("Alice"))  # 输出：Hello, Alice!
print(hi_greeter("Bob"))  # 输出：Hi, Bob!
# ```
#
# ### 六、匿名函数（`lambda` 表达式）
# `lambda ` 用于创建简单的 ** 匿名函数 ** （无函数名），语法简洁，适合定义单行逻辑的函数。
#
#         #### 1. 语法
#         ```python
#         lambda 参数列表: 表达式  # 自动返回表达式的结果
# ```
#
# - 无函数名，通过赋值给变量调用；
# - 只能包含一个表达式（不能有复杂逻辑，如循环、条件语句需简化为三元表达式）。
#
#
# #### 2. 示例
# ```python
# # 定义匿名函数（计算两数之和），赋值给变量add
add = lambda a, b: a + b
print(add(3, 5))  # 输出：8

# 作为参数传递（如排序时自定义key）
nums = [(1, 3), (2, 1), (3, 2)]
# 按元组的第二个元素排序
nums.sort(key=lambda x: x[1])
print(nums)  # 输出：[(2, 1), (3, 2), (1, 3)]
# ```
#
# ### 七、函数文档字符串（Docstring）
# 文档字符串是函数内用三引号包裹的说明文本，用于描述函数功能、参数、返回值等，可通过
# `help(函数名)`
# 或
# `函数名.__doc__`
# 查看。
#
# ```python
#

def calculate_area(radius):
    """
    计算圆的面积

    参数：
        radius: 圆的半径（正数）

    返回：
        float: 圆的面积（π * radius²）
    """
    import math
    return math.pi * radius ** 2


# 查看文档
help(calculate_area)
# 输出：
# Help on function calculate_area in module __main__:
# calculate_area(radius)
#     计算圆的面积
#
#     参数：
#         radius: 圆的半径（正数）
#
#     返回：
#         float: 圆的面积（π * radius²）
# ```
#
# ### 总结
# 函数是Python模块化编程的核心，通过
# `
#
#
# def ` 定义
#
# ，支持多种参数形式（位置参数、关键字参数、默认参数、不定长参数），可返回单个或多个值。函数的作用域控制变量的可见范围，`
# global
# ` 和 `
# nonlocal
# ` 关键字用于修改外层变量。嵌套函数和闭包可实现更灵活的逻辑封装，而
# `lambda ` 表达式适合定义简单匿名函数。掌握函数的使用是编写高效、可维护Python代码的基础。