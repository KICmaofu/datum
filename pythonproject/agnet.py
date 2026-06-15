import requests

headers = {
    "Authorization": "Bearer cs-sk-54c56fc8-987f-49b2-9560-44f185aa2570"
}
res = requests.get("http://127.0.0.1:2003/v1/agents", headers=headers)
agents = res.json()["data"]
for agent in agents:
    print(f"智能体名称：{agent['name']}，ID：{agent['id']}")