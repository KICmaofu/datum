### 一、核心概念拆解

#### 1. 计算图（Computational Graph）

计算图是描述张量运算依赖关系的**有向无环图（DAG）**，节点代表张量，边代表数学运算。PyTorch 采用**动态计算图**机制：每次前向传播时实时构建计算图，反向传播完成后销毁，天然支持循环、条件判断等动态控制流。

#### 2. 前向传播（Forward）

- 执行张量运算，得到前向计算结果；
- 同时**自动追踪并构建计算图**：每个运算结果张量都会记录自身的 `grad_fn`（梯度函数，即该运算对应的反向求导方法）。

#### 3. 反向传播（Backward）

从**标量损失值**出发，沿着计算图反向执行链式求导法则，计算所有 `requires_grad=True` 张量的梯度，并将结果存入张量的 `.grad` 属性。

#### 4. 叶子节点（Leaf Tensor）

- **定义**：由用户直接创建、不是任何运算输出的张量，是计算图的“起点节点”。
- **核心特征**：
  - `is_leaf = True`
  - `grad_fn = None`（没有生成它的运算）
  - 反向传播后梯度会永久保留在 `.grad` 中
- **典型场景**：模型可训练参数、输入特征、自定义权重张量。

与之对应的**非叶子节点（中间节点）**是运算产生的张量，`is_leaf = False`，拥有 `grad_fn`，反向传播后默认释放梯度以节省内存。

#### 5. requires_grad 传递规则

- 张量默认 `requires_grad=False`，不参与梯度计算；
- 只要运算的任意一个输入 `requires_grad=True`，输出张量的 `requires_grad` 自动置为 `True`；
- 设计目的：仅给需要更新的参数计算梯度，大幅节省计算和内存开销。

---

### 二、手动构建计算图实操

我们构建线性函数计算图：`loss = w * x + b`，完整观察前向建图、反向求导的全过程。

#### 步骤1：创建初始叶子节点

```
import torch

# 手动创建3个叶子节点，开启梯度计算
x = torch.tensor([2.0], requires_grad=True)  # 输入值
w = torch.tensor([3.0], requires_grad=True)  # 权重
b = torch.tensor([1.0], requires_grad=True)  # 偏置

print("=== 初始叶子节点属性 ===")
print(f"x: is_leaf={x.is_leaf}, requires_grad={x.requires_grad}, grad_fn={x.grad_fn}")
print(f"w: is_leaf={w.is_leaf}, requires_grad={w.requires_grad}, grad_fn={w.grad_fn}")
print(f"b: is_leaf={b.is_leaf}, requires_grad={b.requires_grad}, grad_fn={b.grad_fn}")
```

输出：

```
=== 初始叶子节点属性 ===
x: is_leaf=True, requires_grad=True, grad_fn=None
w: is_leaf=True, requires_grad=True, grad_fn=None
b: is_leaf=True, requires_grad=True, grad_fn=None
```

三者均为用户直接创建，属于叶子节点，无对应的反向求导函数。

#### 步骤2：前向传播，构建计算图

```
# 前向计算：依次产生中间节点
y = w * x  # 乘法运算
z = y + b  # 加法运算
loss = z.sum()  # 转换为标量（反向传播要求损失必须是标量）

print("\n=== 前向传播后节点属性 ===")
print(f"y: is_leaf={y.is_leaf}, grad_fn={y.grad_fn}")
print(f"z: is_leaf={z.is_leaf}, grad_fn={z.grad_fn}")
print(f"loss: is_leaf={loss.is_leaf}, grad_fn={loss.grad_fn}")
```

输出：

```
=== 前向传播后节点属性 ===
y: is_leaf=False, grad_fn=<MulBackward0 object at ...>
z: is_leaf=False, grad_fn=<AddBackward0 object at ...>
loss: is_leaf=False, grad_fn=<SumBackward0 object at ...>
```

- y、z、loss 都是运算产物，属于非叶子节点；
- 每个节点都记录了对应的反向求导函数（MulBackward、AddBackward、SumBackward），共同构成完整的计算链路。

#### 步骤3：反向传播，计算梯度

