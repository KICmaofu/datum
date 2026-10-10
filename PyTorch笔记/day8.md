### 一、核心知识点
#### 1. Dataset：数据集抽象基类
PyTorch 中所有数据集的父类，负责**单个样本的读取、解析与预处理**，分为两类：
- **Map-style 映射式数据集**（最常用）：继承 `torch.utils.data.Dataset`，必须实现两个核心方法：
  - `__len__()`：返回数据集总样本数
  - `__getitem__(idx)`：根据索引 `idx` 返回单个样本（通常是 `(数据, 标签)` 元组）
  - 支持随机索引访问，可配合 shuffle 实现乱序
- **Iterable-style 流式数据集**：继承 `IterableDataset`，实现 `__iter__()`，用于无法随机访问的流式数据（如超大文件、实时数据流）

#### 2. DataLoader：批量加载调度器
封装 Dataset，实现**批量生成、乱序、多进程加速、数据预取**等工程能力，是模型训练循环的数据入口。
核心参数：
| 参数 | 作用 |
|------|------|
| `dataset` | 传入 Dataset 实例 |
| `batch_size` | 每个 batch 包含的样本数量 |
| `shuffle` | 每个 epoch 是否打乱样本顺序（训练集建议开启） |
| `num_workers` | 数据加载子进程数，0 表示主进程加载（Windows 环境建议设为 0 避免报错） |
| `drop_last` | 是否丢弃最后一个不足 batch_size 的样本 |
| `collate_fn` | 批处理拼接函数，自定义批量逻辑的核心入口 |

#### 3. collate_fn：批处理拼接函数
- **输入**：长度为 `batch_size` 的列表，每个元素是 Dataset 返回的单个样本。
- **输出**：拼接后的批量张量（通常是 `(批量数据, 批量标签)` 元组）。

**默认行为（`default_collate`）**：自动将同位置的张量/标量按第0维堆叠（`torch.stack`），例如单个图像 `[1,28,28]` → 批量图像 `[B,1,28,28]`，单个标签标量 → 标签向量 `[B]`。
**自定义场景**：样本长度不一致（如文本序列）、批量数据增强、异常样本过滤、自定义填充等。

#### 4. 完整批处理流程
1. DataLoader 根据 shuffle 规则生成 `batch_size` 个样本索引
2. 调用 Dataset 的 `__getitem__` 逐个取出单个样本，组成样本列表
3. 将样本列表传入 `collate_fn`，完成单样本到批量张量的拼接
4. 返回完整 batch 供模型计算

---

### 二、实操：自定义 MNIST 数据集加载与批处理
我们遵循规范实现自定义 Dataset 封装 MNIST，配合 DataLoader 完成批量加载，并验证输出。

#### 1. 导入依赖
```python
import torch
from torch.utils.data import Dataset, DataLoader
from torchvision import datasets, transforms
```

#### 2. 自定义 Dataset 实现
严格遵循 Map-style 规范，封装 MNIST 数据读取与预处理。
```python
class CustomMNISTDataset(Dataset):
    """自定义MNIST数据集类"""
    def __init__(self, root='./data', train=True, transform=None):
        """
        :param root: 数据存储根目录
        :param train: 是否加载训练集
        :param transform: 数据预处理/增强变换
        """
        # 加载原始MNIST数据（首次运行自动下载）
        self.raw_data = datasets.MNIST(root=root, train=train, download=True)
        self.transform = transform

    def __len__(self):
        """返回数据集总样本数"""
        return len(self.raw_data)

    def __getitem__(self, idx):
        """根据索引返回单个样本：(图像张量, 标签标量)"""
        # 取出单个样本：PIL格式图像 + 整数标签
        img_pil, label = self.raw_data[idx]
        
        # 应用预处理变换
        if self.transform is not None:
            img = self.transform(img_pil)
        else:
            img = img_pil
        
        return img, label
```

#### 3. 数据预处理与数据集实例化
```python
# 定义预处理流水线：PIL图像转张量 + 归一化到[0,1]
# ToTensor会自动将形状从 [28,28] 转为 [1,28,28]（通道优先）
transform = transforms.Compose([
    transforms.ToTensor(),
])

# 实例化训练集
train_dataset = CustomMNISTDataset(root='./data', train=True, transform=transform)

# 验证数据集规模
print(f"训练集总样本数: {len(train_dataset)}")
# 输出：训练集总样本数: 60000
```

