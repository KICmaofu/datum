# PyTorch 张量创建、设备迁移、内存共享 vs 拷贝 完整示例
> 知识点：
> 1. 0维/1维/2维/3维张量创建
> 2. CPU <-> GPU 设备迁移 `.to()` / `.cuda()` / `.cpu()`
> 3. **共享内存（view、reshape、切片，底层同一块存储）**
> 4. **拷贝内存（clone、detach，新开内存）**
> 5. 原地修改验证共享/拷贝差异

> 前置：确认cuda可用
```python
import torch
print(torch.cuda.is_available())
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(device)
```

## 一、创建不同维度张量
```python
# 0维张量（标量，只有一个值）
t0 = torch.tensor(10)
print("0维张量 shape:", t0.shape, "data:", t0)

# 1维张量（向量）
t1 = torch.tensor([1,2,3,4])
print("1维张量 shape:", t1.shape, "data:", t1)

# 2维张量（矩阵，行×列）
t2 = torch.tensor([[1,2],[3,4]])
print("2维张量 shape:", t2.shape, "data:\n", t2)

# 3维张量 (batch, H, W) 常用于图像
t3 = torch.randn(2, 3, 4)
print("3维张量 shape:", t3.shape, "data:\n", t3)
```

## 二、设备迁移 CPU ↔ GPU
> ⚠️ 关键点：**张量迁移到GPU会产生新拷贝，CPU和GPU内存相互独立，不共享！**
```python
# 创建在CPU上
t_cpu = torch.tensor([1,2,3])
print("原始设备：", t_cpu.device)

# 迁移到GPU
t_gpu = t_cpu.to(device)
# t_gpu = t_cpu.cuda() # 等价写法，仅device为cuda时可用
print("迁移后GPU张量设备：", t_gpu.device)

# 迁回CPU
t_back_cpu = t_gpu.cpu()
print("迁回CPU设备：", t_back_cpu.device)

# 直接在GPU上创建张量
t_gpu_direct = torch.tensor([10,20], device=device)
print("直接GPU创建：", t_gpu_direct.device)
```

> ❗重要坑：CPU张量和GPU张量**不能直接运算**，必须放到同一设备。

## 三、内存共享（同 storage，浅拷贝）
> 下面操作**不会复制底层数据，只是改变张量的视图**，共用一块内存：
> - `reshape()` / `view()`
> - 切片 `t[1:]`
> - `transpose()` / `permute()`
> 判断是否共享内存：`tensor.untyped_storage().data_ptr()` 获取底层内存地址，地址相同=共享。

```python
t = torch.arange(6)
print("原始张量：", t)
print("原始内存地址：", t.untyped_storage().data_ptr())

# view：视图，共享内存
t_view = t.view(2,3)
print("view张量地址：", t_view.untyped_storage().data_ptr())
print("是否共享内存：", t_view.untyped_storage().data_ptr() == t.untyped_storage().data_ptr())

# 修改视图，原张量同步变化！
t_view[0,0] = 999
print("修改view后原始t：", t)
```

输出会看到：**t 和 t_view 内存地址一样，修改其中一个，另一个跟着变**

切片示例：
```python
t = torch.arange(5)
t_slice = t[1:3]
print(t_slice.untyped_storage().data_ptr() == t.untyped_storage().data_ptr())
t_slice[0] = 100
print(t) # 原张量被修改
```

## 四、内存拷贝（新storage，深拷贝）
`.clone()`：**完全复制一份新张量，新内存地址，互不干扰**
```python
t = torch.arange(6)
t_clone = t.clone()

print("原始地址：", t.untyped_storage().data_ptr())
print("clone地址：", t_clone.untyped_storage().data_ptr())
print("地址相等？", t_clone.untyped_storage().data_ptr() == t.untyped_storage().data_ptr())

# 修改clone，原张量不变
t_clone[0] = 999
print("t:", t)
print("t_clone:", t_clone)
```

`.detach()`：返回新张量，**共享底层存储，但脱离计算图**（用于梯度，内存仍然共享！很多人踩坑）
```python
x = torch.tensor([1.,2,3], requires_grad=True)
y = x.detach()
print(y.untyped_storage().data_ptr() == x.untyped_storage().data_ptr()) # True，共享内存
y[0] = 100
print(x) # x的值被修改，但y没有梯度
```

> ✅ 区分记忆：
> - `detach()`：**共享内存，剥离梯度**
> - `clone()`：**新建内存，保留requires_grad属性**
> - `clone().detach()`：最常用，新建内存+脱离计算图

## 五、跨设备迁移一定是拷贝
```python
t_cpu = torch.tensor([1,2,3])
t_gpu = t_cpu.to(device)
# CPU张量 和 GPU张量 底层存储完全分开
print(t_cpu.untyped_storage().data_ptr())
if device.type == "cuda":
    print(t_gpu.untyped_storage().data_ptr()) # GPU显存地址空间，和CPU完全独立
t_gpu[0] = 999
print(t_cpu) # CPU张量不会变化
```

## 六、总结对比表
| 操作 | 是否新开内存 | 是否共享底层数据 | 备注 |
|---|---|---|---|
| view / reshape | ❌ | ✅ | 视图，不能改变总元素数 |
| 切片 | ❌ | ✅ | 视图 |
| transpose | ❌ | ✅ | 转置，共享存储 |
| detach() | ❌ | ✅ | 共享内存，断掉梯度 |
| clone() | ✅ | ❌ | 完整拷贝，新内存 |
| .to(device) / .cuda() | ✅ | ❌ | 设备迁移，显存/内存之间拷贝 |

## 七、常见面试考点
1. `view` 要求张量内存连续；如果不连续，要用 `.contiguous()` 开辟连续内存（会触发拷贝）
```python
t = torch.arange(6).reshape(2,3)
t_t = t.t()
# t_t.view(3,2) # 报错！转置后内存不连续
t_t_cont = t_t.contiguous() # 触发拷贝，开辟连续内存
print(t_t_cont.untyped_storage().data_ptr() == t_t.untyped_storage().data_ptr()) # False
```

2. 共享内存只在**同一个设备**内有效；CPU ↔ GPU 之间永远是拷贝，不存在跨设备共享内存。

3. `reshape` 自动选择 view（共享）或 contiguous+clone（拷贝），取决于张量是否连续；`view` 强制要求连续。

如果你想要，我可以把全部代码合并成一个完整可运行脚本，加上注释和打印输出，直接复制运行。或者出几道自测题检验这个知识点。