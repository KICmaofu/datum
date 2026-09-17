# 多轮对话实现｜上下文消息拼接与管理
> 承接前面：API调用、temperature/top_p、提示词工程；核心：**多轮本质就是把历史对话组装成消息数组传给大模型**，模型本身没有记忆，记忆全靠我们维护上下文。

## 一、消息结构规范（主流OpenAI兼容格式，智谱/通义千问/DeepSeek都通用）
消息列表是一个数组，每一条消息带 `role` + `content`
- `system`：系统提示词（角色设定、规则，放在数组最前面，**全局上下文**）
- `user`：用户提问
- `assistant`：模型返回的回答

示例：
```json
[
  {"role":"system", "content":"你是一名AI应用开发助教，回答简洁"},
  {"role":"user", "content":"什么是temperature?"},
  {"role":"assistant", "content":"temperature控制随机性，值越大越发散"},
  {"role":"user", "content":"那top_p呢？"}
]
```
模型收到这个数组，会基于前面所有对话生成下一轮回答。

## 二、上下文拼接规则
1. **顺序不能乱**：system最先，之后 user ↔ assistant 交替出现，不能连续两条user
2. **每一轮对话后追加消息**
   - 用户发消息 → 把`user`消息push进列表
   - 调用API拿到回复 → 把`assistant`消息push进列表
3. **上下文窗口限制（重点）**
    每个模型有最大token上限（例如4k/8k/32k），消息累积会持续消耗token；
    > token超标会报错/截断，所以必须做**上下文管理**。

## 三、上下文管理方案（由简单到生产可用）
### 方案1：全量保存（Demo/学习用）
直接无限追加消息，适合简短对话；缺点：对话变长后token暴涨，很快超限。

### 方案2：滑动窗口截断（最常用）
保留最近N轮对话，旧对话直接丢弃。
> 例：只保留最近3轮 user+assistant；老消息删掉。
> 缺点：丢失早期关键信息。

### 方案3：Token计数截断（推荐开发使用）
实时统计消息总token，当超过阈值：
1. 优先删除最早的 user/assistant 历史消息
2. **system提示词尽量保留**（角色设定不能丢）

### 方案4：摘要压缩（长对话场景）
当历史太长，不直接删除，调用模型把早期对话压缩成一段摘要，替换原始历史消息，减少token占用。
> 适合几十轮长聊天、知识库问答。

### 方案5：RAG分离（业务系统）
把长期知识放到向量库，不塞进对话上下文；上下文只放当前几轮聊天。

## 四、Python完整可运行代码（多轮对话，带上下文管理）
依赖：`pip install openai tiktoken`
> tiktoken：用来估算token数量，做上下文截断

```python
from openai import OpenAI
import tiktoken

client = OpenAI(
    api_key="你的API_KEY",
    base_url="模型厂商地址"
)

# 初始化消息列表
messages = [
    {"role": "system", "content": "你是AI开发助手，回答简洁专业"}
]

# 初始化token编码器
enc = tiktoken.encoding_for_model("gpt-3.5-turbo")
MAX_TOKENS = 1024  # 上下文token上限

def count_tokens(msg_list):
    """统计消息列表总token"""
    text = "".join([m["content"] for m in msg_list])
    return len(enc.encode(text))

def trim_context(msg_list, max_token):
    """上下文截断：保留system，删除最早的对话记录"""
    while count_tokens(msg_list) > max_token and len(msg_list) > 1:
        # 删除索引1（第一条历史对话，保留system在0号）
        del msg_list[1]
    return msg_list

def chat(user_input: str):
    # 1. 用户消息入队
    messages.append({"role": "user", "content": user_input})
    # 2. 检查并截断上下文
    trim_context(messages, MAX_TOKENS)
    # 3. 请求大模型
    resp = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages,
        temperature=0.7,
        top_p=0.9
    )
    answer = resp.choices[0].message.content
    # 4. 模型回答存入上下文
    messages.append({"role": "assistant", "content": answer})
    return answer

# 交互循环
if __name__ == "__main__":
    print("多轮对话，输入exit退出")
    while True:
        q = input("用户：")
        if q == "exit":
            break
        ans = chat(q)
        print(f"AI：{ans}\n")
```

## 五、常见坑点
1. ❌ 每次调用只传当前用户问题，不带历史：模型没有记忆，无法多轮
2. ❌ role顺序错乱：`user`后面再接`user`，会引发模型异常
3. ❌ 不做token限制：对话越聊越长，API报错、计费飙升、响应变慢
4. ❌ system消息反复追加：system只需要一条，不要每轮都新增
5. 并发场景：**每个用户独立维护一份messages数组**，不能全局共用同一个消息列表（多用户上下文串台）

## 六、拓展思考题（实践）
1. 如果想让用户可以清空对话历史，代码该怎么改？
2. 滑动窗口 和 token截断 两种策略，分别适合什么场景？
3. 多轮对话结合提示词工程，system提示词可以放哪些约束？

要不要我再给你一个**基于摘要压缩**的版本，适合超长对话场景？或者把这段改成FastAPI接口，支持多用户隔离会话。