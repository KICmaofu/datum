# PyTorch 索引切片 & 维度变换

核心目标：掌握张量索引、切片、拼接、维度增减、维度置换；熟练完成 `[B, S, H, D]` ↔ `[B, H, S, D]` 转换（batch, seq_len, head, head_dim）

> 
> B：batch批次大小；S：序列长度seq_len；H：多头注意力head数；D：每个head的维度

## 一、基础索引与切片

张量索引格式：`tensor[dim0, dim1, dim2, dim3]`
切片语法：`start:end:step`，左闭右开；单独 `:` 代表取该维度全部；`...` 省略多个冒号

```
import torch
# 构造4维张量 [B, S, H, D] B=2,S=10,H=4,D=32
x = torch.randn(2, 10, 4, 32)

# 1. 取第0个batch全部数据 [S,H,D]
b0 = x[0, :, :, :]
# 简写
b0 = x[0]

# 2. 取batch=0，前5个token [S=5,H,D]
b0_s5 = x[0, 0:5, :, :]

# 3. 取batch=0，seq=2，head=1，全部dim
val = x[0, 2, 1, :]

# 4. 间隔采样：seq每隔2个取一个
s_step = x[:, ::2, :, :]

# 5. 布尔索引：取出大于0的值
mask = x > 0
pos = x[mask]
```

要点：

- 索引返回**视图（view）**，不复制内存；修改会影响原张量
- 切片如果改变维度结构，仍为视图；高级索引（整数数组索引）会返回新拷贝

## 二、维度增减 squeeze / unsqueeze

- `unsqueeze(dim)`：**增加一维**，插入在dim位置，大小为1
- `squeeze(dim)`：**删除大小为1的维度**；不传参则删除所有size=1的维度

```
# [B,S,H,D] -> [B,1,S,H,D] 在第1维插入维度1
x1 = x.unsqueeze(1)
print(x1.shape) # torch.Size([2, 1, 10, 4, 32])

# 删除第1维size=1的维度
x2 = x1.squeeze(1)
print(x2.shape) # torch.Size([2, 10, 4, 32])
```

> 
> 常见场景：广播对齐维度，注意力mask增加维度

## 三、维度置换 transpose / permute

### transpose：只能交换**两个维度**

`tensor.transpose(dim1, dim2)`

```
# [B,S,H,D] 交换 S 和 H → [B,H,S,D]
x = torch.randn(2, 10, 4, 32)
x_t = x.transpose(1,2)
print(x_t.shape) # [2,4,10,32] B H S D
```

### permute：一次性重排**全部维度**（多维度调换，更通用）

`tensor.permute(d0, d1, d2, d3)` 传入新维度顺序

```
# 原顺序：0:B,1:S,2:H,3:D → 目标 [B,H,S,D] → 新顺序 [0,2,1,3]
x_p = x.permute(0, 2, 1, 3)
print(x_p.shape) # [2,4,10,32] B H S D

# 还原：[B,H,S,D] → [B,S,H,D] permute(0,2,1,3)
x_back = x_p.permute(0, 2, 1, 3)
print(x_back.shape) # [2,10,4,32]
```

> 
> ⚠️ permute / transpose 之后张量内存不再连续；后续如果要view，需要先 `.contiguous()`

```
x_p = x.permute(0,2,1,3).contiguous()
```

## 四、堆叠与拼接 cat / stack

- `torch.cat([t1,t2], dim)`：**拼接**，在已有维度上合并，不新增维度；要求除dim外其余shape一致
- `torch.stack([t1,t2], dim)`：**堆叠**，新建一个维度，把张量放进去；所有张量shape必须完全相同

```
# 两个 [B,S,H,D] 张量
a = torch.randn(2,10,4,32)
b = torch.randn(2,10,4,32)

# 在seq维度拼接 S=20
cat_seq = torch.cat([a,b], dim=1)
print(cat_seq.shape) # [2,20,4,32]

# 在head维度stack，新增维度，head变成[[a],[b]]
stack_h = torch.stack([a,b], dim=2)
print(stack_h.shape) # [2,10,2,4,32]
```

## 五、实操：[B,S,H,D] ↔ [B,H,S,D]（多头注意力标准变换）

> 
> 多头注意力计算 QKV 时，经常要把 `[B,S,H,D]` 转 `[B,H,S,D]`，方便对 seq 做注意力分数计算

```
import torch

B, S, H, D = 2, 10, 4, 32
# 原始张量 shape: [B, S, H, D]
x = torch.randn(B, S, H, D)
print("原始shape:", x.shape) # torch.Size([2, 10, 4, 32])

# 方式1 transpose 交换dim1(S) 和 dim2(H)
x_hsd = x.transpose(1, 2)
print("transpose转换后 [B,H,S,D]:", x_hsd.shape) # [2,4,10,32]

# 方式2 permute 重排维度
x_hsd2 = x.permute(0, 2, 1, 3)
print("permute转换后 [B,H,S,D]:", x_hsd2.shape) # [2,4,10,32]

# 转回 [B,S,H,D]
x_restore = x_hsd.transpose(1,2)
print("还原shape：", x_restore.shape) # [2,10,4,32]
```

### 精准切片练习（转换后切片）

```
# [B,H,S,D] 张量，取 batch=0，head=0，前6个token
slice_val = x_hsd[0, 0, 0:6, :]
print(slice_val.shape) # [6,32]
```

## 六、高频易错点总结

1. transpose 只能交换两个维度；多维度重排优先 permute
2. permute/transpose 产生非连续张量，view/reshape 报错，加 `.contiguous()`
3. cat 是**合并现有维度**，stack是**新增维度**，不要混淆
4. squeeze 只能删除size=1维度；想删别的维度要用索引
5. 4维多头张量维度顺序非常关键：`[B,S,H,D]` 是拆分QKV后的形状；`[B,H,S,D]` 是计算attention score的形状

## 七、验收自测题

```
# 自测：
B, S, H, D = 4, 16, 8, 64
t = torch.randn(B, S, H, D)
# 1. 将t转为 [B,H,S,D]
# 2. 在转换后的张量上，取出第0个batch，第2个head，3~10号token
# 3. 把切片结果再转回 [S,D]
```

参考答案

```
t_hsd = t.permute(0,2,1,3)
res = t_hsd[0, 2, 3:11, :]
print(res.shape) # torch.Size([8,64])
```

要不要我出一套5道练习题（含答案）帮你巩固张量维度变换？