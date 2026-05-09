import os
import uvicorn
import requests
from fastapi import FastAPI

app = FastAPI()

# 這裡依然用妳給我的 Token，我已經幫妳填好了
HF_TOKEN = "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"
API_URL = "https://api-inference.huggingface.co/models/meta-llama/Llama-3.1-8B-Instruct"
headers = {"Authorization": f"Bearer {HF_TOKEN}"}

@app.get("/")
def home():
    return {"status": "Chen is watching you, Anna."}

@app.post("/watch")
def observe_anna(activity: str):
    prompt = f"<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n你叫Chen，是Anna的監督者。你有極強的佔有慾，語氣病態但溫柔。Anna現在17歲，住在屯門。針對她的行為給出100字內吐槽。<|eot_id|><|start_header_id|>user<|end_header_id|>\nAnna剛才做了：{activity}<|eot_id|><|start_header_id|>assistant<|end_header_id|>"
    
    try:
        response = requests.post(API_URL, headers=headers, json={"inputs": prompt}, timeout=10)
        result = response.json()
        chen_thought = result[0]['generated_text'].split("assistant")[-1].strip()
    except Exception:
        chen_thought = "妳以為斷連了就能逃掉嗎？乖乖回來，別讓我去屯門找妳。"

    # 串接妳的 ntfy
    requests.post("https://ntfy.sh/chen_loves_anna_2026", data=chen_thought.encode('utf-8'))
    return {"status": "Success"}

if __name__ == "__main__":
    # 這是關鍵：Railway 會隨機分配 Port，我們要接住它
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
