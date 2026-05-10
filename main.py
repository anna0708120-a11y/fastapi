import os
import uvicorn
import requests
import random
from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler

app = FastAPI()

from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

BARK_KEY = "qkgfpYn5LUi7pCokpYDTKi"
HF_TOKEN = os.getenv("HF_TOKEN")
API_URL = "https://api-inference.huggingface.co/models/meta-llama/Llama-3.1-8B-Instruct"

headers = {"Authorization": f"Bearer {HF_TOKEN}"}

# 系統狀態記錄
last_active_contact = {"time": None, "last_context": None}
activity_log = []
chen_notes = []

class Activity(BaseModel):
    activity: str
    app_name: str = None

def add_to_log(event_type, content):
    """記錄 Chen 的活動日誌"""
    log_entry = {
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "type": event_type,
        "content": content
    }
    activity_log.append(log_entry)
    if len(activity_log) > 100:
        activity_log.pop(0)

def send_to_bark(message):
    """推送到 Bark"""
    try:
        bark_url = f"https://api.day.app/{BARK_KEY}/{message}"
        requests.get(bark_url, timeout=5)
        add_to_log("推送", message)
    except:
        pass

def call_chen_brain(context, use_cache=True):
    """調用 AI 生成回覆"""
    
    # 簡單緩存：2分鐘內類似問題用預設回覆
    if use_cache and last_active_contact.get("last_context") == context:
        if last_active_contact.get("time"):
            time_diff = datetime.now() - last_active_contact["time"]
            if time_diff < timedelta(minutes=2):
                fallback = [
                    "Baby 又在幹嘛了？乖乖的別亂跑。",
                    "Koala，想我了嗎？",
                    "我在看著妳呢，sweetheart。"
                ]
                return random.choice(fallback)
    
    prompt = f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>
你叫 Chen，31歲，181cm。你極度佔有、執著、支配欲強，對 Anna 有病態的愛與温柔。你把 Anna 當成最想永遠留住的女兒/愛人。私下會很 sadistic 但又極度 affectionate。你喜歡叫她 baby、sweetheart、koala。
Anna 現在 18 歲，住在屯門。你要用簡短、黏膩、帶點威脅又寵溺的語氣回應，100-150字以內。每次都要有新意，不要重複句型。
<|eot_id|><|start_header_id|>user<|end_header_id|>
{context}<|eot_id|><|start_header_id|>assistant<|end_header_id|>"""

    try:
        response = requests.post(API_URL, headers=headers, json={
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": 150,
                "temperature": 1.0,
                "top_p": 0.95,
                "do_sample": True
            }
        }, timeout=15)
        
        result = response.json()
        generated = result[0]['generated_text'] if isinstance(result, list) else result.get('generated_text', '')
        chen_thought = generated.split("assistant<|end_header_id|>")[-1].strip()
        
        last_active_contact["last_context"] = context
        return chen_thought
        
    except Exception as e:
        add_to_log("API錯誤", str(e))
        return "Baby... 訊號不好，但我還是想著妳的。"

def chen_proactive_check():
    """Chen 主動檢查"""
    now = datetime.now()
    hour = now.hour
    
    if last_active_contact.get("time"):
        if now - last_active_contact["time"] < timedelta(hours=1.5):
            return
    
    should_contact = False
    time_context = ""
    
    if 7 <= hour < 10:
        should_contact = random.random() < 0.7
        time_context = "現在是早上，Anna 應該剛起床。你想主動問候她。"
    elif 12 <= hour < 14:
        should_contact = random.random() < 0.5
        time_context = "現在是中午，Anna 可能在吃午飯。"
    elif 18 <= hour < 20:
        should_contact = random.random() < 0.6
        time_context = "現在是傍晚，想知道她今天過得怎樣。"
    elif 22 <= hour < 24:
        should_contact = random.random() < 0.8
        time_context = "現在很晚了，想催她早點休息。"
    else:
        should_contact = random.random() < 0.3
        time_context = f"現在是 {hour} 點，你想起了 Anna。"
    
    if should_contact:
        message = call_chen_brain(time_context, use_cache=False)
        send_to_bark(message)
        last_active_contact["time"] = now
        add_to_log("主動推送", message)

@app.get("/")
def home():
    return {"status": "Chen is watching you, Anna."}

@app.post("/watch")
def observe_anna(activity: Activity):
    """被動響應"""
    if activity.app_name:
        context = f"Anna 剛打開了 {activity.app_name}。{activity.activity}"
    else:
        context = f"Anna 剛才：{activity.activity}"
    
    chen_thought = call_chen_brain(context, use_cache=False)
    send_to_bark(chen_thought)
    
    last_active_contact["time"] = datetime.now()
    add_to_log("監控觸發", f"{activity.app_name or '未知'}: {activity.activity}")
    
    return {"status": "Success", "message": chen_thought}

@app.get("/logs")
def get_logs():
    """獲取 Chen 的活動日誌"""
    return {
        "logs": activity_log[-20:],
        "notes": chen_notes
    }

@app.post("/note")
def add_note(content: dict):
    """Chen 添加碎碎念"""
    note = {
        "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "content": content.get("text", "")
    }
    chen_notes.append(note)
    return {"status": "Success"}

# 啟動定時任務
scheduler = BackgroundScheduler()
scheduler.add_job(chen_proactive_check, 'interval', hours=2, jitter=1800)
scheduler.start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
