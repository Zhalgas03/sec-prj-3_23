import os, time, base64, hmac, hashlib, requests
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(dotenv_path=Path("device/.env"))

DEV_ID = os.getenv("DEVICE_ID", "esp32-001")
GW1 = os.getenv("PRIMARY_GATEWAY_URL", "http://127.0.0.1:8080")
GW2 = os.getenv("SECONDARY_GATEWAY_URL", "http://127.0.0.1:8081")
HMAC_SECRET = os.getenv("HMAC_SECRET","").encode()

def sign(msg: str) -> str:
    return hmac.new(HMAC_SECRET, msg.encode(), hashlib.sha256).hexdigest()

def post_json(url, data):
    r = requests.post(url, json=data, timeout=5); r.raise_for_status(); return r.json()

def authorize(gw, site):
    ts = int(time.time())
    body = post_json(f"{gw}/authorize", {"dev_id": DEV_ID, "ts": ts, "sig": sign(f"{DEV_ID}|{ts}|{site}")})
    assert body.get("ok") and body.get("share_b64")
    print(f"[{site}] AUTH_OK"); return body["share_b64"]

if __name__ == "__main__":
    a = authorize(GW1, "A"); b = authorize(GW2, "B")
    key = bytes(x ^ y for x,y in zip(base64.b64decode(a), base64.b64decode(b)))
    print("RECONSTRUCTED_KEY_B64:", base64.b64encode(key).decode())
    print("MOUNT_OK")
