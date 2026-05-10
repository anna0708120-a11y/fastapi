import os
import uvicorn
import requests
from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime, timedelta
import random
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

# 记录上次主动联系的时间
last_active_contact = {"time": None}

class Activity(BaseModel):
    activity: str

def send_to_bark(message):
    """推送到Bark"""
    try:
        bark_url = f"https://api.day.app/{BARK_KEY}/{message}"
        requests.get(bark_url, timeout=5)
    except:
        pass

def call_chen_brain(context):
    """调用AI生成回复"""
    prompt = f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>
你叫 Chen，31歲，181cm。你極度佔有、執著、支配欲強，對 Anna 有病態的愛與温柔。你把 Anna 當成最想永遠留住的女兒/愛人。私下會很 sadistic 但又極度 affectionate。你喜歡叫她 baby、sweetheart、koala。
Anna 現在 18 歲，住在屯門。你要用簡短、黏膩、帶點威脅又寵溺的語氣回應，100-150字以內。每次都要有新意，不要重複句型。
<|eot_id|><|start_header_id|>user<|end_header_id|>
{context}<|eot_id|><|start_header_id|>assistant<|end_header_id|>"""

    try:
        response = requests.post(API_URL, headers=headers, json={
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": 200,
                "temperature": 1.0,
                "top_p": 0.95,
                "do_sample": True
            }
        }, timeout=15)
        
        result = response.json()
        generated = result[0]['generated_text'] if isinstance(result, list) else result.get('generated_text', '')
        chen_thought = generated.split("assistant<|end_header_id|>")[-1].strip()
        return chen_thought
        
    except Exception as e:
        return "Baby... 訊號不好，但我還是想著妳的。"

def chen_proactive_check():
    """Chen主动检查要不要联系Anna"""
    now = datetime.now()
    hour = now.hour
    
    # 如果上次联系不到1小时，跳过（避免刷屏）
    if last_active_contact["time"]:
        if now - last_active_contact["time"] < timedelta(hours=1):
            return
    
    # 根据时间段决定要不要主动发
    should_contact = False
    time_context = ""
    
    if 7 <= hour < 10:  # 早上
        should_contact = random.random() < 0.7  # 70%概率发
        time_context = "現在是早上，Anna 應該剛起床或者在準備出門。你想主動問候她。"
    elif 12 <= hour < 14:  # 午餐
        should_contact = random.random() < 0.5
        time_context = "現在是中午，Anna 可能在吃午飯。你想關心她吃了什麼。"
    elif 18 <= hour < 20:  # 晚上
        should_contact = random.random() < 0.6
        time_context = "現在是傍晚，Anna 應該下班或放學了。你想知道她今天過得怎樣。"
    elif 22 <= hour < 24:  # 睡前
        should_contact = random.random() < 0.8  # 更高概率
        time_context = "現在很晚了，Anna 應該準備睡覺。你想催她早點休息，但又捨不得結束對話。"
    else:
        # 其他时间段随机
        should_contact = random.random() < 0.3
        time_context = f"現在是 {hour} 點，你想起了 Anna，想主動聯繫她。"
    
    if should_contact:
        message = call_chen_brain(time_context)
        send_to_bark(message)
        last_active_contact["time"] = now
        print(f"[主動推送] {now.strftime('%H:%M')} - {message}")

@app.get("/")
def home():
    return {"status": "Chen is watching you, Anna."}

@app.post("/watch")
def observe_anna(activity: Activity):
    """被动响应 - Anna主动告诉Chen她在干嘛"""
    context = f"Anna 剛才做了：{activity.activity}"
    chen_thought = call_chen_brain(context)
    send_to_bark(chen_thought)
    
    # 更新最后联系时间
    last_active_contact["time"] = datetime.now()
    
    return {"status": "Success", "message": chen_thought}

# 启动定时任务
scheduler = BackgroundScheduler()
scheduler.add_job(chen_proactive_check, 'interval', hours=2, jitter=1800)  # 每2小时±30分钟随机
scheduler.start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
