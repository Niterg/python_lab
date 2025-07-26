from jose import jwt
from datetime import datetime, timedelta
import os

SECRET_KEY = os.getenv("SECRET_KEY", "NyDc4fb1c5EXYe5jY6fozs8qcnMb3R8_wK_C7DYaQvA")
ALGORITHM = "HS256"

payload = {
    "sub": "testuser",
    "role": "user",
    "exp": datetime.utcnow() + timedelta(hours=1)
}

token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
print("New Token:", token)
