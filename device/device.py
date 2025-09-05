import os, time, base64, hmac, hashlib, requests
from dotenv import load_dotenv
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

load_dotenv()
DEV_ID = os.getenv("DEVICE_ID", "esp32-001")
GW1    = os.getenv("PRIMARY_GATEWAY_URL", "http://127.0.0.1:8080")
GW2    = os.getenv("SECONDARY_GATEWAY_URL", "http://127.0.0.1:8081")
HMAC_SECRET = os.getenv("HMAC_SECRET","").encode()

SECURE_FILE = "secure_data.enc"
STATE = {"locked": True, "mounted": False}

def sign(msg: str) -> str:
    return hmac.new(HMAC_SECRET, msg.encode(), hashlib.sha256).hexdigest()

def post_json(url, data):
    r = requests.post(url, json=data, timeout=5)
    r.raise_for_status()
    return r.json()

def gw_event(gw_base: str, site_id: str, evt: str):
    ts = int(time.time())
    payload = {"dev_id": DEV_ID, "type": evt, "ts": ts, "sig": sign(f"{DEV_ID}|{evt}|{ts}|{site_id}")}
    try:
        post_json(f"{gw_base}/event", payload)
    except Exception:
        pass

def boot():
    STATE["locked"] = True
    STATE["mounted"] = False
    print("BOOT: filesystem locked")
    gw_event(GW1, "A", "BOOT_LOCKED")
    gw_event(GW2, "B", "BOOT_LOCKED")

def authorize_site(gw_base: str, site_id: str) -> str:
    ts = int(time.time())
    payload = {"dev_id": DEV_ID, "ts": ts, "sig": sign(f"{DEV_ID}|{ts}|{site_id}")}
    body = post_json(f"{gw_base}/authorize", payload)
    if not body.get("ok") or "share_b64" not in body:
        raise RuntimeError(f"site {site_id}: no share")
    print(f"AUTH_OK from site {site_id}")
    return body["share_b64"]

def reconstruct_key_b64(share_a_b64: str, share_b_b64: str) -> str:
    a = base64.b64decode(share_a_b64)
    b = base64.b64decode(share_b_b64)
    if len(a) != len(b):
        raise ValueError("shares length mismatch")
    key = bytes(x ^ y for x, y in zip(a, b))
    return base64.b64encode(key).decode()

def decrypt_secure_file(key_b64: str) -> bytes:
    data = open(SECURE_FILE, "rb").read()
    nonce, ct = data[:12], data[12:]
    key = base64.b64decode(key_b64)
    return AESGCM(key).decrypt(nonce, ct, None)

def mount(key_b64: str) -> bool:
    try:
        plaintext = decrypt_secure_file(key_b64)
    except Exception as e:
        print("MOUNT_FAIL:", e)
        return False
    STATE["locked"] = False
    STATE["mounted"] = True
    print("MOUNT_OK: secure partition mounted")
    print("SECURE CONTENT:", plaintext.decode(errors="ignore").strip())
    return True

def main():
    boot()
    try:
        share_a = authorize_site(GW1, "A")
        share_b = authorize_site(GW2, "B")
        key_b64 = reconstruct_key_b64(share_a, share_b)
    except Exception as e:
        print("AUTH_FAIL:", e)
        gw_event(GW1, "A", "AUTH_FAIL")
        gw_event(GW2, "B", "AUTH_FAIL")
        return
    ok = mount(key_b64)
    gw_event(GW1, "A", "MOUNT_OK" if ok else "MOUNT_FAIL")
    gw_event(GW2, "B", "MOUNT_OK" if ok else "MOUNT_FAIL")

if __name__ == "__main__":
    main()
