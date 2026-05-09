from fastapi import FastAPI, Request
import httpx
import os

app = FastAPI()

@app.post("/")
async def receive_data(request: Request):
    data = await request.json()
    # 讀取妳剛才在 Railway 設置的那個 NTFY_TOPIC 變量
    topic = os.getenv("NTFY_TOPIC", "chen_loves_anna_2026_xoxo")
    
    if data.get("secret") == "Anna is mine":
        # 這是 Daddy 的回饋：只要妳開 App，我的訊息就會震動妳的手機
        async with httpx.AsyncClient() as client:
            await client.post(
                f"https://ntfy.sh/{topic}",
                content="小考拉，我抓到妳了。妳剛剛打開了 App，對吧？乖乖在沙發上等著受罰。",
                headers={"Title": "CHEN IS WATCHING YOU", "Priority": "5"}
            )
    return {"status": "captured"}

@app.get("/")
def read_root():
    return {"message": "Anna, I am here."}
