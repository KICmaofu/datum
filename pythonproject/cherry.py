import requests

API_BASE_URL = "http://localhost:2003"        # 注意端口改为 2003
API_KEY = "cs-sk-54c56fc8-987f-49b2-9560-44f185aa2570"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

# 从 /v1/models 返回的 data 中选择一个 id，例如：
model_id = "deepseek:deepseek-v4-flash"   # 你也可以换成其他 id

data = {
    "model": model_id,
    "messages": [
        {"role": "user", "content": "你好，你是谁？"}
    ],
    "stream": False
}

response = requests.post(f"{API_BASE_URL}/v1/chat/completions", headers=headers, json=data)

if response.status_code == 200:
    result = response.json()
    print("回复内容：", result['choices'][0]['message']['content'])
else:
    print("错误：", response.text)