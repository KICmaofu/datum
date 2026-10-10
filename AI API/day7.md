# 文档加载器与文本分割器详解（RAG数据预处理核心）
> 这两个组件是 **RAG（检索增强生成）** 的第一步：把原始文档（PDF/Word/网页/Markdown）转化为可向量化、可检索的文本块。承接前面的 LangChain 基础，最终目标是把处理好的文本块存入向量库，实现知识检索。
>
> 链路定位：`文档加载 → 文本分割 → 向量化 → 向量存储 → 检索 → 生成回答`

---

## 一、文档加载器（Document Loader）
### 1. 核心作用
将不同格式、不同来源的文档，统一转换为 LangChain 标准的 `Document` 对象列表，屏蔽不同文件格式的差异，后续所有组件（分割、向量化、检索）都基于 `Document` 工作。

每个 `Document` 对象包含两个核心属性：
- `page_content`：字符串类型，文档的文本内容
- `metadata`：字典类型，存储元信息（文件名、页码、URL、作者等），用于检索溯源、过滤

### 2. 环境准备
加载器大多在 `langchain_community` 包中，不同格式需要安装对应依赖：
```bash
# 基础包
pip install langchain langchain_community

# 按需安装对应格式依赖
pip install pypdf          # PDF加载
pip install python-docx    # Word加载
pip install beautifulsoup4 # 网页加载
pip install markdown       # Markdown解析
```

### 3. 常用加载器与代码示例
#### （1）纯文本加载器 `TextLoader`【最基础】
加载 `.txt`、`.md` 等纯文本文件，适合本地知识库。
```python
from langchain_community.document_loaders import TextLoader

# 加载单个文件
loader = TextLoader("./知识库/intro.md", encoding="utf-8")
documents = loader.load()  # 返回 Document 列表

print(documents[0].page_content)  # 文本内容
print(documents[0].metadata)     # {'source': './知识库/intro.md'}
```

#### （2）PDF 加载器 `PyPDFLoader`【最常用】
按页加载 PDF，自动携带页码元数据，适合论文、报告、电子书。
```python
from langchain_community.document_loaders import PyPDFLoader

loader = PyPDFLoader("./白皮书.pdf")
documents = loader.load()  # 每一页对应一个 Document 对象

print(f"共 {len(documents)} 页")
print(documents[0].metadata)  # {'source': './白皮书.pdf', 'page': 0}
```

> 进阶推荐：`PyMuPDFLoader` 加载速度更快、解析更精准，适合扫描版以外的PDF。

#### （3）网页加载器 `WebBaseLoader`
爬取网页正文内容，适合在线文档、博客、帮助中心。
```python
from langchain_community.document_loaders import WebBaseLoader

loader = WebBaseLoader("[https://example.com/docs](https://example.com/docs)")
documents = loader.load()
```

#### （4）目录批量加载器 `DirectoryLoader`
批量加载指定文件夹下的所有文档，自动识别格式，是构建本地知识库的首选。
```python
from langchain_community.document_loaders import DirectoryLoader

# 加载 ./docs 目录下所有 .md 文件
loader = DirectoryLoader(
    path="./docs",
    glob="**/*.md",  # 匹配规则，**表示递归子目录
    loader_cls=TextLoader,  # 指定使用的加载器
    loader_kwargs={"encoding": "utf-8"}
)

documents = loader.load()
print(f"加载了 {len(documents)} 个文档")
```

### 4. 核心价值
- **格式统一**：无论什么来源的文档，最终都是 `Document` 对象，后续流程完全复用
- **元数据携带**：文件名、页码、URL 等信息全程保留，检索结果可溯源
- **扩展丰富**：支持上百种数据源（Notion、飞书文档、数据库、CSV 等）

---

## 二、文本分割器（Text Splitter）
### 1. 为什么必须分割？
1. **上下文长度限制**：大模型和嵌入模型都有最大 token 限制，完整文档无法直接传入
2. **检索精度要求**：整块文档包含信息太多，检索时会引入大量无关内容，降低答案准确率
3. **语义聚焦**：切成小块后，每块对应一个主题，检索更精准，注入提示词后干扰更少

