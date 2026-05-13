diff --git a/main.py b/main.py
index e06d1e9a4eb1548ac35eeafc05945a2ac1fcfab5..41b007a2fd3d97b080badcd0743cc33d63b09bfb 100644
--- a/main.py
+++ b/main.py
@@ -1,26 +1,25 @@
-cat << 'PYEOF' > /home/claude/main_memory.py
 import os
 import uvicorn
 import requests
 import random
 import time
 from fastapi import FastAPI
 from fastapi.responses import HTMLResponse
 from pydantic import BaseModel
 from datetime import datetime, timedelta
 from collections import deque
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
 GROQ_API_KEY = os.getenv("GROQ_KEY", "")
 GROQ_MODEL = "llama-3.3-70b-versatile"
@@ -588,27 +587,25 @@ def get_logs():
 
 @app.post("/memory")
 def add_memory(item: MemoryItem):
     memory_bank.append({
         "tag": item.tag,
         "content": item.content,
         "time": datetime.now().strftime("%Y-%m-%d %H:%M")
     })
     if len(memory_bank) > 100:
         memory_bank.pop(0)
     add_to_log("記憶新增", f"[{item.tag}] {item.content[:30]}")
     return {"status": "Success"}
 
 @app.post("/note")
 def add_note(content: dict):
     add_chen_note(content.get("text", ""))
     return {"status": "Success"}
 
 scheduler = BackgroundScheduler()
 scheduler.add_job(chen_proactive_check, 'interval', hours=2, jitter=1800)
 scheduler.start()
 
 if __name__ == "__main__":
     port = int(os.environ.get("PORT", 8080))
     uvicorn.run(app, host="0.0.0.0", port=port)
-PYEOF
-echo "Done: $(wc -l < /home/claude/main_memory.py) lines"
