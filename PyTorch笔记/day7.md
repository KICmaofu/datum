### 一、核心知识点
#### 1. nn.Module 定义规范
`nn.Module` 是 PyTorch 所有神经网络组件的基类，自定义网络必须遵循标准开发规范：
- **继承要求**：自定义类必须继承 `torch.nn.Module`
- **初始化规范**：`__init__` 方法第一行必须调用 `super().__init__()`，启动父类的参数注册与管理机制
- **模块定义**：可学习层、激活层、子模块都在 `__init__` 中定义，并赋值为 `self.xxx` 属性
- **前向逻辑**：必须实现 `forward()` 方法，编写张量运算流程；调用 `model(x)` 时底层自动执行 `forward()`

#### 2. 参数管理机制
PyTorch 会自动递归管理所有嵌套模块的可学习参数：
- **自动注册**：赋值为实例属性的 `nn.Parameter` 和 `nn.Module` 子模块，其参数会自动纳入父模块管理
- **核心访问接口**：
  - `model.parameters()`：返回所有参数张量的迭代器，主要用于传入优化器
  - `model.named_parameters()`：返回 `(参数名, 参数张量)` 迭代器，参数名携带层级路径
  - `model.state_dict()`：返回所有参数的有序字典，用于模型保存与加载
- **命名规则**：参数名 = `子模块属性名.参数类型名`，多层嵌套时逐级拼接，例如 `fc1.weight`

#### 3. 子模块嵌套规则
- 任意 `nn.Module` 子类实例，只要赋值为 `self.xxx` 就会自动注册为子模块
- 支持任意深度嵌套，父模块可递归收集所有子孙模块的参数
- 常用模块化容器：`nn.Sequential`（顺序执行）、`nn.ModuleList`（列表式管理）、`nn.ModuleDict`（字典式管理）

---

### 二、实操：两层全连接网络实现
我们实现一个标准的两层全连接分类网络：
**结构**：输入 → 全连接层1 → ReLU激活 → 全连接层2 → 输出

```python
import torch
import torch.nn as nn

class TwoLayerFC(nn.Module):
    """两层全连接神经网络"""
    def __init__(self, in_dim, hidden_dim, out_dim):
        """
        :param in_dim: 输入特征维度
        :param hidden_dim: 隐藏层维度
        :param out_dim: 输出维度（类别数）
        """
        # 必须调用父类初始化，启动参数管理机制
        super().__init__()
        # 第一层全连接
        self.fc1 = nn.Linear(in_dim, hidden_dim)
        # ReLU 激活层
        self.relu = nn.ReLU()
        # 第二层全连接
        self.fc2 = nn.Linear(hidden_dim, out_dim)
    
    def forward(self, x):
        """前向传播逻辑"""
        x = self.fc1(x)
        x = self.relu(x)
        x = self.fc2(x)
        return x

# 实例化模型：输入784维（MNIST图像展平），隐藏层256维，输出10类
model = TwoLayerFC(in_dim=784, hidden_dim=256, out_dim=10)
```

---

### 三、验收：打印所有参数名与形状
通过 `named_parameters()` 遍历所有参数，输出名称、形状与可训练属性：

```python
print("=== 模型所有参数列表 ===")
total_params = 0
for name, param in model.named_parameters():
    print(f"参数名: {name:15} | 形状: {tuple(param.shape)} | 可训练: {param.requires_grad}")
    total_params += param.numel()

print(f"\n总参数量: {total_params:,}")
```

#### 运行输出
```
=== 模型所有参数列表 ===
参数名: fc1.weight      | 形状: (256, 784) | 可训练: True
参数名: fc1.bias        | 形状: (256,)     | 可训练: True
参数名: fc2.weight      | 形状: (10, 256)  | 可训练: True
参数名: fc2.bias        | 形状: (10,)      | 可训练: True

总参数量: 203,530
```

#### 结果说明
1. **命名规则**：参数名与 `__init__` 中定义的子模块属性名一一对应，`fc1.weight` 即第一层全连接的权重矩阵
2. **权重形状**：`nn.Linear` 权重默认形状为 `(输出维度, 输入维度)`（`out_features × in_features`），与矩阵乘法的左乘逻辑匹配
3. **可训练性**：`nn.Linear` 的参数默认 `requires_grad=True`，自动参与梯度计算与参数更新
4. **参数量验证**：
   - fc1：`256×784 + 256 = 200,960`
   - fc2：`10×256 + 10 = 2,570`
   - 总计 203,530，与遍历统计结果完全一致

---

### 四、拓展：参数与子模块管理常用操作
#### 1. 遍历所有子模块
```python
print("=== 所有子模块 ===")
for name, module in model.named_children():
    print(f"模块名: {name} | 类型: {type(module).__name__}")
```

#### 2. 冻结指定层参数
```python
# 冻结第一层参数，微调时常用
for name, param in model.named_parameters():
    if name.startswith("fc1"):
        param.requires_grad = False
```

#### 3. Sequential 容器简化写法
两层全连接也可以用 `nn.Sequential` 快速堆叠，参数管理规则完全一致：
```python
class TwoLayerFC_Sequential(nn.Module):
    def __init__(self, in_dim, hidden_dim, out_dim):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(in_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, out_dim)
        )
    
    def forward(self, x):
        return self.net(x)
```
此时参数名会变为 `net.0.weight`、`net.0.bias`、`net.2.weight`，按 Sequential 内的顺序编号命名。

---

### 五、关键避坑点
1. 遗漏 `super().__init__()` 会导致参数无法注册，`named_parameters()` 返回空
2. 子模块如果放在普通 Python 列表/字典中，参数不会被自动管理，必须用 `nn.ModuleList` / `nn.ModuleDict` 包裹
3. `forward()` 内部支持任意 Python 逻辑（循环、条件判断等），动态计算图会自动构建

需要我补充 `nn.ModuleList` 和 `nn.Sequential` 的核心区别，或者实现一个带 BatchNorm + Dropout 的两层全连接网络吗？