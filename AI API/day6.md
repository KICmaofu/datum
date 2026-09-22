# 提示词模板与输出解析器 深度实战

> 
> 承接 LangChain 核心概念，本节聚焦两个最常用的工程化组件：
> 
> 
> - **PromptTemplate**：把提示词工程模板化、可复用、可传参
> - **OutputParser**：自动约束输出格式 + 解析成结构化数据
> 完美对应之前学的「提示词工程」「格式约束」，解决原生 API 开发的维护痛点。

---

## 一、提示词模板（Prompt Template）

### 1. 核心价值

原生开发中，提示词硬编码在代码里，修改、复用、多场景适配都很麻烦。模板把**固定规则**和**动态变量**分离：

- 固定部分：角色设定、格式要求、思维链指令
- 动态部分：用户问题、业务参数
通过占位符 `{变量名}` 动态填充，实现提示词与业务逻辑解耦。

### 2. 两类常用模板

#### （1）字符串模板 `PromptTemplate`

纯文本模板，适合简单提示、文本补全场景。

```
from langchain_core.prompts import PromptTemplate

# 定义模板，{role} {question} 是占位符
template = PromptTemplate.from_template(
    "你是资深{role}，请用100字以内解释{question}，通俗易懂。"
)

# 填充变量，生成最终提示词
prompt_text = template.format(role="AI开发工程师", question="什么是提示词模板")
print(prompt_text)
```

#### （2）对话模板 `ChatPromptTemplate`【主流】

对应对话模型的消息结构（system/user/assistant），是当前最常用的模板类型，完美匹配角色设定、多轮对话。

```
from langchain_core.prompts import ChatPromptTemplate

# 按角色定义模板，支持多条消息
chat_template = ChatPromptTemplate.from_messages([
    ("system", "你是{persona}，回答遵循：{rules}"),  # 系统提示：角色+规则
    ("user", "{user_input}")                            # 用户输入：动态变量
])

# 填充变量，生成模型可接收的消息列表
messages = chat_template.invoke({
    "persona": "技术讲师",
    "rules": "分3点回答，每点不超过20字",
    "user_input": "LangChain模板的作用"
})
```

> 
> ✅ 工程优势：角色、规则、输入完全分离，产品运营可以直接改模板文案，不用动业务代码。

### 3. 进阶实用技巧

#### ① 部分预填充 `partial`

提前固定部分变量（比如角色），调用时只传业务变量，减少重复传参。

```
# 定义基础模板
base_template = ChatPromptTemplate.from_messages([
    ("system", "你是{role}，回答风格：{style}"),
    ("user", "{question}")
])

# 预填充角色和风格，生成专用模板
dev_template = base_template.partial(
    role="后端架构师",
    style="严谨专业，优先给出方案优缺点"
)

# 后续调用只需要传 question
chain = dev_template | model
result = chain.invoke({"question": "微服务架构适用场景"})
```

#### ② 嵌入思维链（CoT）指令

把之前学的思维链引导直接写进系统提示模板，一键开启推理模式。

```
cot_template = ChatPromptTemplate.from_messages([
    ("system", """你是逻辑推理助手。
请严格按照步骤回答：
1. 先分步写出推理过程
2. 最后给出最终结论
不要跳步，不要直接给答案。"""),
    ("user", "{question}")
])
```

#### ③ 嵌入少样本（Few-shot）示例

把示例写进模板，让模型模仿输出格式，适合复杂格式约束场景。

```
fewshot_template = ChatPromptTemplate.from_messages([
    ("system", "按照示例格式对技术名词分类"),
    ("user", "MySQL"),
    ("assistant", "分类：数据库，子类：关系型"),
    ("user", "Redis"),
    ("assistant", "分类：数据库，子类：缓存型"),
    ("user", "{term}")
])
```

---

## 二、输出解析器（Output Parser）

### 1. 核心价值

原生 API 开发中，要求模型输出 JSON 但经常多写一句「好的，下面是结果」导致 `json.loads()` 报错。
OutputParser 解决两个核心问题：

1. **自动注入格式指令**：把输出格式要求自动拼接到提示词里，不用手写
2. **自动解析+校验**：把模型返回的字符串转成 Python 对象（字典、类实例），自带容错

### 2. 常用解析器详解

#### （1）`StrOutputParser`【最基础】

只提取模型回复的文本内容，去掉消息对象包装，是默认最常用的解析器。

```
from langchain_core.output_parsers import StrOutputParser

parser = StrOutputParser()

# 组装链：模板 → 模型 → 字符串解析
chain = chat_template | model | parser

# 调用后直接得到字符串，不用 .content
result = chain.invoke({"user_input": "什么是LangChain"})
print(type(result))  # <class 'str'>
```

#### （2）`JsonOutputParser`【最灵活】

