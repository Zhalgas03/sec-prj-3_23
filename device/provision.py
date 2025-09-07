import os, base64
from dotenv import load_dotenv
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

load_dotenv()
KEY_B64 = os.getenv("DEVICE_KEY_B64", "")
if not KEY_B64:
    raise SystemExit("DEVICE_KEY_B64 not set in device/.env")

key = base64.b64decode(KEY_B64)       
if len(key) != 32:
    raise SystemExit("DEVICE_KEY_B64 must be 32 bytes (base64 of 32B)")

plaintext = b"Smart-City secure payload: logs v1\n"
nonce = os.urandom(12)                 
ct = AESGCM(key).encrypt(nonce, plaintext, None)
with open("secure_data.enc", "wb") as f:
    f.write(nonce + ct)                 

print("secure_data.enc created (AES-256-GCM)")
