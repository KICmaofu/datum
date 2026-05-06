在Python中，**推导式（Comprehension）** 是一种简洁、高效的语法，用于从可迭代对象（如列表、字符串、`range`等）创建新的序列或集合（如列表、字典、集合）。推导式能将传统的循环+条件判断的代码简化为一行，既提高了代码简洁度，又保持了可读性（在逻辑简单时）。


Python主要支持4种推导式：**列表推导式**、**字典推导式**、**集合推导式**、**生成器推导式**（也叫元组推导式，但结果是生成器对象）。


### 一、列表推导式（List Comprehension）
列表推导式用于快速创建新列表，是最常用的推导式。

#### 1. 基本语法
```python
[表达式 for 变量 in 可迭代对象]
```
- 作用：遍历“可迭代对象”中的每个“变量”，对变量执行“表达式”计算，将结果收集为新列表。


#### 2. 带条件的列表推导式
可添加`if`条件筛选元素，只对符合条件的变量执行表达式：
```python
[表达式 for 变量 in 可迭代对象 if 条件]
```


#### 3. 示例
```python
# 示例1：生成1-5的平方列表（基本用法）
squares = [x**2 for x in range(1, 6)]
print(squares)  # [1, 4, 9, 16, 5]

# 示例2：筛选1-20中的偶数（带条件）
evens = [x for x in range(1, 21) if x % 2 == 0]
print(evens)  # [2, 4, 6, 8, 10, 12, 14, 16, 18, 20]

# 示例3：处理字符串列表（转为大写）
words = ["apple", "banana", "cat"]
upper_words = [word.upper() for word in words]
print(upper_words)  # ['APPLE', 'BANANA', 'CAT']

# 示例4：嵌套循环（生成二维列表的元素）
# 传统循环：生成[(1,1), (1,2), (2,1), (2,2)]
pairs = []
for i in range(1, 3):
    for j in range(1, 3):
        pairs.append((i, j))
# 列表推导式简化：
pairs = [(i, j) for i in range(1, 3) for j in range(1, 3)]
print(pairs)  # [(1, 1), (1, 2), (2, 1), (2, 2)]
```


### 二、字典推导式（Dictionary Comprehension）
字典推导式用于快速创建新字典，核心是生成“键值对”。

#### 1. 基本语法
```python
{键表达式: 值表达式 for 变量 in 可迭代对象}
```
- 作用：遍历“可迭代对象”中的每个“变量”，分别计算“键表达式”和“值表达式”，组成键值对，收集为新字典。


#### 2. 带条件的字典推导式
```python
{键表达式: 值表达式 for 变量 in 可迭代对象 if 条件}
```


#### 3. 示例
```python
# 示例1：生成键为1-5，值为键的平方的字典
square_dict = {x: x**2 for x in range(1, 6)}
print(square_dict)  # {1: 1, 2: 4, 3: 9, 4: 16, 5: 25}

# 示例2：筛选值为偶数的键值对
nums = {"a": 1, "b": 2, "c": 3, "d": 4}
even_dict = {k: v for k, v in nums.items() if v % 2 == 0}
print(even_dict)  # {'b': 2, 'd': 4}

# 示例3：交换字典的键和值
original = {"name": "Alice", "age": 18}
swapped = {v: k for k, v in original.items()}
print(swapped)  # {'Alice': 'name', 18: 'age'}
```


### 三、集合推导式（Set Comprehension）
集合推导式用于快速创建新集合，特性与集合一致（自动去重、无序）。

#### 1. 基本语法
```python
{表达式 for 变量 in 可迭代对象}
```
- 作用：遍历“可迭代对象”中的每个“变量”，对变量执行“表达式”计算，结果去重后组成新集合。


#### 2. 带条件的集合推导式
```python
{表达式 for 变量 in 可迭代对象 if 条件}
```


#### 3. 示例
```python
# 示例1：生成1-5的平方集合（自动去重，此处无重复）
square_set = {x**2 for x in range(1, 6)}
print(square_set)  # {1, 4, 9, 16, 25}（顺序不定）

# 示例2：字符串去重（提取不重复字符）
chars = {c for c in "hello world"}
print(chars)  # {'h', 'e', 'l', 'o', ' ', 'w', 'r', 'd'}（'l'重复，仅保留一个）

# 示例3：筛选偶数的平方
even_squares = {x**2 for x in range(1, 11) if x % 2 == 0}
print(even_squares)  # {4, 16, 36, 64, 100}
```


### 四、生成器推导式（Generator Comprehension）
生成器推导式的语法与列表推导式类似，但用**圆括号 `()`** 表示，返回的是一个**生成器对象**（而非列表）。  
生成器是一种惰性迭代器，不会一次性生成所有元素，而是按需生成，节省内存（适合处理大量数据）。

#### 1. 基本语法
```python
(表达式 for 变量 in 可迭代对象)  # 返回生成器对象
```


#### 2. 示例
```python
# 生成器推导式：生成1-5的平方
gen = (x**2 for x in range(1, 6))
print(gen)  # <generator object <genexpr> at 0x...>（生成器对象）

# 遍历生成器（每次调用next()或用for循环获取元素）
print(next(gen))  # 1
print(next(gen))  # 4
for num in gen:
    print(num)  # 9、16、25（剩余元素）
```

**注意**：生成器只能遍历一次，遍历结束后再访问会返回空。


### 五、推导式的优势与注意事项
#### 1. 优势
- **简洁高效**：用一行代码替代多行循环+条件的代码，且执行效率通常高于传统循环（Python内部优化）。  
- **可读性**：逻辑简单时，推导式比循环更易理解（一眼看出“从什么生成什么”）。  


#### 2. 注意事项
- **逻辑复杂度**：若条件或表达式过于复杂（如多层嵌套、多条件），推导式会变得晦涩，此时建议用传统循环（可读性优先）。  
  ```python
  # 不推荐：逻辑复杂的推导式（难以理解）
  complex_list = [x for x in range(100) if x % 2 == 0 and x % 3 == 0 and x > 50]
  # 推荐：用循环+条件，逻辑更清晰
  complex_list = []
  for x in range(100):
      if x % 2 == 0 and x % 3 == 0 and x > 50:
          complex_list.append(x)
  ```

- **嵌套层数**：最多建议嵌套2层循环，多层嵌套（如3层及以上）的推导式可读性极差。  


### 总结
推导式是Python的特色语法，通过简洁的格式快速创建列表、字典、集合或生成器：  
- 列表推导式：`[表达式 for 变量 in 可迭代对象 if 条件]` → 生成列表；  
- 字典推导式：`{k: v for 变量 in 可迭代对象 if 条件}` → 生成字典；  
- 集合推导式：`{表达式 for 变量 in 可迭代对象 if 条件}` → 生成集合（去重）；  
- 生成器推导式：`(表达式 for 变量 in 可迭代对象)` → 生成生成器（惰性迭代）。  

合理使用推导式能提升代码效率和简洁度，但需避免过度复杂导致可读性下降。