```
# 触发反向传播，链式求导
loss.backward()

print("\n=== 反向传播后叶子节点梯度 ===")
print(f"x.grad = {x.grad}")  # d(loss)/dx = w
print(f"w.grad = {w.grad}")  # d(loss)/dw = x
print(f"b.grad = {b.grad}")  # d(loss)/db = 1
```

输出：

```
=== 反向传播后叶子节点梯度 ===
x.grad = tensor([3.])
w.grad = tensor([2.])
b.grad = tensor([1.])
```

**数学验证**：
对于 $loss = w \cdot x + b$：

- 对 $x$ 求偏导：$\frac{\partial loss}{\partial x} = w = 3$
- 对 $w$ 求偏导：$\frac{\partial loss}{\partial w} = x = 2$
- 对 $b$ 求偏导：$\frac{\partial loss}{\partial b} = 1$
计算结果与手动推导完全一致。

> 
> 补充：中间节点 y 的梯度默认被释放，`y.grad` 为 None。若需保留中间梯度，可在前向传播后调用 `y.retain_grad()`。

---

### 三、梯度累积现象与清零的必要性

#### 1. PyTorch 默认行为：梯度累积

PyTorch 中 `.grad` 的默认行为是**累加**，而非覆盖。每次调用 `backward()`，新计算的梯度都会加到原有的 `.grad` 上，而不是替换原有值。

#### 2. 实验验证梯度累积

```
print("=== 第一次反向传播后 w.grad =", w.grad)

# 第二次前向+反向，不清空梯度
y2 = w * x
z2 = y2 + b
loss2 = z2.sum()
loss2.backward()

print("=== 第二次反向传播后 w.grad =", w.grad)
```

输出：

```
=== 第一次反向传播后 w.grad = tensor([2.])
=== 第二次反向传播后 w.grad = tensor([4.])
```

可以看到，w 的梯度从 2 变成了 4，发生了**两倍累积**。如果不清零，多次迭代后梯度会持续叠加，完全偏离单步真实梯度值。

#### 3. 为什么必须梯度清零？

在标准模型训练流程中，**每个 batch 的梯度应当独立计算**：

1. 每个 batch 前向传播计算损失，反向传播得到该 batch 的梯度；
2. 优化器基于该 batch 的梯度更新参数；
3. 若不清零，下一个 batch 的梯度会与上一个 batch 的梯度叠加，导致梯度计算错误，模型更新方向混乱，最终无法收敛。

实际训练中，`optimizer.zero_grad()` 会遍历所有可训练参数，批量执行 `.grad.zero_()` 原地清零操作。

#### 4. 正确清零演示

```
# 手动原地清零梯度
w.grad.zero_()
b.grad.zero_()
x.grad.zero_()

# 清零后再次反向传播
y3 = w * x
z3 = y3 + b
loss3 = z3.sum()
loss3.backward()

print("=== 清零后再次反向传播 w.grad =", w.grad)
```

输出：

```
=== 清零后再次反向传播 w.grad = tensor([2.])
```

梯度恢复为正确的单步计算值。

#### 5. 梯度累积的合理使用场景

梯度累积是有意设计的特性，而非缺陷，典型适用场景：

- **模拟大 batch 训练**：显存不足时，累计多个小 batch 的梯度后再更新参数，等价于大 batch 的训练效果；
- **多 GPU 分布式训练**：不同 GPU 上的梯度需要汇总累加，再统一更新参数。

但在常规的单 batch 单步更新场景下，**每次反向传播前必须清零梯度**。

---

### 四、关键避坑总结

1. **反向传播前提**：损失必须是标量（scalar），否则需要传入 `gradient` 参数指定求导权重。
2. **仅叶子节点保留梯度**：非叶子节点的梯度默认释放，不要直接访问其 `.grad`。
3. **in-place 操作风险**：对叶子节点使用原地运算（如 `x += 1`）会破坏计算图，导致反向传播报错。
4. **推理阶段关闭梯度**：用 `torch.no_grad()` 包裹推理代码，避免构建计算图，节省内存和算力。

需要我再演示一个多层感知机的完整计算图，或者讲解 `torch.no_grad()` 与 `detach()` 的区别吗？