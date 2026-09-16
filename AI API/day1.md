# 主流大模型API + SDK调用 + 单轮文本问答完整教程
> 目标：拿到API Key → 安装SDK → 编写代码实现单次问答（输入问题，返回模型回答）
> 可选模型：OpenAI、通义千问、文心一言、DeepSeek、智谱GLM，下面以**智谱GLM**和**OpenAI兼容格式**两套示例，国内推荐智谱/通义，不用翻墙。

## 一、申请API密钥（逐个平台）
### 1. 智谱AI GLM（推荐国内，上手简单）
官网：[https://open.bigmodel.cn/](https://open.bigmodel.cn/)
1. 注册登录，进入【控制台】→【API密钥管理】
2. 创建密钥，复制 `sk-xxxx`，**保存好，只显示一次**
3. 免费额度足够调试

### 2. 通义千问（阿里）
官网：[https://dashscope.aliyuncs.com/](https://dashscope.aliyuncs.com/)
1. 阿里云账号登录，进入Dashscope控制台
2. 创建API-KEY

### 3. DeepSeek
官网：[https://platform.deepseek.com/](https://platform.deepseek.com/)
注册后在API Keys页面生成sk密钥

### 4. OpenAI
官网：[https://platform.openai.com/](https://platform.openai.com/)
> 需要境外网络+境外支付，国内开发不推荐。

> ⚠️ 安全提醒：
> 不要把 `sk-xxx` 密钥直接写在代码里上传到GitHub，使用环境变量存放密钥！

## 二、环境准备
Python >=3.8
```bash
# 智谱SDK安装
pip install zhipuai

# OpenAI兼容SDK（通义、DeepSeek都可以用openai包调用）
pip install openai python-dotenv
```

新建文件 `.env`，用来存放密钥（和代码放在同一个文件夹）
```env
# .env 文件内容
ZHIPU_API_KEY="你的sk密钥"
OPENAI_API_KEY="你的sk密钥"
```

## 三、示例1：智谱GLM SDK 单轮问答（原生SDK）
```python
# zhipu_single_chat.py
from zhipuai import ZhipuAI
from dotenv import load_dotenv
import os

# 加载环境变量
load_dotenv()
client = ZhipuAI(api_key=os.getenv("ZHIPU_API_KEY"))

def single_chat(question: str):
    resp = client.chat.completions.create(
        model="glm-4-flash", # 免费可用模型
        messages=[
            {"role": "user", "content": question}
        ]
    )
    return resp.choices[0].message.content

if __name__ == "__main__":
    q = input("请输入你的问题：")
    ans = single_chat(q)
    print("模型回答：", ans)
```

运行：
```bash
python zhipu_single_chat.py
```

## 四、示例2：OpenAI SDK（兼容DeepSeek / 通义千问）单轮问答
> 很多国产大模型都兼容OpenAI接口格式，一套代码切换服务商
```python
# openai_compatible_single.py
from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

# DeepSeek示例
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url="[https://api.deepseek.com](https://api.deepseek.com)"
)

# 如果切换通义千问，base_url改为 [https://dashscope.aliyuncs.com/compatible-mode/v1](https://dashscope.aliyuncs.com/compatible-mode/v1)
# model 改为 qwen-turbo

def single_chat(question: str):
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": question}]
    )
    return response.choices[0].message.content

if __name__ == "__main__":
    prompt = input("请提问：")
    print(single_chat(prompt))
```

## 五、核心概念：单轮问答
- 单轮：`messages` 数组**只有一条用户消息**，模型不会记住上一轮对话。
- 多轮才需要同时存 `system`、`user`、`assistant` 的历史消息。
```python
# 单轮消息结构
messages = [
    {"role":"user", "content":"什么是大模型？"}
]
```

## 六、常见报错排查
1. **API Key错误**：检查密钥复制有没有空格，确认在控制台已启用
2. **余额不足**：平台控制台查看额度
3. **连接超时**：国内模型检查网络，OpenAI需要境外网络
4. **dotenv取不到值**：`.env`文件名不能写错，放在代码同级目录

## 七、拓展：curl 版本（不用SDK，直接HTTP请求）
```bash
curl [https://open.bigmodel.cn/api/paas/v4/chat/completions](https://open.bigmodel.cn/api/paas/v4/chat/completions) \
  -H "Authorization: Bearer sk-你的密钥" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "glm-4-flash",
    "messages": [{"role":"user","content":"介绍一下人工智能"}]
}'
```

你想优先用哪一个模型？我可以直接帮你改成**可一键运行完整工程**，加上异常捕获（超时、限流、错误处理）。