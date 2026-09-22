# LangChain 环境搭建与核心概念详解

> 
> LangChain 是大模型应用开发框架，核心作用是**把模型、提示词、工具、记忆等组件模块化、可编排化**，避免重复写胶水代码。本文承接之前的原生 API 与提示词工程知识，带你从 0 搭建环境并理解三大核心概念。

## 一、LangChain 环境搭建

### 1. 环境要求

- Python **3.9 ~ 3.12**（LangChain 0.2+ 版本不再支持 3.8）
- 提前准备好可用的大模型 API Key（智谱/DeepSeek/通义/OpenAI 均可，兼容 OpenAI 接口格式）

### 2. 安装核心依赖

```
# 1. LangChain 核心框架
pip install langchain

# 2. OpenAI 兼容模型集成包（智谱、DeepSeek、通义兼容模式都能用）
pip install langchain-openai

# 3. 环境变量工具（沿用之前的用法）
pip install python-dotenv
```

### 3. 环境变量配置

在项目根目录新建 `.env` 文件，和之前保持一致：

```
# .env
# 以智谱 GLM 为例，其他模型改对应 base_url 即可
LLM_API_KEY=你的sk-xxx
LLM_BASE_URL=[https://open.bigmodel.cn/api/paas/v4/](https://open.bigmodel.cn/api/paas/v4/)
LLM_MODEL=glm-4-flash
```

### 4. 最小可行性验证

创建 `test_langchain.py`，确认环境跑通：

```
from dotenv import load_dotenv
import os
from langchain_openai import ChatOpenAI

load_dotenv()

# 初始化大模型（和原生 API 参数一一对应）
llm = ChatOpenAI(
    api_key=os.getenv("LLM_API_KEY"),
    base_url=os.getenv("LLM_BASE_URL"),
    model=os.getenv("LLM_MODEL"),
    temperature=0.7
)

# 直接调用
if __name__ == "__main__":
    result = llm.invoke("你好，介绍一下 LangChain")
    print(result.content)
```

---

## 二、三大核心概念：模型 / 提示词模板 / 链

### 1. 模型（Models）—— 统一大模型调用接口

#### 概念

LangChain 对不同厂商的大模型做了抽象封装，主流分为两类：

- **Chat Model（对话模型）**：接收消息列表（system/user/assistant），输出消息，对应 `ChatOpenAI` 类，是当前主流。
- **LLM（文本补全模型）**：接收纯字符串，输出字符串，属于旧范式，现在少用。

#### 核心能力

- 统一调用方式：换模型只改初始化参数，业务代码不用动
- 原生支持 `temperature`、`top_p`、`max_tokens` 等所有采样参数
- 支持流式输出、回调、重试等工程能力

#### 代码示例

```
from langchain_openai import ChatOpenAI

model = ChatOpenAI(
    model="glm-4-flash",
    temperature=0.3,
    top_p=0.8,
    max_tokens=512
)
```

---

### 2. 提示词模板（Prompt Templates）—— 提示词工程化复用

#### 概念

把之前手写的提示词（角色设定、格式约束、用户问题）做成**带占位符的模板**，动态传入变量，实现提示词与业务代码解耦、复用。

对应之前的知识点：角色设定、格式约束都可以封装进模板，用户输入作为变量传入。

#### 两种常用模板

##### （1）字符串模板（简单场景）

```
from langchain_core.prompts import PromptTemplate

prompt = PromptTemplate.from_template(
    "你是资深{role}，请用通俗易懂的语言解释{question}，不超过100字。"
)

# 填充变量
formatted_prompt = prompt.format(role="后端工程师", question="什么是微服务")
```

##### （2）对话提示模板（主流，对应消息结构）

更常用，支持 system、user 等角色，完美匹配对话模型的消息格式：

```
from langchain_core.prompts import ChatPromptTemplate

# 按角色定义模板，{xxx} 是占位符
prompt = ChatPromptTemplate.from_messages([
    ("system", "你是{persona}，回答遵循：{rules}"),
    ("user", "{question}")
])

# 填充变量，生成完整消息列表
messages = prompt.invoke({
    "persona": "AI开发讲师",
    "rules": "分点回答，简洁专业",
    "question": "什么是提示词模板"
})
```

> 
> ✅ 优势：提示词模板可以单独维护、版本管理，不用硬编码在业务逻辑里。

---

### 3. 链（Chains）—— 组件编排流水线

#### 概念

链是 LangChain 的核心编排机制，把「提示词模板 → 模型 → 输出解析」等多个步骤按顺序拼接成一个可执行的流水线，实现“输入变量 → 链处理 → 输出结果”的完整流程。

#### 现代写法：LCEL 表达式语言

LangChain 现在官方推荐 **LCEL（LangChain Expression Language）**，用管道符 `|` 拼接组件，写法简洁且灵活：

```
链 = 提示词模板 | 模型 | 输出解析器
```

#### 基础链完整示例

把上面的模板和模型组装成一条问答链：

```
from dotenv import load_dotenv
import os
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()

# 1. 初始化模型
model = ChatOpenAI(
    api_key=os.getenv("LLM_API_KEY"),
    base_url=os.getenv("LLM_BASE_URL"),
    model=os.getenv("LLM_MODEL"),
    temperature=0.3
)

# 2. 定义提示词模板
prompt = ChatPromptTemplate.from_messages([
    ("system", "你是资深技术讲师，回答分3个要点，每个要点不超过20字。"),
    ("user", "{question}")
])

# 3. 组装成链（LCEL 管道写法）
chain = prompt | model

# 4. 运行链，传入变量
if __name__ == "__main__":
    result = chain.invoke({"question": "LangChain 的核心作用是什么"})
    print(result.content)
```

---

## 三、进阶补充：输出解析器（OutputParser）

对应之前的「格式约束」知识点，LangChain 提供了 `OutputParser` 自动解析模型输出，不用自己写正则/JSON 解析。

### 示例：结构化 JSON 输出

```
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate

# 定义解析器
parser = JsonOutputParser()

# 模板里注入格式要求
prompt = ChatPromptTemplate.from_messages([
    ("system", "严格按要求输出，不要多余文字。\n{format_instructions}"),
    ("user", "分析{topic}的优缺点")
]).partial(format_instructions=parser.get_format_instructions())

# 组装链：模板 → 模型 → JSON解析器
chain = prompt | model | parser

# 运行后直接得到 Python 字典
result = chain.invoke({"topic": "微服务架构"})
print(type(result))  # <class 'dict'>
```

---

## 四、核心价值总结

| 组件 | 解决的问题 | 对应原生开发的痛点 |
| --- | --- | --- |
| 模型 | 统一大模型调用接口 | 换厂商要重写 API 调用代码 |
| 提示词模板 | 提示词复用、版本化管理 | 提示词硬编码在代码里，维护混乱 |
| 链 | 流程编排、组件组合 | 手动拼接消息、处理输出，重复造轮子 |

## 五、常见踩坑

1. **版本不兼容**：LangChain 迭代快，建议用 `langchain>=0.2.0`，和 `langchain-openai>=0.1.0` 配套
2. **国内模型接入**：只要厂商支持 OpenAI 兼容接口，都可以用 `ChatOpenAI` 类，只改 `base_url`
3. **模板占位符写错**：变量名必须和 `invoke` 传入的 key 完全一致，否则报错
4. **JSON 解析失败**：配合 `JsonOutputParser` 时，system 提示词要加上“严格输出，不要多余解释”

---

要不要我基于这套环境，给你写一个**带角色设定+格式约束+思维链引导**的完整 LangChain 链代码，直接复现上一节的提示词进阶效果？