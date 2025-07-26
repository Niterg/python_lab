from jose import jwt

token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0dXNlciIsInJvbGUiOiJ1c2VyIiwiZXhwIjoxNzUzNTQyMDIxfQ.EM4zc4xKSrZRU0GJCrkec8Iug5O_HirAxBiBA10FKRA"  
secret = "NyDc4fb1c5EXYe5jY6fozs8qcnMb3R8_wK_C7DYaQvA" 

payload = jwt.decode(token, secret, algorithms=["HS256"])
print(payload)
