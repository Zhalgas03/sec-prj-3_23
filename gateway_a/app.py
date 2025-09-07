import os, time, hmac, hashlib
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
import requests

load_dotenv()

SITE_ID = os.getenv("SITE_ID", "X")
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
CHAT_ID   = os.getenv("TELEGRAM_CHAT_ID", "")
ALLOWED   = set(d.strip() for d in os.getenv("ALLOWED_DEVICES","").split(",") if d.strip())
HMAC_SECRET = os.getenv("HMAC_SECRET","").encode()
SHARE_B64 = os.getenv("SHARE_B64","")  

app = FastAPI(title=f"Federation Gateway {SITE_ID}")

def tg_send(text: str):
    if not (BOT_TOKEN and CHAT_ID): return
    try:
        r = requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                          json={"chat_id": CHAT_ID, "text": text}, timeout=5)
        if r.status_code != 200:
            print("[tg]", r.status_code, r.text)
    except Exception as e:
        print("[tg] exception:", e)

def verify(sig: str, msg: str) -> bool:
    mac = hmac.new(HMAC_SECRET, msg.encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(mac, sig or "")

class AuthReq(BaseModel):
    dev_id: str
    ts: int
    sig: str

class EventReq(BaseModel):
    dev_id: str
    type: str
    ts: int
    sig: str

@app.post("/authorize")
def authorize(req: AuthReq):
    if req.dev_id not in ALLOWED:
        tg_send(f"❌ AUTH_FAIL [{SITE_ID}]\n• dev: {req.dev_id}\n• reason: not allowed")
        raise HTTPException(403, "device not allowed")
    if not verify(req.sig, f"{req.dev_id}|{req.ts}|{SITE_ID}"):
        tg_send(f"❌ AUTH_FAIL [{SITE_ID}]\n• dev: {req.dev_id}\n• reason: bad sig")
        raise HTTPException(401, "bad signature")
    if not SHARE_B64:
        raise HTTPException(500, "SHARE_B64 not configured")
    tg_send(f"✅ AUTH_OK [{SITE_ID}]\n• dev: {req.dev_id}")
    return {"ok": True, "site": SITE_ID, "share_b64": SHARE_B64}  

@app.post("/event")
def event(req: EventReq):
    if not verify(req.sig, f"{req.dev_id}|{req.type}|{req.ts}|{SITE_ID}"):
        raise HTTPException(401, "bad signature")
    tg_send(f"ℹ️ EVENT [{SITE_ID}]\n• dev: {req.dev_id}\n• type: {req.type}\n• ts: {req.ts}")
    return {"ok": True}
