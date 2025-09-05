import os, base64
from dotenv import dotenv_values

env = dotenv_values("gateway/.env")
key_b64 = env.get("DATA_KEY_B64")
assert key_b64, "Put DATA_KEY_B64 in gateway/.env first"

key = base64.b64decode(key_b64)
rand = os.urandom(len(key))              # share A
share_b = bytes(a ^ b for a, b in zip(rand, key))  # share B = A XOR key

print("SHARE_A_B64=", base64.b64encode(rand).decode())
print("SHARE_B_B64=", base64.b64encode(share_b).decode())
