在Python中，**循环语句**用于重复执行一段代码块，主要有两种类型：`while` 循环和 `for` 循环。循环能大幅简化重复操作（如遍历序列、重复计算等），是程序中处理批量数据的核心工具。


### 一、`while` 循环
`while` 循环根据**条件的真假**决定是否重复执行代码块：当条件为 `True` 时，执行循环体；当条件为 `False` 时，退出循环。


#### 1. 基本语法
```python
while 条件表达式:
    循环体（条件为True时重复执行）
    [更新条件的语句]  # 避免无限循环
```


#### 2. 示例：基本用法
**场景**：从1数到5（循环5次）  
```python
count = 1  # 初始化计数器
while count <= 5:  # 条件：count小于等于5
    print(count)
    count += 1  # 更新计数器（每次+1，避免无限循环）
# 输出：
# 1
# 2
# 3
# 4
# 5
```


#### 3. 注意：避免无限循环
若条件始终为 `True`，`while` 循环会无限执行（卡死程序），需确保循环中**有更新条件的语句**。  
```python
# 错误示例：无限循环（条件永远为True）
# count = 1
# while count <=5:
#     print(count)  # 忘记更新count，count始终为1，循环永不结束
```


#### 4. 示例：结合用户输入的循环
**场景**：反复要求用户输入，直到输入"quit"为止  
```python
while True:  # 条件恒为True（无限循环框架）
    user_input = input("请输入内容（输入'quit'退出）：")
    if user_input == "quit":
        break  # 输入"quit"时，用break跳出循环
    print(f"你输入了：{user_input}")
```


### 二、`for` 循环
`for` 循环用于**遍历可迭代对象**（如列表、字符串、元组、字典、`range` 对象等），即依次取出对象中的每个元素并执行循环体。  
可迭代对象：指可以被 `for` 循环遍历的对象（如序列、集合、生成器等）。


#### 1. 基本语法
```python
for 变量 in 可迭代对象:
    循环体（变量依次取可迭代对象中的每个元素）
```


#### 2. 示例：遍历常见可迭代对象
- **遍历列表**：  
  ```python
  fruits = ["apple", "banana", "orange"]
  for fruit in fruits:  # fruit依次取列表中的每个元素
      print(f"I like {fruit}")
  # 输出：
  # I like apple
  # I like banana
  # I like orange
  ```

- **遍历字符串**（每个字符为元素）：  
  ```python
  s = "hello"
  for char in s:
      print(char)
  # 输出：
  # h
  # e
  # l
  # l
  # o
  ```

- **遍历字典**（默认遍历键，可通过 `keys()`/`values()`/`items()` 遍历键/值/键值对）：  
  ```python
  person = {"name": "Alice", "age": 18}
  # 遍历键（默认）
  for key in person:
      print(key)  # name、age

  # 遍历键值对
  for key, value in person.items():
      print(f"{key}: {value}")  # name: Alice、age: 18
  ```


#### 3. `range()` 函数：生成数字序列
`for` 循环常与 `range()` 配合生成数字序列，控制循环次数。  
`range()` 语法：`range(start, stop, step)`  
- `start`：起始值（可选，默认0）；  
- `stop`：结束值（必填，不包含该值）；  
- `step`：步长（可选，默认1，不能为0）。  


**示例**：  
```python
# range(5) → 0,1,2,3,4（默认start=0，step=1）
for i in range(5):
    print(i)  # 0、1、2、3、4

# range(1, 6) → 1,2,3,4,5（start=1，stop=6）
for i in range(1, 6):
    print(i)  # 1、2、3、4、5

# range(0, 10, 2) → 0,2,4,6,8（步长为2，间隔1个数字）
for i in range(0, 10, 2):
    print(i)  # 0、2、4、6、8

# 倒序：range(5, 0, -1) → 5,4,3,2,1（步长为-1）
for i in range(5, 0, -1):
    print(i)  # 5、4、3、2、1
```


### 三、循环控制语句
循环控制语句用于改变循环的执行流程，主要有 `break` 和 `continue`。


#### 1. `break`：跳出整个循环
当 `break` 被执行时，立即终止当前循环，不再执行后续循环体和剩余迭代。  