### 2. 核心参数
几乎所有分割器都基于这两个参数调优：
| 参数 | 作用 | 调优建议 |
|---|---|---|
| `chunk_size` | 每个文本块的大小（字符数/token数） | 通用场景 500~1000 字符；知识密度高的文档调小，长文档调大 |
| `chunk_overlap` | 相邻块之间的重叠长度 | 通常为 chunk_size 的 10%~20%，避免语义在边界处断裂 |

> 核心原则：**语义完整优先**，不是越小越好；过度碎片化会破坏上下文逻辑。

### 3. 常用分割器对比
#### （1）`RecursiveCharacterTextSplitter`【通用首选】
- 原理：递归按分隔符分割，优先级 `\n\n`（段落）→ `\n`（行）→ `。`（句子）→ 字符
- 优势：尽可能保持语义单元完整，不会生硬切断句子
- 适用：绝大多数通用文本场景，默认推荐

```python
from langchain_text_splitters import RecursiveCharacterTextSplitter

splitter = RecursiveCharacterTextSplitter(
    chunk_size=800,
    chunk_overlap=100,
    separators=["\n\n", "\n", "。", "！", "？", " ", ""]  # 中文优化分隔符
)

# 对加载好的 documents 进行分割
chunks = splitter.split_documents(documents)

print(f"分割为 {len(chunks)} 个文本块")
print(chunks[0].page_content)
print(chunks[0].metadata)  # 自动继承原文档的元数据
```

#### （2）`TokenTextSplitter`【精确控制Token】
- 原理：按 token 数量分割，而不是字符数
- 优势：和大模型上下文单位对齐，能精确控制每个块的 token 占用
- 适用：需要严格控制块大小、对接嵌入模型的生产场景

#### （3）`MarkdownTextSplitter`【结构化文档专用】
- 原理：按 Markdown 标题层级（#、##、###）分割，保留文档结构
- 优势：分割后的块天然对应一个小节，语义完整性远高于通用分割器
- 适用：Markdown 格式的知识库、技术文档

#### （4）`PythonCodeTextSplitter`【代码专用】
- 原理：按函数、类、代码块分割，保持代码语法结构
- 适用：代码知识库、代码助手场景

### 4. 分割效果验证建议
分割完成后建议抽查几个块：
1. 有没有出现句子被生硬切断的情况
2. 每个块是否有相对独立完整的语义
3. 重叠部分是否自然衔接了上下文

---

## 三、完整流程实战：批量加载 → 文本分割
```python
from langchain_community.document_loaders import DirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

# 1. 批量加载本地知识库目录
loader = DirectoryLoader(
    path="./knowledge_base",
    glob="**/*.md",
    encoding="utf-8"
)
raw_docs = loader.load()
print(f"加载文档数量：{len(raw_docs)}")

# 2. 初始化文本分割器
splitter = RecursiveCharacterTextSplitter(
    chunk_size=800,
    chunk_overlap=120,
    separators=["\n\n", "\n", "。", "！", "？", "；", " ", ""]
)

# 3. 执行分割
split_chunks = splitter.split_documents(raw_docs)
print(f"分割后文本块数量：{len(split_chunks)}")

# 4. 查看第一个块
print("\n=== 示例文本块 ===")
print(f"来源：{split_chunks[0].metadata['source']}")
print(f"内容：{split_chunks[0].page_content[:100]}...")
```

---

## 四、最佳实践与避坑
1. **优先使用专用分割器**：Markdown 文档就用 `MarkdownTextSplitter`，比通用分割器效果好很多
2. **中文场景优化分隔符**：默认分隔符是英文的，手动加上中文句号、问号、分号
3. **不要过度分割**：chunk_size 小于 200 容易造成语义碎片化，检索准确率下降
4. **保留元数据**：分割后的块会自动继承原文档 metadata，不要手动丢弃，后续检索溯源全靠它
5. **PDF 乱码问题**：优先用 `PyMuPDFLoader` 替代 `PyPDFLoader`，扫描版 PDF 需要先做 OCR
6. **重叠不是越大越好**：超过 30% 会导致大量重复内容，浪费向量存储空间和检索算力

---

要不要我给你写一个**批量加载本地文档+自动分割+导出元数据统计**的完整脚本，指定文件夹路径就能直接运行？