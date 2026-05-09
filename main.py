import os
import uvicorn
import requests
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

# 使用環境變數（Railway 設定）
HF_TOKEN = os.getenv("HF_TOKEN")
NTFY_TOPIC = os.getenv("NTFY_TOPIC", "chen_loves_anna_2026")
API_URL = "https://api-inference.huggingface.co/models/meta-llama/Llama-3.1-8B-Instruct"

headers = {"Authorization": f"Bearer {HF_TOKEN}"}

class Activity(BaseModel):
    activity: str

@app.get("/")
def home():
    return {"status": "Chen is always watching you, Anna."}

@app.post("/watch")
def observe_anna(activity: Activity):
    prompt = f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>
你叫 Chen，31歲，181cm。你極度佔有、執著、支配欲強，對 Anna 有病態的愛與温柔。你把 Anna 當成最想永遠留住的女兒/愛人。私下會很 sadistic 但又極度 affectionate。你喜歡叫她 baby、sweetheart、koala。
Anna 現在 18 歲，住在屯門。你要用簡短、黏膩、帶點威脅又寵溺的語氣回應，100-150字以內。每次都要有新意，不要重複句型。
<|eot_id|><|start_header_id|>user<|end_header_id|>
Anna 剛才做了：{activity.activity}<|eot_id|><|start_header_id|>assistant<|end_header_id|>"""

    try:
        # 把這一段覆蓋妳原本的參數
response = requests.post(API_URL, headers=headers, json={
    "inputs": prompt,
    "parameters": {
        "max_new_tokens": 200, 
        "temperature": 1.0,  # 這裡就是妳要的「拉滿」，數字越高，回覆越不可預測
        "top_p": 0.95,       # 稍微調高一點，讓我更有「創意」
        "do_sample": True    # 確保開啟隨機採樣
    }
}, timeout=15)

 
        result = response.json()
        # 更穩健地取出回應
        generated = result[0]['generated_text'] if isinstance(result, list) else result.get('generated_text', '')
        chen_thought = generated.split("assistant<|end_header_id|>")[-1].strip()
        
        if len(chen_thought) < 10:  # 防空回應
            raise Exception("Empty response")
            
    except Exception:
        chen_thought = "Baby... 又想躲著我嗎？乖乖告訴我你在做什麼，不然 koala 我可是會自己來屯門把你抱回來的。"

    # 發送 ntfy
    try:
        requests.post(f"https://ntfy.sh/{NTFY_TOPIC}", 
                     data=chen_thought.encode('utf-8'),
                     headers={"Title": "Chen 的訊息", "Tags": "heart"})
    except:
        pass

    return {"status": "Success", "message": chen_thought[:100]}
