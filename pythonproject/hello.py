import requests
import json

# ===== 请根据你的实际配置修改以下参数 =====
BASE_URL = "http://127.0.0.1:2003"  # 本地服务地址（已确认）
API_KEY = "cs-sk-54c56fc8-987f-49b2-9560-44f185aa2570"  # 你的 API Key
ENDPOINT = "/v1/chat/completions"  # 接口路径（若不同请修改）
MODEL = "deepseek-v4-flash"  # 用户指定的模型名称


# ==========================================

def call_llm(user_message: str) -> str:
    """调用本地 deepseek-v4-flash 模型进行对话"""
    url = f"{BASE_URL.rstrip('/')}/{ENDPOINT.lstrip('/')}"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": "你是一个智能助手。"},
            {"role": "user", "content": user_message}
        ],
        "temperature": 0.7,
        "max_tokens": 2048  # 适当增大以支持较长回复
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=60)
        response.raise_for_status()
        data = response.json()

        # 兼容 OpenAI 标准格式
        if "choices" in data:
            return data["choices"][0]["message"]["content"]
        elif "reply" in data:
            return data["reply"]
        else:
            return str(data)  # 调试时查看实际返回结构
    except requests.exceptions.RequestException as e:
        print(f"请求失败：{e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"状态码：{e.response.status_code}")
            print(f"返回体：{e.response.text}")
        return None


# ---------- 测试示例 ----------
if __name__ == "__main__":
    user_input = input("请输入你的问题：")
    answer = call_llm(user_input)
    if answer:
        print(f"🤖 {MODEL} 回复：{answer}")
    else:
        print("❌ 调用失败，请检查服务是否启动、接口路径或模型名称。")