自动要求模型输出 JSON，解析成 Python 字典，适合动态字段、简单结构化场景。

```
from langchain_core.output_parsers import JsonOutputParser

# 初始化解析器
json_parser = JsonOutputParser()

# 模板中注入格式指令
json_template = ChatPromptTemplate.from_messages([
    ("system", "严格按要求输出，不要任何多余解释。\n{format_instructions}"),
    ("user", "分析技术：{tech_name}，输出名称、定位、核心优势、适用场景")
]).partial(format_instructions=json_parser.get_format_instructions())

# 组装链
chain = json_template | model | json_parser

# 调用后直接得到字典
result = chain.invoke({"tech_name": "LangChain"})
print(result["核心优势"])  # 直接按键取值
```

> 
> 🔍 原理：`get_format_instructions()` 会生成一段标准的JSON格式要求文本，自动注入到提示词中，模型识别后按格式输出。

#### （3）`PydanticOutputParser`【生产级推荐】

基于 Pydantic 模型做**强类型校验**，字段类型、必填项自动检查，解析失败会自动重试修复，适合生产环境。

```
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

# 1. 定义数据结构（类似数据库表结构）
class TechAnalysis(BaseModel):
    name: str = Field(description="技术名称")
    category: str = Field(description="技术分类")
    advantages: list[str] = Field(description="核心优势，数组格式")
    difficulty: str = Field(description="学习难度：简单/中等/困难")

# 2. 初始化解析器
pydantic_parser = PydanticOutputParser(pydantic_object=TechAnalysis)

# 3. 模板注入格式指令
pydantic_template = ChatPromptTemplate.from_messages([
    ("system", "严格输出指定格式，不要多余文字。\n{format_instructions}"),
    ("user", "分析技术：{tech_name}")
]).partial(format_instructions=pydantic_parser.get_format_instructions())

# 4. 组装链
chain = pydantic_template | model | pydantic_parser

# 5. 调用后直接得到 TechAnalysis 对象
result = chain.invoke({"tech_name": "向量数据库"})
print(result.advantages[0])  # 点语法访问，IDE有代码提示
```

> 
> ✅ 生产优势：类型安全、字段明确、自动校验，避免脏数据流入下游业务。

---

## 三、组合完整实战：角色+CoT+结构化输出

整合所有知识点，实现一个「技术方案分析助手」：

- 角色：资深架构师
- 能力：分步推理，输出结构化JSON
- 输出：包含推理过程、最终结论、风险点三个字段

```
from dotenv import load_dotenv
import os
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

load_dotenv()

# 1. 初始化模型
model = ChatOpenAI(
    api_key=os.getenv("LLM_API_KEY"),
    base_url=os.getenv("LLM_BASE_URL"),
    model=os.getenv("LLM_MODEL"),
    temperature=0.3
)

# 2. 定义输出解析器
parser = JsonOutputParser()

# 3. 提示词模板：角色 + 思维链 + 格式约束
prompt = ChatPromptTemplate.from_messages([
    ("system", """你是资深后端架构师，擅长技术方案评估。
【思考要求】
1. 先分步分析方案的优势
2. 再分析潜在风险
3. 最后给出总结论
【输出要求】
严格输出JSON，不要任何多余解释。
{format_instructions}
输出字段：
- reasoning: 数组，推理步骤列表
- conclusion: 字符串，最终结论
- risks: 数组，风险点列表"""),
    ("user", "评估方案：{scheme}")
]).partial(format_instructions=parser.get_format_instructions())

# 4. 组装 LCEL 链
chain = prompt | model | parser

# 5. 运行
if __name__ == "__main__":
    result = chain.invoke({"scheme": "中小团队全面采用微服务架构"})
    print("结论：", result["conclusion"])
    print("\n风险点：")
    for r in result["risks"]:
        print("-", r)
```

---

## 四、最佳实践与避坑

1. **模板变量名严格一致**：`{question}` 和 `invoke({"question": "xxx"})` 的 key 必须完全相同，区分大小写
2. **对话模板顺序正确**：system 在前，user/assistant 交替，和原生消息结构规则一致
3. **JSON 输出双重保障**：既用解析器的 `format_instructions`，也在系统提示里强调「不要多余文字」，提升成功率
4. **生产优先用 Pydantic**：JsonOutputParser 灵活但无校验，Pydantic 强类型适合业务系统
5. **模板独立管理**：复杂提示词可以抽成单独的 `.txt` 或 `.json` 文件，版本化管理，不用写在代码里
6. **避免模板过长**：占位符太多会导致提示词膨胀，增加 token 成本和响应时间

---

要不要我再讲一下 LangChain 的**记忆组件**，把多轮对话和模板、解析器整合起来，实现带上下文的结构化问答？