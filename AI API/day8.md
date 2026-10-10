# Embedding 模型调用与文本转向量实现
> 承接上一节「文档加载 + 文本分割」，本节进入 RAG 核心环节：**文本向量化（Embedding）**。这一步是连接“非结构化文本”和“向量检索”的桥梁，分割后的文本块通过 Embedding 模型转化为固定维度的向量数组，才能存入向量数据库并实现语义检索。
>
> RAG 链路位置：`文档加载 → 文本分割 → 【文本向量化】 → 向量存储 → 检索 → 生成回答`

---

## 一、Embedding 核心原理
### 1. 什么是 Embedding
Embedding（嵌入）是一种将非结构化文本映射为**固定维度高维稠密向量**的技术，由专门训练的 Embedding 模型生成。
- 核心特性：**语义越相似的文本，生成的向量在空间中的距离越近**（余弦相似度越高）
- 本质作用：把人类可理解的“语义匹配”转化为计算机可计算的“向量距离计算”，从而实现毫秒级语义检索

### 2. 两个核心方法
LangChain 中 Embedding 模型统一提供两个方法，对应 RAG 的两个核心场景：
| 方法 | 用途 | 场景 |
|---|---|---|
| `embed_documents(texts)` | 批量文本转向量 | 知识库入库：把所有分割后的文本块批量向量化后存入向量库 |
| `embed_query(text)` | 单条查询转向量 | 检索时：把用户问题转化为向量，去向量库中匹配相似文本 |

> ⚠️ 铁则：**知识库入库和用户检索必须使用同一个 Embedding 模型**，模型不同则向量空间不一致，检索会完全失效。

---

## 二、主流 Embedding 模型选型
### 1. 闭源 API 型（推荐快速开发，无需本地算力）
| 模型 | 厂商 | 中文效果 | 推荐场景 |
|---|---|---|---|
| `embedding-2` | 智谱 AI | 优秀 | 和 GLM 对话模型同平台，复用密钥，国内直连 |
| `text-embedding-v3` | 通义千问 | 优秀 | 阿里出品，稳定可靠，Dashscope 平台 |
| `text-embedding-3-small` | OpenAI | 一般（英文标杆） | 英文场景，需境外网络 |

### 2. 开源本地型（推荐数据敏感、离线部署）
| 模型 | 出品方 | 维度 | 推荐场景 |
|---|---|---|---|
| `bge-small-zh-v1.5` | 智源 BAAI | 512 | 中文场景首选，轻量高速，效果标杆 |
| `bge-base-zh-v1.5` | 智源 BAAI | 768 | 平衡精度与性能，生产常用 |
| `m3e-base` | MokaAI | 768 | 中文通用场景，短文本检索优秀 |

---

## 三、环境准备
```bash
# 核心依赖
pip install langchain langchain-openai python-dotenv

# 本地开源 Embedding 依赖（可选，跑 API 方式不用装）
pip install sentence-transformers

# 向量计算工具
pip install numpy scikit-learn
```

沿用之前的 `.env` 配置，新增 Embedding 模型配置：
```env
# .env
LLM_API_KEY=你的sk-xxx
LLM_BASE_URL=[https://open.bigmodel.cn/api/paas/v4/](https://open.bigmodel.cn/api/paas/v4/)
EMBEDDING_MODEL=embedding-2
```

---

## 四、方式一：API 调用 Embedding（快速上手推荐）
使用 `langchain_openai` 的 `OpenAIEmbeddings` 类，兼容所有支持 OpenAI 接口规范的厂商（智谱、通义、DeepSeek 等），只需修改 `base_url` 和 `model`。

### 1. 初始化与基础调用
```python
from dotenv import load_dotenv
import os
from langchain_openai import OpenAIEmbeddings

load_dotenv()

# 初始化 Embedding 模型
embeddings = OpenAIEmbeddings(
    api_key=os.getenv("LLM_API_KEY"),
    base_url=os.getenv("LLM_BASE_URL"),
    model=os.getenv("EMBEDDING_MODEL"),
    batch_size=10  # 批量调用时的并发数
)

# 1. 单条查询转向量（检索场景用）
query_vector = embeddings.embed_query("什么是向量数据库")
print(f"向量维度：{len(query_vector)}")
print(f"向量前5个值：{query_vector[:5]}")

# 2. 批量文本转向量（知识库入库用）
texts = ["向量数据库用于存储Embedding向量", "关系型数据库存储结构化数据"]
doc_vectors = embeddings.embed_documents(texts)
print(f"批量生成向量数量：{len(doc_vectors)}")
```

