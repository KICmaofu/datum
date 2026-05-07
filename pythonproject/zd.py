classes={'name':'25计算机','num':40,'dep':"dzx"}
com=dict(cn='py',cr=4,tr="li")
print(classes)
for k in com:
    print(k,com[k])
print("---------------")
for v in com:
    print(v,com[v])
print("--------------")
for k,v in classes.items():
    print(k,v)
print("-----------")
classes["classid"] = "5"
print(classes)
classes["dep"] = "电子信息工系"
print(classes)
del classes["num"]
print(classes)
print("-------")
# 在Python3中，**字典（Dictionary）** 是一种无序（Python3.7+ 开始保证插入顺序）、可变的键值对（`key-value`）集合，用于存储具有关联关系的数据（如“姓名-年龄”“ID-信息”等）。字典是Python中最灵活、最常用的数据结构之一，查找效率极高。
#
#
# ### 一、字典的定义
# 字典用**大括号 `{}`** 表示，每个元素是一个**键值对（`key: value`）**，键值对之间用逗号 `,` 分隔。
# - **键（key）**：必须是**可哈希的不可变类型**（如整数、字符串、元组等），且**唯一**（重复的键会被后面的覆盖）；
# - **值（value）**：可以是任意类型（整数、字符串、列表、字典等），且可重复。


#### 1. 基本定义方式
# ```python
# 空字典
empty_dict = {}
print(empty_dict, type(empty_dict))  # {} <class 'dict'>

# 包含键值对的字典
person = {
    "name": "Alice",  # 键"name"对应值"Alice"
    "age": 18,        # 键"age"对应值18
    "is_student": True,
    "hobbies": ["reading", "music"]  # 值可以是列表
}
print(person)  # {'name': 'Alice', 'age': 18, 'is_student': True, 'hobbies': ['reading', 'music']}

# 用dict()函数创建字典（通过键值对参数或可迭代对象）
dict1 = dict(name="Bob", age=20)  # 关键字参数
dict2 = dict([("name", "Charlie"), ("age", 22)])  # 键值对组成的列表
print(dict1)  # {'name': 'Bob', 'age': 20}
print(dict2)  # {'name': 'Charlie', 'age': 22}
# ```


#### 2. 字典的核心特性
# - **键值对关联**：通过“键”快速访问“值”（无需像列表那样通过索引）；
# - **键的唯一性**：同一字典中不能有重复的键，重复定义时后者会覆盖前者；
#   ```python
  # 重复键会被覆盖
d = {"a": 1, "a": 2}
print(d)  # {'a': 2}（仅保留最后一个键值对）
#   ```
# - **可变性**：可修改、添加、删除键值对（但键本身不可变）；
# - **Python3.7+ 有序性**：从Python3.7开始，字典会保留键值对的插入顺序（之前版本无序）。
#
#
# ### 二、字典的基本操作
# #### 1. 访问值（通过键）
# 通过 `字典名[键]` 访问对应的值，若键不存在则抛出 `KeyError`。
# 更安全的方式：用 `get(key, default)` 方法，键不存在时返回 `default`（默认 `None`）。
#
# ```python
person = {"name": "Alice", "age": 18}

# 直接访问（键存在）
print(person["name"])  # 'Alice'

# 直接访问（键不存在 → 报错）
# print(person["gender"])  # 报错：KeyError: 'gender'

# get()方法（键不存在返回默认值）
print(person.get("gender"))  # None（默认）
print(person.get("gender", "unknown"))  # 'unknown'（指定默认值）
# ```
#
#
# #### 2. 添加/修改键值对
# - 若键**已存在**：`字典名[键] = 新值` 会修改对应的值；
# - 若键**不存在**：`字典名[键] = 值` 会添加新的键值对。
#
# ```python
person = {"name": "Alice", "age": 18}

# 修改已有键的值
person["age"] = 19  # 键"age"已存在，修改为19
print(person)  # {'name': 'Alice', 'age': 19}

# 添加新键值对
person["gender"] = "female"  # 键"gender"不存在，添加
print(person)  # {'name': 'Alice', 'age': 19, 'gender': 'female'}
# ```


# #### 3. 删除键值对
# - `del 字典名[键]`：删除指定键~~的键值对（键不存在则报错）；
# - `pop(key, default)`：删除并返回指定键的值（键不存在时返回 `default`，否则报错）；
# - `clear()`：清空字典（删除所有~~键值对，保留空字典）。
#
# ```python
person = {"name": "Alice", "age": 18, "gender": "female"}

# del删除
del person["gender"]  # 删除键"gender"
print(person)  # {'name': 'Alice', 'age': 18}

# pop()删除并返回值
age = person.pop("age")
print(age)      # 18（返回删除的值）
print(person)   # {'name': 'Alice'}

# pop()处理不存在的键（指定默认值）
print(person.pop("height", 160))  # 160（键不存在，返回默认值）

# clear()清空
person.clear()
print(person)  # {}
# ```
#
#
# ### 三、字典的常用内置方法
# 字典提供了丰富的方法用于操作键、值和键值对，以下是最常用的方法：
#
#
# #### 1. 获取键、值、键值对
# - `keys()`：返回所有键的视图（可迭代对象）；
# - `values()`：返回所有值的视图；
# - `items()`：返回所有键值对的视图（每个元素是 `(key, value)` 元组）。
#
# ```python
d = {"a": 1, "b": 2, "c": 3}

