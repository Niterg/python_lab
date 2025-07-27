# Python Lab

The created application supports microservices architecture which helps in scaling the application in a large containerized deployment.
The applications can be found in a ``Dockerfile``

### 1. Chat application 
Installation of dependencies with packages
```bash
# Creats a virtual environment 
# python3 -m venv venv
mkdir chat-app/services
cd chat-app/services

# Creating separate venv for auth and chat for microservices
python -m venv auth-venv
python -m venv chat-venv
```

Additional packages are installed inside ``requirements.txt`` using 
``pip freeze > requirements.txt``

``psycopg2`` requires installation of ``C++ build tools`` from ``Microsoft Visual Studio`` 

> ### Connecting to Postgres:
```bash
postgres -v
psql -U postgres   
\list
CREATE DATABASE chatdb;
\q
```

- Creating SECRET_KEY
```python
python
import secrets
# Creating 32 characters secret
secrets.token_urlsafe(32)
'NyDc4fb1c5EXYe5jY6fozs8qcnMb3R8_wK_C7DYaQvA'
exit()
```
```bash
# In bash terminal
set SECRET_KEY="NyDc4fb1c5EXYe5jY6fozs8qcnMb3R8_wK_C7DYaQvA"
```

Executing these microservices separately 

### For ``auth-service``
```ps1
# In Windows
# Disables Scripts Restiction temporarily
Set-ExecutionPolicy Unrestricted -Scope Process
cd auth-service
auth-venv\Scripts\activate
pip install -r requirements.txt

# Initializing databse 
python -c "from app.dependencies import Base, engine; Base.metadata.create_all(bind=engine)"

# Running the service in port 8000 using uvicorn
uvicorn app.main:app --reload --port 8000
```
### For ``chat-service``
```ps1
# In another terminal of Windows
Set-ExecutionPolicy Unrestricted -Scope Process
cd chat-service
chat-venv\Scripts\activate
pip install -r requirements.txt

# Initializing databse 
python -c "from app.dependencies import Base, engine; Base.metadata.create_all(bind=engine)"

# Running the service in port 8001 using uvicorn
uvicorn app.main:app --reload --port 8001
```

### Testing
To use ``curl`` command install the package using ``winget``
- In Windows (using backtick for line break) `` ` ``
- In Linux use backslash ``\``
```ps1
winget install curl.curl

# Testing by inserting test data
curl.exe -X POST "http://localhost:8000/signup" `
-H "Content-Type: application/json" `
-d '{"username":"testuser","email":"test@example.com","password":"meropass","role":"user"}'
```
OR
```ps1
# Creating user
Invoke-RestMethod -Uri "http://localhost:8000/signup" `
  -Method POST `
  -ContentType "application/json" `
  -Body (@{
      username = "testuser"
      email = "test@example.com"
      password = "meropass"
      role = "user"
  } | ConvertTo-Json)
```
- Creating token for the ``testuser``
```ps1
Invoke-RestMethod -Uri "http://localhost:8000/token" `
  -Method POST `
  -ContentType "application/x-www-form-urlencoded" `
  -Body @{
      username = "testuser"
      password = "meropass"
  }
```
OR Using the python script to generate the token 
    - I have created ``create-token.py`` to generate it 

- Creating Rooms
```ps1
$token = "<just put your token here>"
$headers = @{
    Authorization = "Bearer $token"
    "Content-Type" = "application/json"
}
$body = @{
    name = "Test Room"
} | ConvertTo-Json -Depth 2
$response = Invoke-RestMethod -Uri "http://localhost:8001/rooms" -Method POST -Headers $headers -Body $body
$response
```

- Checking via Postgres CLI
```bash
psql -U postgres 
\list
# lists the databases
\c chatdb
# Selects the database chatdb
\dt
# Lists the table and it's name 
SELECT * FROM auth.users;
```
- Checking connection to websocket in browser console 
```js
const roomId = 1;
const token = "jwt-token"
const ws = new WebSocket(`ws://localhost:8001/ws/${roomId}?token=${token}`);
ws.onopen = () => {
  console.log('Connected');
  ws.send('Hello world!');
};
ws.onmessage = (e) => {
  console.log('Message:', JSON.parse(e.data));
};

ws.onopen = function() {
  console.log("Connected to chat room", roomId);
  setTimeout(() => {
    ws.send(JSON.stringify({
      type: "chat_message",
      content: "Hello everyone!"
    }));
  }, 1000);
};

// function to see text messages
function sendTestMessage() {
  const testMsg = {
    type: "chat_message",
    content: `Test at ${new Date().toLocaleTimeString()}`
  };
  ws.send(JSON.stringify(testMsg));
  console.log('[SENT]', testMsg);
}
sendTestMessage();
```

- Checking messages in Postgres
```ps1
\c chatdb
SELECT * FROM chat.messages WHERE room_id = 1;
 id |     content     |         timestamp          | room_id | user_id | username
----+-----------------+----------------------------+---------+---------+----------
  1 | Hello everyone! | 2025-07-26 16:33:46.323961 |       1 |         | testuser
```