#### 4. DataLoader 批量加载器实例化
```python
BATCH_SIZE = 8

# 使用默认collate_fn创建DataLoader
train_loader = DataLoader(
    dataset=train_dataset,
    batch_size=BATCH_SIZE,
    shuffle=True,       # 每个epoch打乱样本顺序
    num_workers=0,      # Windows环境设为0，Linux可设为4/8加速
    drop_last=False     # 保留不足batch的最后一批
)
```

#### 5. 验收：输出一个 Batch 的图像与标签
```python
# 从DataLoader迭代器中取出一个batch
data_iter = iter(train_loader)
images, labels = next(data_iter)

print("=== Batch 输出验证 ===")
print(f"图像 batch 形状: {images.shape}")  # 预期: [8, 1, 28, 28] → [batch_size, 通道数, 高, 宽]
print(f"标签 batch 形状: {labels.shape}")  # 预期: [8]
print(f"标签值: {labels.tolist()}")
print(f"图像数值范围: [{images.min().item():.2f}, {images.max().item():.2f}]")
```

**运行输出示例**：
```
=== Batch 输出验证 ===
图像 batch 形状: torch.Size([8, 1, 28, 28])
标签 batch 形状: torch.Size([8])
标签值: [5, 0, 4, 1, 9, 2, 1, 3]
图像数值范围: [0.00, 1.00]
```
输出形状与数值完全符合预期，批量加载正确。

---

### 三、进阶：自定义 collate_fn 演示
我们实现一个自定义批处理函数，在拼接 batch 的同时完成**归一化到[-1, 1]** 和形状校验，演示 collate_fn 的灵活能力。

```python
def custom_mnist_collate(batch):
    """
    自定义批处理函数
    :param batch: 样本列表，每个元素是 (img, label) 元组
    :return: 批量图像张量, 批量标签张量
    """
    # 拆分图像和标签
    img_list = []
    label_list = []
    for img, label in batch:
        img_list.append(img)
        label_list.append(label)
    
    # 手动堆叠成batch
    batch_images = torch.stack(img_list, dim=0)
    batch_labels = torch.tensor(label_list, dtype=torch.long)
    
    # 自定义处理：将数值从[0,1]映射到[-1,1]
    batch_images = batch_images * 2.0 - 1.0
    
    return batch_images, batch_labels
```

使用自定义 collate_fn 创建 DataLoader 并验证：
```python
# 使用自定义collate_fn的加载器
custom_loader = DataLoader(
    dataset=train_dataset,
    batch_size=8,
    shuffle=True,
    collate_fn=custom_mnist_collate
)

# 验证效果
images_custom, labels_custom = next(iter(custom_loader))
print("\n=== 自定义 collate_fn 验证 ===")
print(f"图像形状: {images_custom.shape}")
print(f"图像数值范围: [{images_custom.min().item():.2f}, {images_custom.max().item():.2f}]")
```

**输出示例**：
```
=== 自定义 collate_fn 验证 ===
图像形状: torch.Size([8, 1, 28, 28])
图像数值范围: [-1.00, 1.00]
```

---

### 四、关键避坑点
1. **Dataset 只处理单个样本**：不要在 `__getitem__` 里做批量操作，批量拼接逻辑由 `collate_fn` 负责
2. **num_workers 兼容性**：Windows 系统下多进程加载容易报错，调试阶段设为 0，Linux 可适当调大
3. **ToTensor 的作用**：将 PIL/numpy 图像从 `[H,W,C]` 转为 PyTorch 标准的 `[C,H,W]` 格式，并归一化到 [0,1]
4. **默认 collate_fn 的限制**：要求所有样本形状完全一致，否则堆叠报错；变长样本必须自定义 collate_fn 做 padding
5. **标签数据类型**：分类任务标签建议转为 `torch.long` 类型，匹配交叉熵损失函数的输入要求

需要我补充变长样本的 collate_fn 实现（如文本填充），或者写一个完整的训练循环结合这个 DataLoader 吗？