# 获取所有键
print(d.keys())    # dict_keys(['a', 'b', 'c'])（视图对象）
print(list(d.keys()))  # ['a', 'b', 'c']（转为列表）

# 获取所有值
print(d.values())  # dict_values([1, 2, 3])
print(list(d.values()))  # [1, 2, 3]

# 获取所有键值对
print(d.items())   # dict_items([('a', 1), ('b', 2), ('c', 3)])
print(list(d.items()))  # [('a', 1), ('b', 2), ('c', 3)]
# ```
#
#
# #### 2. 合并字典
# `update(other)`：将 `other` 字典的键值对合并到当前字典（若键重复，`other` 的值会覆盖当前字典的值）。
#
# ```python
d1 = {"a": 1, "b": 2}
d2 = {"b": 3, "c": 4}

d1.update(d2)  # 合并d2到d1
print(d1)  # {'a': 1, 'b': 3, 'c': 4}（键"b"被d2的值覆盖）
# ```


# #### 3. 其他常用方法
# - `copy()`：返回字典的**浅拷贝**（新字典，修改新字典不影响原字典）；
# - `setdefault(key, default)`：若键存在则返回对应值；若不存在则添加 `key: default` 并返回 `default`（默认 `None`）。
#
# ```python
# copy()浅拷贝
d = {"a": 1, "b": [2, 3]}
d_copy = d.copy()
d_copy["a"] = 100  # 修改新字典的键"a"
print(d)       # {'a': 1, 'b': [2, 3]}（原字典不变）
print(d_copy)  # {'a': 100, 'b': [2, 3]}

# setdefault()
d = {"name": "Alice"}
# 键存在 → 返回对应值
print(d.setdefault("name", "Bob"))  # 'Alice'
# 键不存在 → 添加并返回默认值
print(d.setdefault("age", 18))      # 18
print(d)  # {'name': 'Alice', 'age': 18}
# ```
#
#
# ### 四、字典的遍历
# 通过 `for` 循环遍历字典的键、值或键值对，结合 `keys()`、`values()`、`items()` 方法实现。
#
# ```python
person = {"name": "Alice", "age": 18, "gender": "female"}

# 遍历键（默认遍历键，等价于 for key in person.keys()）
for key in person:
    print(key)  # name、age、gender

# 遍历值
for value in person.values():
    print(value)  # Alice、18、female

# 遍历键值对（用items()，接收key和value）
for key, value in person.items():
    print(f"{key}: {value}")  # name: Alice、age: 18、gender: female
# ```


### 五、字典推导式（Dictionary Comprehension）
# 字典推导式是一种简洁创建字典的语法，格式为：
# `{键表达式: 值表达式 for 变量 in 可迭代对象 if 条件}`
# 作用：遍历可迭代对象，对符合条件的元素生成键值对，组成新字典。
#
#
# #### 示例
# ```python
# 生成键为1-5，值为键的平方的字典
squares = {x: x**2 for x in range(1, 6)}
print(squares)  # {1: 1, 2: 4, 3: 9, 4: 16, 5: 25}

# 过滤值为偶数的键值对
nums = {"a": 1, "b": 2, "c": 3, "d": 4}
even_nums = {k: v for k, v in nums.items() if v % 2 == 0}
print(even_nums)  # {'b': 2, 'd': 4}

# 交换键值对（键和值互换）
d = {"a": 1, "b": 2}
swapped = {v: k for k, v in d.items()}
print(swapped)  # {1: 'a', 2: 'b'}
# ```
#
#
# ### 六、字典与其他数据类型的区别
# | 数据类型 | 核心特点                          | 访问方式       | 适用场景                     |
# |----------|-----------------------------------|----------------|------------------------------|
# | 列表     | 有序、可变、元素无关联            | 索引（`[0]`）  | 存储有序的、可修改的序列     |
# | 元组     | 有序、不可变、元素无关联          | 索引（`[0]`）  | 存储固定不变的序列           |
# | 字典     | 键值对关联、可通过键快速访问      | 键（`["key"]`）| 存储具有关联关系的数据（如配置、信息） |


# ### 七、注意事项
# 1. **键必须可哈希**：列表、字典等可变类型不可作为键（因不可哈希），否则会报错。
#    ```python
#    # 错误示例：列表作为键
#    # d = {[1, 2]: "value"}  # 报错：TypeError: unhashable type: 'list'
#    ```
#
# 2. **字典是引用类型**：直接赋值（`d2 = d1`）会让两个变量指向同一个字典，修改其中一个会影响另一个。如需独立副本，需用 `copy()` 或字典推导式。
#    ```python
d1 = {"a": 1}
d2 = d1  # 引用赋值
d2["a"] = 2
print(d1)  # {'a': 2}（d1也被修改）
#    ```
#
# 3. **嵌套字典**：字典的值可以是字典，用于表示更复杂的层级关系（如JSON结构）。
#    ```python
user = {
       "name": "Alice",
       "info": {
           "age": 18,
           "address": "Beijing"
       }
   }
print(user["info"]["age"])  # 18（访问嵌套字典的值）
#    ```
#
#
# ### 总结
# 字典是Python中以键值对形式存储数据的核心结构，具有键值关联、查找高效、可修改等特点。通过键可快速访问对应的值，支持添加、修改、删除键值对等操作，提供了丰富的内置方法（如 `keys()`、`values()`、`items()`）和简洁的字典推导式。字典广泛应用于存储配置信息、用户数据、映射关系等场景，是Python编程中不可或缺的工具。
