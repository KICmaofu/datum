Java中的**数据结构**主要通过**Java集合框架（Java Collections Framework）** 实现，用于存储和组织数据。集合框架提供了一套统一的接口和实现类，涵盖了常见的数据结构（如列表、集合、映射、栈、队列等），并支持高效的增删改查操作。


### 一、Java集合框架的整体结构  
Java集合框架的核心接口分为两大体系：**`Collection`**（存储单个元素的集合）和**`Map`**（存储键值对的映射表）。其简化结构如下：  

```  
java.util  
├─ Collection（单元素集合根接口）  
│  ├─ List（有序、可重复）  
│  │  ├─ ArrayList（动态数组）  
│  │  ├─ LinkedList（双向链表）  
│  │  └─ Vector（线程安全的动态数组，已过时）  
│  │  
│  ├─ Set（无序、不可重复）  
│  │  ├─ HashSet（基于哈希表，无序）  
│  │  ├─ LinkedHashSet（哈希表+链表，有序）  
│  │  └─ TreeSet（基于红黑树，可排序）  
│  │  
│  └─ Queue（队列，先进先出）  
│     ├─ LinkedList（双向链表实现的队列）  
│     └─ PriorityQueue（优先队列，基于堆）  
│  
└─ Map（键值对映射表）  
   ├─ HashMap（哈希表，无序）  
   ├─ LinkedHashMap（哈希表+链表，有序）  
   ├─ TreeMap（基于红黑树，可排序）  
   └─ Hashtable（线程安全的哈希表，已过时）  
```  


### 二、核心数据结构及实现类  


#### 1. List（列表）：有序、可重复的元素集合  
`List`接口的核心特点是**元素有序（插入顺序）、可重复**，支持通过索引（下标）访问元素，类似“动态数组”。  

| 实现类       | 底层结构         | 核心特点                                                                 | 适用场景                                   |
|--------------|------------------|--------------------------------------------------------------------------|--------------------------------------------|
| `ArrayList`  | 动态数组         | - 随机访问快（`get(index)`时间复杂度O(1)）<br>- 插入/删除元素慢（需移动元素，O(n)）<br>- 非线程安全 | 频繁查询，少量插入删除（如数据展示列表）   |
| `LinkedList` | 双向链表         | - 随机访问慢（O(n)）<br>- 插入/删除元素快（只需修改指针，O(1)在头尾）<br>- 非线程安全 | 频繁插入删除（如队列、栈）                 |  


**示例：`ArrayList`与`LinkedList`**  
```java
import java.util.ArrayList;
import java.util.LinkedList;
import java.util.List;

public class ListDemo {
    public static void main(String[] args) {
        // ArrayList：动态数组
        List<String> arrayList = new ArrayList<>();
        arrayList.add("A"); // 新增元素
        arrayList.add("B");
        System.out.println(arrayList.get(0)); // 快速访问：A（O(1)）

        // LinkedList：双向链表
        List<String> linkedList = new LinkedList<>();
        linkedList.add("X");
        linkedList.addFirst("Y"); // 头部插入（O(1)）
        System.out.println(linkedList.get(0)); // Y（查询需遍历，O(n)）
    }
}
```  


#### 2. Set（集合）：无序、不可重复的元素集合  
`Set`接口的核心特点是**元素无序（或按特定规则排序）、不可重复**（通过`equals()`和`hashCode()`判断唯一性）。  

| 实现类          | 底层结构               | 核心特点                                                                 | 适用场景                                   |
|-----------------|------------------------|--------------------------------------------------------------------------|--------------------------------------------|
| `HashSet`       | 哈希表（数组+链表/红黑树） | - 无序（存储顺序≠插入顺序）<br>- 增删查效率高（平均O(1)）<br>- 允许`null`元素 | 去重、快速查找（如存储唯一标识）           |
| `LinkedHashSet` | 哈希表+双向链表        | - 有序（维护插入顺序）<br>- 性能略低于`HashSet`（需维护链表）             | 去重且需要保留插入顺序（如日志记录）       |
| `TreeSet`       | 红黑树（自平衡二叉树） | - 可排序（默认自然排序或自定义`Comparator`）<br>- 增删查效率O(log n)      | 去重且需要排序（如排行榜、范围查询）       |  


**示例：`HashSet`与`TreeSet`**  
```java
import java.util.HashSet;
import java.util.TreeSet;

public class SetDemo {
    public static void main(String[] args) {
        // HashSet：无序去重
        HashSet<Integer> hashSet = new HashSet<>();
        hashSet.add(3);
        hashSet.add(1);
        hashSet.add(3); // 重复元素，自动过滤
        System.out.println(hashSet); // 输出：[1, 3]（顺序不确定）

        // TreeSet：自动排序
        TreeSet<Integer> treeSet = new TreeSet<>();
        treeSet.add(3);
        treeSet.add(1);
        treeSet.add(2);
        System.out.println(treeSet); // 输出：[1, 2, 3]（自然排序）
    }
}
```  


#### 3. Queue（队列）：先进先出（FIFO）的元素集合  
`Queue`接口模拟“队列”数据结构，核心特点是**先进先出（FIFO）**，通常用于处理需要按顺序排队的元素。  