**示例**：找到列表中的"banana"后停止遍历  
```python
fruits = ["apple", "banana", "orange", "grape"]
for fruit in fruits:
    if fruit == "banana":
        print("找到banana，停止遍历")
        break  # 跳出循环
    print(f"当前水果：{fruit}")
# 输出：
# 当前水果：apple
# 找到banana，停止遍历
```


#### 2. `continue`：跳过当前循环的剩余部分
当 `continue` 被执行时，跳过当前循环中 `continue` 之后的代码，直接进入下一次循环。  

**示例**：遍历1-10，只打印奇数（跳过偶数）  
```python
for i in range(1, 11):
    if i % 2 == 0:  # 若为偶数
        continue  # 跳过后续打印，进入下一次循环
    print(i)  # 只打印奇数
# 输出：1、3、5、7、9
```


### 四、循环嵌套
循环内部可以再包含循环（嵌套循环），用于处理多维数据或复杂重复逻辑（如打印矩阵、九九乘法表等）。


#### 示例：打印5x5的正方形星号图案
```python
# 外层循环控制行数（5行）
for i in range(5):
    # 内层循环控制每行的星号数（5个）
    for j in range(5):
        print("*", end="")  # end=""表示不换行
    print()  # 每行结束后换行
# 输出：
# *****
# *****
# *****
# *****
# *****
```


#### 示例：九九乘法表
```python
# 外层循环控制乘数（1-9）
for i in range(1, 10):
    # 内层循环控制被乘数（1-i）
    for j in range(1, i+1):
        print(f"{j}×{i}={i*j}", end="\t")  # \t制表符对齐
    print()  # 每行结束后换行
```


### 五、循环的 `else` 子句（Python特色）
Python的循环可以搭配 `else` 子句，`else` 中的代码块在**循环正常结束**（即未被 `break` 中断）时执行。


#### 示例：判断一个数是否为质数（只能被1和自身整除的数）
```python
num = 7
for i in range(2, num):  # 检查2到num-1是否能整除num
    if num % i == 0:  # 若能整除，说明不是质数
        print(f"{num}不是质数")
        break
else:  # 循环正常结束（未被break）→ 所有i都不能整除num
    print(f"{num}是质数")
# 输出：7是质数
```


### 六、`while` 与 `for` 的适用场景
| 循环类型 | 核心特点                          | 适用场景                     |
|----------|-----------------------------------|------------------------------|
| `while`  | 基于条件判断，循环次数不确定      | 未知循环次数（如等待用户输入） |
| `for`    | 遍历可迭代对象，循环次数已知      | 已知循环次数（如遍历列表、固定次数循环） |


### 七、常见错误与注意事项
1. **缩进错误**：循环体必须缩进（通常4个空格），否则会报错或逻辑错误。  
   ```python
   # 错误示例：循环体未缩进
   for i in range(3):
   print(i)  # 未缩进，报错：IndentationError
   ```

2. `range()` 的终止值不包含自身：`range(1,5)` 生成 `1,2,3,4`，而非 `1-5`。  

3. 嵌套循环的效率：过多层嵌套（如3层以上）会降低程序效率，需尽量优化。  

4. 避免在循环中修改可迭代对象：遍历列表时，若添加/删除元素可能导致漏遍历或重复遍历。  
   ```python
   # 危险示例：遍历中删除元素导致漏项
   lst = [1, 2, 3, 4]
   for x in lst:
       if x % 2 == 0:
           lst.remove(x)  # 删除2后，列表变为[1,3,4]，下一次会遍历3，跳过4
   print(lst)  # [1, 3]（预期可能是[1,3]，但逻辑易出错）
   ```


### 总结
循环是Python处理重复操作的核心语法：  
- `while` 循环基于条件判断，适合未知循环次数的场景；  
- `for` 循环用于遍历可迭代对象，配合 `range()` 可控制循环次数，适合已知次数的场景；  
- `break` 跳出整个循环，`continue` 跳过当前循环剩余部分；  
- 嵌套循环处理多维逻辑，`else` 子句在循环正常结束时执行。  

掌握循环能大幅提升处理批量数据的效率，是编写实用程序的基础。