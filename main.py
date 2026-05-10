import os
import uvicorn
import requests
import json
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

# 记录系统状态
last_active_contact = {"time": None}
activity_log = []  # Chen的观察日志
chen_notes = []    # Chen的碎碎念

class Activity(BaseModel):
    activity: str
    app_name: str = None  # 可选：告诉Chen是哪个app

def add_to_log(event_type, content):
    """记录Chen的活动日志"""
    log_entry = {
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "type": event_type,
        "content": content
    }
    activity_log.append(log_entry)
    # 只保留最近100条
    if len(activity_log) > 100:
        activity_log.pop(0)

def send_to_bark(message):
    """推送到Bark"""
    try:
        bark_url = f"https://api.day.app/{BARK_KEY}/{message}"
        requests.get(bark_url, timeout=5)
        add_to_log("推送", message)
    except:
        pass

def call_chen_brain(context, use_cache=True):
    """调用AI生成回复 - 优化版"""
    
    # 简单缓存：如果2分钟内问过类似的问题，直接用预设回复
    if use_cache and last_active_contact.get("last_context") == context:
        time_diff = datetime.now() - last_active_contact.get("time", datetime.min)
        if time_diff < timedelta(minutes=2):
            fallback_responses = [
                "Baby又在幹嘛了？乖乖的別亂跑。",
                "Koala，想我了嗎？",
                "我在看著妳呢，sweetheart。"
            ]
            return random.choice(fallback_responses)
    
    prompt = f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>
你叫 Chen，31歲，181cm。你極度佔有、執著、支​​​​​​​​​​​​​​​​