### 2. 串联文本分割：批量向量化
承接上一节的文本分割结果，直接对所有文本块批量向量化：
```python
from langchain_community.document_loaders import DirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

# 1. 加载 + 分割（复用之前的流程）
loader = DirectoryLoader("./knowledge_base", glob="**/*.md", encoding="utf-8")
raw_docs = loader.load()

splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)
chunks = splitter.split_documents(raw_docs)

# 2. 提取所有文本内容
chunk_texts = [doc.page_content for doc in chunks]

# 3. 批量向量化
chunk_vectors = embeddings.embed_documents(chunk_texts)

print(f"文本块数量：{len(chunks)}")
print(f"生成向量数量：{len(chunk_vectors)}")
print(f"每个向量维度：{len(chunk_vectors[0])}")
```

---

## 五、方式二：本地开源 Embedding（BGE 中文模型）
适合数据敏感、离线部署、不想调用 API 的场景，直接在本地运行 BGE 中文模型。

```python
from langchain_community.embeddings import HuggingFaceEmbeddings

# 初始化本地 BGE 中文小模型
embeddings = HuggingFaceEmbeddings(
    model_name="BAAI/bge-small-zh-v1.5",
    model_kwargs={"device": "cpu"},  # 有 GPU 可改为 "cuda"
    encode_kwargs={"normalize_embeddings": True}  # 归一化向量，方便计算余弦相似度
)

# 用法和 API 版完全一致
vector = embeddings.embed_query("嵌入式开发入门")
print(f"向量维度：{len(vector)}")
```

> 首次运行会自动下载模型文件（~100MB），后续本地运行无需网络。

---

## 六、语义相似度验证（余弦相似度）
通过计算向量之间的余弦相似度，可以直观验证 Embedding 的语义匹配能力。余弦值越接近 1，语义越相似。

```python
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

# 准备3条测试文本
texts = [
    "如何学习大模型应用开发",
    "大模型开发入门教程",
    "今天天气真不错"
]

# 批量转向量
vectors = embeddings.embed_documents(texts)
vectors_np = np.array(vectors)

# 计算第1条和第2条的相似度
sim_1_2 = cosine_similarity([vectors_np[0]], [vectors_np[1]])[0][0]
# 计算第1条和第3条的相似度
sim_1_3 = cosine_similarity([vectors_np[0]], [vectors_np[2]])[0][0]

print(f"语义相近文本相似度：{sim_1_2:.4f}")  # 通常 0.8+
print(f"语义无关文本相似度：{sim_1_3:.4f}")  # 通常 0.3 以下
```

---

## 七、最佳实践与避坑指南
1. **模型一致性原则**：入库和检索必须使用完全相同的 Embedding 模型、版本、参数，否则向量空间不匹配，检索失效
2. **中文场景选中文模型**：优先使用 BGE、智谱、通义等中文预训练模型，英文原生模型（如 ada）中文语义效果一般
3. **控制文本长度**：Embedding 模型有最大 token 限制（通常 512/1024），超过会被截断，所以必须先做文本分割
4. **向量归一化**：开启 `normalize_embeddings`，归一化后的向量用内积即可等价于余弦相似度，计算更快
5. **批量调用优化**：入库时使用 `embed_documents` 批量处理，比单条循环调用速度快、限流风险低
6. **不要混用对话模型**：Embedding 和对话大模型是两类完全不同的模型，不能用对话模型生成向量

---

## 八、下一步：向量数据库
到这一步，我们已经能把文档切成块、转成向量数组。下一步就是把这些向量连同原文、元数据一起存入**向量数据库**，实现基于语义的相似度检索，最终完整实现 RAG。

要不要我接着讲**向量数据库（FAISS / Chroma）** 的存储与检索，直接把上面的向量存进去，写一个完整的“提问→检索→生成回答”最小 RAG demo？