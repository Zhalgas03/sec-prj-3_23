import os, base64
from dotenv import dotenv_values

env = dotenv_values("device/.env")
key_b64 = env.get("DEVICE_KEY_B64")
assert key_b64, "Put DEVICE_KEY_B64 in device/.env first"

key = base64.b64decode(key_b64)
assert len(key) == 32, "DEVICE_KEY_B64 must decode to 32 bytes"

share_a = os.urandom(len(key))                         
share_b = bytes(a ^ b for a, b in zip(share_a, key))   
print("SHARE_A_B64=", base64.b64encode(share_a).decode())
print("SHARE_B_B64=", base64.b64encode(share_b).decode())
