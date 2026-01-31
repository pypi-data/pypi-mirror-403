
import requests
import json

def run_ollama_local(model_id: str, user_prompt: str) -> str:
    
    url = "http://localhost:11434/api/generate"
    payload = {
        "model": model_id,
        "prompt": user_prompt,
        "stream": False
    }

    response = requests.post(url, json=payload)

    response.raise_for_status()

    data = response.json()
    return data["response"]

   
def run_ollama_stream(model_id: str, user_prompt: str):
    url = "http://localhost:11434/api/chat"

    payload = {
        "model": model_id,
        "messages": [{"role": "user", "content": user_prompt}],
        "stream": True
    }

    with requests.post(url, json=payload, stream=True) as r:
        r.raise_for_status()
        for line in r.iter_lines():
            if not line:
                continue

            data = json.loads(line.decode("utf-8"))

            # user-friendly yield of token content
            if "message" in data and "content" in data["message"]:
                yield data["message"]["content"]

            if data.get("done"):
                break



