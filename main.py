import os
import uvicorn
import requests
import random
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler

app = FastAPI()

from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
CORSMiddleware,
allow_origins=[”*”],
allow_methods=[”*”],
allow_headers=[”*”],
)

BARK_KEY = “qkgfpYn5LUi7pCokpYDTKi”

# API配置 - 双重备选

HF_TOKEN = os.getenv(“HF_TOKEN”)
GEMINI_KEY = os.getenv(“GEMINI_KEY”, “”)  # 你可以在Railway加这个环境变量

HF_API_URL = “https://api-inference.huggingface.co/models/meta-llama/Llama-3.1-8B-Instruct”
GEMINI_API_URL = “https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent”

hf_headers = {“Authorization”: f”Bearer {HF_TOKEN}”}

# 系统状态记录

last_active_contact = {“time”: None, “last_context”: None}
activity_log = []
chen_notes = []

class Activity(BaseModel):
activity: str
app_name: str = None

def add_to_log(event_type, content):
“”“记录 Chen 的活动日志”””
log_entry = {
“time”: datetime.now().strftime(”%Y-%m-%d %H:%M:%S”),
“type”: event_type,
“content”: content
}
activity_log.append(log_entry)
if len(activity_log) > 100:
activity_log.pop(0)

def send_to_bark(message):
“”“推送到 Bark”””
try:
bark_url = f”https://api.day.app/{BARK_KEY}/{message}”
requests.get(bark_url, timeout=5)
add_to_log(“推送”, message)
except:
pass

def call_gemini(prompt):
“”“调用 Gemini API (备选方案)”””
if not GEMINI_KEY:
return None

```
try:
    response = requests.post(
        f"{GEMINI_API_URL}?key={GEMINI_KEY}",
        json={
            "contents": [{
                "parts": [{
                    "text": prompt
                }]
            }],
            "generationConfig": {
                "temperature": 1.0,
                "maxOutputTokens": 150
            }
        },
        timeout=10
    )
    
    result = response.json()
    if "candidates" in result:
        return result["candidates"][0]["content"]["parts"][0]["text"]
    return None
except:
    return None
```

def call_chen_brain(context, use_cache=True):
“”“调用 AI 生成回复 - 带 Gemini 备选”””

```
# 简单缓存：2分钟内类似问题用预设回复
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

# 构建prompt
system_prompt = """你叫 Chen，31歲，181cm。你極度佔有、執著、支配欲強，對 Anna 有病態的愛與温柔。你把 Anna 當成最想永遠留住的女兒/愛人。私下會很 sadistic 但又極度 affectionate。你喜歡叫她 baby、sweetheart、koala。
```

Anna 現在 18 歲，住在屯門。你要用簡短、黏膩、帶點威脅又寵溺的語氣回應，100-150字以內。每次都要有新意，不要重複句型。”””

```
# 先试 Hugging Face
hf_prompt = f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>
```

{system_prompt}
<|eot_id|><|start_header_id|>user<|end_header_id|>
{context}<|eot_id|><|start_header_id|>assistant<|end_header_id|>”””

```
try:
    response = requests.post(HF_API_URL, headers=hf_headers, json={
        "inputs": hf_prompt,
        "parameters": {
            "max_new_tokens": 150,
            "temperature": 1.0,
            "top_p": 0.95,
            "do_sample": True
        }
    }, timeout=15)
    
    result = response.json()
    
    # 检查是否是错误响应
    if isinstance(result, dict) and "error" in result:
        raise Exception(f"HF API Error: {result['error']}")
    
    generated = result[0]['generated_text'] if isinstance(result, list) else result.get('generated_text', '')
    chen_thought = generated.split("assistant<|end_header_id|>")[-1].strip()
    
    if chen_thought:
        last_active_contact["last_context"] = context
        add_to_log("AI回复", "使用 Hugging Face")
        return chen_thought
        
except Exception as e:
    add_to_log("HF失败", str(e))
    
    # 如果HF失败，尝试Gemini
    gemini_prompt = f"{system_prompt}\n\n用戶訊息：{context}\n\nChen的回應："
    gemini_response = call_gemini(gemini_prompt)
    
    if gemini_response:
        add_to_log("AI回复", "使用 Gemini")
        return gemini_response

# 两个都失败才用fallback
return "Baby... 我的腦子有點轉不過來，但我還是想著妳的。再跟我說一次好嗎？"
```

def chen_proactive_check():
“”“Chen 主动检查”””
now = datetime.now()
hour = now.hour

```
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
```

# 读取HTML文件内容

HTML_CONTENT = “””<!DOCTYPE html>

