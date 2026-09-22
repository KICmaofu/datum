# 一、高维张量运算逻辑 & 维度对齐原则（PyTorch）
## 1. 核心概念：Batch维度 + 矩阵维度
对于Transformer注意力里的张量：
> `Q, K, V` shape: `[batch, heads, seq_len, d_k]`
- 前面维度（batch, heads）：**批量维度，广播维度**，不参与矩阵乘法
- 最后两维：**矩阵维度，真正做matmul**
  - Q：`[..., n, d]`
  - K：`[..., m, d]` → K转置 `K^T: [..., d, m]`
  - $QK^T$：`[..., n, m]`

> ✅ **高维matmul维度对齐原则（torch.matmul）**
> 1. 只作用于**最后两个维度**做矩阵相乘；前面所有维度视为批量维度，自动广播。
> 2. 矩阵乘法要求：Q最后一维 == K倒数第二维（转置之后）
> 3. 批量维度遵循**广播规则**：维度相等 / 其中一个为1；广播后扩展，不复制数据。

### 广播规则回顾
从最右侧批量维度开始向左比对：
- 两个维度相等 ✔
- 其中一个维度等于1 ✔，会自动扩展
- 都大于1且不等 ❌，报错
> 广播**不会修改最后两个矩阵维度**，只作用于前面的batch/head维度。

## 2. 逐元素运算 vs matmul
- **逐元素运算 (+, *, mask)**：全部维度都要满足广播
- **torch.matmul**：仅前面批量维度广播，最后两维严格矩阵乘法约束

## 3. 缩放点积注意力公式
$$
\text{Attention}(Q,K,V)=\text{softmax}\left(\frac{QK^T}{\sqrt{d_k}} + \text{mask}\right)V
$$
1. $QK^T$：高维批量矩阵乘法
2. 缩放：除以$\sqrt{d_k}$，防止内积过大导致softmax梯度消失（逐元素除法）
3. mask：加掩码，把需要屏蔽位置填 `-inf`，softmax后概率趋近0（广播）
4. softmax：对最后一维做归一化
5. 乘V：再次批量matmul

---

# 二、完整实操代码：模拟QKᵀ + 缩放 + 掩码
目标：
输入 Q,K，计算注意力分数，输出正确shape的attn_score。
mask演示：上三角掩码（自回归，不能看到未来token）

```python
import torch
import torch.nn.functional as F

def scaled_dot_product_attention_score(Q, K, mask=None):
    """
    只计算注意力分数部分：QK^T / sqrt(d_k) + mask
    :param Q: [batch, heads, seq_q, d_k]
    :param K: [batch, heads, seq_k, d_k]
    :param mask: [seq_q, seq_k] 或者可广播到 [batch, heads, seq_q, seq_k]
    :return: attn_score: [batch, heads, seq_q, seq_k] 注意力分数（softmax之前）
    """
    d_k = Q.size(-1)
    # 1. 批量矩阵乘法 Q @ K.transpose(-2,-1)
    # transpose(-2,-1): 交换K最后两个维度 [b,h,m,d] -> [b,h,d,m]
    QK_T = torch.matmul(Q, K.transpose(-2, -1))
    # 2. 缩放
    attn_score = QK_T / torch.sqrt(torch.tensor(d_k, dtype=torch.float32))
    # 3. 掩码：mask为True的位置填充 -inf，softmax后为0
    if mask is not None:
        attn_score = attn_score.masked_fill(mask, -1e9)
    return attn_score

# ========== 测试 ==========
batch = 2
heads = 4
seq_len = 10
d_k = 64

# 构造Q,K
Q = torch.randn(batch, heads, seq_len, d_k)
K = torch.randn(batch, heads, seq_len, d_k)

# 构造自回归掩码：上三角mask，不能看到未来token
# mask shape [seq_len, seq_len]，会自动广播到 [batch, heads, seq_len, seq_len]
mask = torch.triu(torch.ones(seq_len, seq_len, dtype=torch.bool), diagonal=1)

attn_score = scaled_dot_product_attention_score(Q, K, mask)
print(f"Q shape: {Q.shape}")
print(f"K shape: {K.shape}")
print(f"mask shape: {mask.shape}")
print(f"attn_score shape: {attn_score.shape}")
# 预期输出：torch.Size([2, 4, 10, 10])

# 验证掩码效果：打印第一个head第一行
print("\nmasked区域（未来token）值：", attn_score[0,0,0,1:])
```

运行输出示例：
```
Q shape: torch.Size([2, 4, 10, 64])
K shape: torch.Size([2, 4, 10, 64])
mask shape: torch.Size([10, 10])
attn_score shape: torch.Size([2, 4, 10, 10])

masked区域（未来token）值： tensor([-1.0000e+09, -1.0000e+09, -1.0000e+09, -1.0000e+09, -1.0000e+09,
        -1.0000e+09, -1.0000e+09, -1.0000e+09, -1.0000e+09])
```

# 三、维度对齐拆解（重点）
Q: `[2,4,10,64]`
K: `[2,4,10,64]`
K.transpose(-2,-1) → `[2,4,64,10]`

`matmul(Q, K.T)`
- batch=2，heads=4：批量维度，一一对应，不广播
- Q最后两维 `[10,64]` @ K.T最后两维 `[64,10]` → `[10,10]`
输出：`[2,4,10,10]`

mask原始shape `[10,10]`，做`attn_score.masked_fill(mask, -1e9)`
mask广播：`[10,10]` → `[1,1,10,10]` → `[2,4,10,10]`，完美匹配 attn_score。

> 如果mask写成 `[batch, 1, seq_len, seq_len]`，heads维度会广播，同一个mask复用给所有多头，是工程里常用写法。

# 四、易错点总结
1. ❌ K.transpose(0,1)：错误！**必须 transpose(-2,-1)**，交换矩阵的两个维度，不要动batch/head
2. ❌ mask用0/1相乘：不行，softmax前要加 `-inf`，不能直接置0；0仍然会产生概率
3. ❌ 缩放用`d_k`整数直接除：建议转浮点开根号，避免整数精度问题
4. ❌ matmul和`*`混淆：`*`是逐元素，不能用来做QK矩阵乘法

# 五、拓展：接上softmax与V相乘（完整注意力）
```python
V = torch.randn(batch, heads, seq_len, d_k)
attn_weight = F.softmax(attn_score, dim=-1) # softmax在最后一维 token维度
out = torch.matmul(attn_weight, V)
print("attention output shape:", out.shape) # [2,4,10,64]
```

# 验收要点
✅ 输入`[B,H,S,D]`的Q、K，输出注意力分数shape为 `[B,H,S,S]`
✅ 掩码正确广播，未来token位置填充`-1e9`
✅ 维度规则理解：批量维度广播，最后两维执行矩阵乘法

如果你需要，我可以继续：
1. 手写实现**批量matmul**（不用torch.matmul，用循环实现多头QK相乘）来验证；
2. 或者做一个广播异常案例，看哪些维度组合会报错。