| 实现类             | 底层结构         | 核心特点                                                                 | 适用场景                                   |
|--------------------|------------------|--------------------------------------------------------------------------|--------------------------------------------|
| `LinkedList`       | 双向链表         | 实现`Queue`接口，支持队列的基本操作（`add()`入队、`poll()`出队）          | 普通队列（如任务排队）                     |
| `PriorityQueue`    | 小顶堆（完全二叉树） | 优先队列，元素按优先级排序（默认自然排序），出队时总是取最小元素           | 按优先级处理任务（如医院急诊排队）         |  


**示例：`PriorityQueue`**  
```java
import java.util.PriorityQueue;
import java.util.Queue;

public class QueueDemo {
    public static void main(String[] args) {
        // 优先队列（默认小顶堆，元素从小到大出队）
        Queue<Integer> pq = new PriorityQueue<>();
        pq.add(3);
        pq.add(1);
        pq.add(2);

        while (!pq.isEmpty()) {
            System.out.println(pq.poll()); // 依次输出：1、2、3
        }
    }
}
```  


#### 4. Map（映射）：键值对（Key-Value）的集合  
`Map`接口存储**键值对**，通过“键（Key）”快速查找“值（Value）”，键唯一（重复键会覆盖值），值可重复。  

| 实现类            | 底层结构               | 核心特点                                                                 | 适用场景                                   |
|-------------------|------------------------|--------------------------------------------------------------------------|--------------------------------------------|
| `HashMap`         | 哈希表（数组+链表/红黑树） | - 无序（键的存储顺序≠插入顺序）<br>- 增删查效率高（平均O(1)）<br>- 允许`null`键和值 | 快速键值映射（如缓存、字典）               |
| `LinkedHashMap`   | 哈希表+双向链表        | - 有序（维护插入顺序或访问顺序）<br>- 性能略低于`HashMap`                 | 需要保留键的顺序（如LRU缓存）               |
| `TreeMap`         | 红黑树                 | - 可排序（键按自然排序或自定义`Comparator`）<br>- 增删查效率O(log n)      | 键需要排序的映射（如按日期排序的日志）     |  


**示例：`HashMap`与`TreeMap`**  
```java
import java.util.HashMap;
import java.util.TreeMap;

public class MapDemo {
    public static void main(String[] args) {
        // HashMap：无序键值对
        HashMap<String, Integer> hashMap = new HashMap<>();
        hashMap.put("B", 2);
        hashMap.put("A", 1);
        System.out.println(hashMap); // 输出：{A=1, B=2}（顺序不确定）

        // TreeMap：键自动排序
        TreeMap<String, Integer> treeMap = new TreeMap<>();
        treeMap.put("B", 2);
        treeMap.put("A", 1);
        System.out.println(treeMap); // 输出：{A=1, B=2}（按键的自然顺序）
    }
}
```  


#### 5. 其他基础数据结构  
除集合框架外，Java中还有一些基础数据结构：  

- **数组（Array）**：固定大小的连续内存空间，支持随机访问（O(1)），但大小不可变，适合存储已知数量的元素。  
  ```java
  int[] arr = new int[3]; // 固定大小3
  arr[0] = 10;
  System.out.println(arr[0]); // 10
  ```  

- **栈（Stack）**：先进后出（LIFO），Java中可通过`Deque`的`push()`（入栈）和`pop()`（出栈）实现（推荐用`ArrayDeque`，而非过时的`Stack`类）。  
  ```java
  import java.util.ArrayDeque;
  import java.util.Deque;

  Deque<Integer> stack = new ArrayDeque<>();
  stack.push(1); // 入栈
  stack.push(2);
  System.out.println(stack.pop()); // 出栈：2（后进先出）
  ```  

- **树（Tree）**：`TreeSet`和`TreeMap`底层基于**红黑树**（自平衡二叉查找树），支持有序遍历和范围查询（如`subSet()`、`subMap()`）。  

- **图（Graph）**：Java标准库未直接实现，需自定义（常用邻接表：`Map<Node, List<Node>>` 或邻接矩阵：二维数组）。  


### 三、数据结构的选择依据  
选择合适的数据结构需结合**操作效率**和**业务需求**：  

| 需求场景                     | 推荐数据结构               | 核心原因                          |
|------------------------------|----------------------------|-----------------------------------|
| 频繁随机访问（`get(index)`） | `ArrayList`                | 数组底层，O(1)时间复杂度          |
| 频繁插入删除（尤其是头尾）   | `LinkedList`               | 链表底层，O(1)时间复杂度          |
| 去重（无重复元素）           | `HashSet`                  | 哈希表，快速去重和查找            |
| 去重且需要排序               | `TreeSet`                  | 红黑树，自动排序                  |
| 键值对映射，快速查询         | `HashMap`                  | 哈希表，O(1)平均查询效率          |
| 键值对且需要排序             | `TreeMap`                  | 红黑树，键有序                    |
| 按顺序排队（FIFO）           | `LinkedList`（作为Queue）   | 链表实现，高效入队出队            |
| 按优先级排队                 | `PriorityQueue`            | 堆结构，自动按优先级出队          |  


### 总结  
Java集合框架提供了丰富的数据结构实现，核心分为`Collection`（单元素）和`Map`（键值对）两大体系。不同实现类基于数组、链表、哈希表、红黑树等底层结构，适用于不同场景：  
- `ArrayList`/`LinkedList` 用于有序可重复的列表；  
- `HashSet`/`TreeSet` 用于无序/有序的去重集合；  
- `HashMap`/`TreeMap` 用于键值对映射；  
- `Queue`/`PriorityQueue` 用于队列和优先队列。  

理解各数据结构的底层原理和效率特性，是编写高效Java代码的基础。