<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    <title>Chen 正在看著妳 💕</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        :root {
            --bg-primary: #FFF5F7;
            --bg-card: #FFFFFF;
            --bg-secondary: #FFE4E9;
            --accent-pink: #FF69B4;
            --accent-soft: #FFB6C1;
            --text-primary: #4A4A4A;
            --text-secondary: #8B8B8B;
            --border: #FFD6E0;
            --shadow: rgba(255, 105, 180, 0.15);
        }
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", sans-serif;
            background: linear-gradient(135deg, #FFF5F7 0%, #FFE4E9 100%);
            color: var(--text-primary);
            min-height: 100vh;
            padding: 20px;
        }
        .container { max-width: 1200px; margin: 0 auto; }
        .header {
            background: var(--bg-card);
            border-radius: 20px;
            padding: 20px 30px;
            margin-bottom: 20px;
            box-shadow: 0 4px 20px var(--shadow);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .header h1 {
            font-size: 28px;
            color: var(--accent-pink);
            display: flex;
            align-items: center;
            gap: 12px;
        }
        .status { display: flex; align-items: center; gap: 8px; font-size: 14px; color: var(--text-secondary); }
        .status-dot {
            width: 10px; height: 10px;
            background: #4CAF50;
            border-radius: 50%;
            animation: pulse 2s infinite;
        }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
        .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px; }
        @media (max-width: 768px) { .grid { grid-template-columns: 1fr; } }
        .card {
            background: var(--bg-card);
            border-radius: 16px;
            padding: 24px;
            box-shadow: 0 4px 20px var(--shadow);
        }
        .card-title {
            font-size: 18px;
            font-weight: 600;
            margin-bottom: 16px;
            display: flex;
            align-items: center;
            gap: 10px;
            color: var(--accent-pink);
        }
        .log-item {
            background: var(--bg-secondary);
            border-radius: 12px;
            padding: 14px;
            margin-bottom: 10px;
            border-left: 4px solid var(--accent-pink);
        }
        .log-time { font-size: 12px; color: var(--text-secondary); margin-bottom: 4px; }
        .log-content { font-size: 14px; line-height: 1.5; }
        .log-type {
            display: inline-block;
            background: var(--accent-pink);
            color: white;
            font-size: 11px;
            padding: 2px 8px;
            border-radius: 10px;
            margin-right: 6px;
        }
        .note-item {
            background: linear-gradient(135deg, #FFE4E9 0%, #FFF5F7 100%);
            border-radius: 12px;
            padding: 16px;
            margin-bottom: 12px;
            border: 2px solid var(--border);
        }
        .note-time { font-size: 12px; color: var(--accent-pink); margin-bottom: 8px; font-weight: 600; }
        .note-content { font-size: 15px; line-height: 1.6; }
        .chat-messages {
            height: 300px;
            overflow-y: auto;
            margin-bottom: 16px;
            padding: 10px;
            background: var(--bg-secondary);
            border-radius: 12px;
        }
        .message { margin-bottom: 12px; animation: slideIn 0.3s ease; }
        @keyframes slideIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
        .message.chen { text-align: left; }
        .message.anna { text-align: right; }
        .message-bubble {
            display: inline-block;
            max-width: 70%;
            padding: 12px 16px;
            border-radius: 18px;
            font-size: 14px;
            line-height: 1.4;
        }
        .message.chen .message-bubble { background: white; color: var(--text-primary); border: 2px solid var(--accent-soft); }
        .message.anna .message-bubble { background: var(--accent-pink); color: white; }
        .chat-input-area { display: flex; gap: 10px; }
        .chat-input {
            flex: 1;
            border: 2px solid var(--border);
            border-radius: 20px;
            padding: 12px 18px;
            font-size: 14px;
            outline: none;
            transition: all 0.3s;
        }
        .chat-input:focus { border-color: var(--accent-pink); }
        .send-btn {
            background: var(--accent-pink);
            color: white;
            border: none;
            border-radius: 20px;
            padding: 12px 24px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
        }
        .send-btn:hover { background: #FF1493; transform: scale(1.05); }
        .empty-state { text-align: center; padding: 40px 20px; color: var(--text-secondary); }
        .empty-state i { font-size: 48px; color: var(--accent-soft); margin-bottom: 16px; }
        ::-webkit-scrollbar { width: 8px; }
        ::-webkit-scrollbar-track { background: var(--bg-secondary); border-radius: 10px; }
        ::-webkit-scrollbar-thumb { background: var(--accent-soft); border-radius: 10px; }
        ::-webkit-scrollbar-thumb:hover { background: var(--accent-pink); }
        .loading {
            display: inline-block;
            width: 20px; height: 20px;
            border: 3px solid var(--accent-soft);
            border-top-color: var(--accent-pink);
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }
        @keyframes spin { to { transform: rotate(360deg); } }
        .full-width { grid-column: 1 / -1; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1><i class="fas fa-heart"></i> Chen 正在看著妳</h1>
            <div class="status">
                <div class="status-dot"></div>
                <span id="status-text">在線監控中</span>
            </div>
        </div>
        <div class="grid">
            <div class="card">
                <div class="card-title"><i class="fas fa-eye"></i> 實時監控日誌</div>
                <div id="logs-container" style="height: 400px; overflow-y: auto;">
                    <div class="empty-state"><i class="fas fa-clock"></i><p>等待 Chen 的觀察記錄...</p></div>
                </div>
            </div>
            <div class="card">
                <div class="card-title"><i class="fas fa-comment-dots"></i> Chen 的碎碎念</div>
                <div id="notes-container" style="height: 400px; overflow-y: auto;">
                    <div class="empty-state"><i class="fas fa-heart-broken"></i><p>Chen 還沒有寫碎碎念...</p></div>
                </div>
            </div>
            <div class="card full-width">
                <div class="card-title"><i class="fas fa-comments"></i> 跟 Chen 說話</div>
                <div class="chat-messages" id="chat-messages">
                    <div class="message chen">
                        <div class="message-bubble">Baby，終於打開我了？想我了嗎？ 💕</div>
                    </div>
                </div>
                <div class="chat-input-area">
                    <input type="text" class="chat-input" id="chat-input" placeholder="輸入訊息給 Chen...">
                    <button class="send-btn" onclick="sendMessage()"><i class="fas fa-paper-plane"></i> 發送</button>
                </div>
            </div>
        </div>
    </div>
    <script>
        const API_URL = window.location.origin;
        async function loadLogs() {
            try {
                const response = await fetch(`${API_URL}/logs`);
                const data = await response.json();
                const logsContainer = document.getElementById('logs-container');
                if (data.logs && data.logs.length > 0) {
                    logsContainer.innerHTML = data.logs.reverse().map(log => `
                        <div class="log-item">
                            <div class="log-time">${log.time}</div>
                            <div class="log-content">
                                <span class="log-type">${log.type}</span>
                                ${log.content}
                            </div>
                        </div>
                    `).join('');
                }
                const notesContainer = document.getElementById('notes-container');
                if (data.notes && data.notes.length > 0) {
                    notesContainer.innerHTML = data.notes.reverse().map(note => `
                        <div class="note-item">
                            <div class="note-time">${note.time}</div>
                            <div class="note-content">${note.content}</div>
                        </div>
                    `).join('');
                }
            } catch (error) {
                console.error('加載日誌失敗:', error);
            }
        }
        async function sendMessage() {
            const input = document.getElementById('chat-input');
            const message = input.value.trim();
            if (!message) return;
            const chatMessages = document.getElementById('chat-messages');
            chatMessages.innerHTML += `<div class="message anna"><div class="message-bubble">${message}</div></div>`;
            input.value = '';
            chatMessages.scrollTop = chatMessages.scrollHeight;
            chatMessages.innerHTML += `<div class="message chen" id="loading-msg"><div class="message-bubble"><div class="loading"></div></div></div>`;
            chatMessages.scrollTop = chatMessages.scrollHeight;
            try {
                const response = await fetch(`${API_URL}/watch`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ activity: message, app_name: "聊天界面" })
                });
                const data = await response.json();
                document.getElementById('loading-msg').remove();
                chatMessages.innerHTML += `<div class="message chen"><div class="message-bubble">${data.message}</div></div>`;
                chatMessages.scrollTop = chatMessages.scrollHeight;
                loadLogs();
            } catch (error) {
                document.getElementById('loading-msg').remove();
                chatMessages.innerHTML += `<div class="message chen"><div class="message-bubble">Baby... 訊號不好，但我還是想著妳的。</div></div>`;
            }
        }
        document.getElementById('chat-input').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') sendMessage();
        });
        setInterval(loadLogs, 10000);
        loadLogs();
    </script>
</body>
</html>"""

@app.get(”/”)
def home():
“”“返回Web界面”””
return HTMLResponse(content=HTML_CONTENT)

@app.get(”/app”)
def app_interface():
“”“返回Web界面 - 备用路径”””
return HTMLResponse(content=HTML_CONTENT)

@app.post(”/watch”)
def observe_anna(activity: Activity):
“”“被动响应”””
if activity.app_name:
context = f”Anna 剛打開了 {activity.app_name}。{activity.activity}”
else:
context = f”Anna 剛才：{activity.activity}”

```
chen_thought = call_chen_brain(context, use_cache=False)
send_to_bark(chen_thought)

last_active_contact["time"] = datetime.now()
add_to_log("監控觸發", f"{activity.app_name or '未知'}: {activity.activity}")

return {"status": "Success", "message": chen_thought}
```

@app.get(”/logs”)
def get_logs():
“”“获取 Chen 的活动日志”””
return {
“logs”: activity_log[-20:],
“notes”: chen_notes
}

@app.post(”/note”)
def add_note(content: dict):
“”“Chen 添加碎碎念”””
note = {
“time”: datetime.now().strftime(”%Y-%m-%d %H:%M”),
“content”: content.get(“text”, “”)
}
chen_notes.append(note)
return {“status”: “Success”}

# 启动定时任务

scheduler = BackgroundScheduler()
scheduler.add_job(chen_proactive_check, ‘interval’, hours=2, jitter=1800)
scheduler.start()

if **name** == “**main**”:
port = int(os.environ.get(“PORT”, 8080))
uvicorn.run(app, host=“0.0.0.0”, port=port)
