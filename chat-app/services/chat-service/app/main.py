from datetime import datetime
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from app import models, manager
from sqlalchemy.orm import Session, joinedload
from app.dependencies import get_db, engine, Base
from app.models import Message, Room, User
from app.admin import setup_admin
import os

app = FastAPI()

# Security
SECRET_KEY = os.getenv("SECRET_KEY", "")
ALGORITHM = "HS256"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

connection_manager = manager.ConnectionManager()

def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=400, detail="Invalid token")
        return username
    except JWTError:
        raise HTTPException(status_code=400, detail="Invalid token")

@app.websocket("/ws/{room_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    room_id: int,
    token: str,
    db: Session = Depends(get_db)
):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if not username:
            await websocket.close(code=1008)
            return
    except JWTError:
        await websocket.close(code=1008)
        return

    await connection_manager.connect(websocket, room_id)
    try:
        # Send last 50 messages
        messages = db.query(Message).options(
            joinedload(Message.user)
        ).filter(
            Message.room_id == room_id
        ).order_by(
            Message.timestamp.desc()
        ).limit(50).all()
        
        for msg in reversed(messages):
            await websocket.send_json({
                "content": msg.content,
                "username": msg.user.username,
                "timestamp": msg.timestamp.isoformat()
            })

        while True:
            data = await websocket.receive_text()
            db_message = Message(
                content=data,
                room_id=room_id,
                user_id=User.id,
                timestamp=datetime.utcnow()
            )
            db.add(db_message)
            db.commit()
            await connection_manager.broadcast({
                "content": data,
                "username": username,
                "timestamp": db_message.timestamp.isoformat()
            }, room_id)
    except WebSocketDisconnect:
        connection_manager.disconnect(websocket, room_id)

@app.on_event("startup")
async def startup():
    # Create tables in proper order
    Base.metadata.create_all(bind=engine, tables=[
        Room.__table__,  
        User.__table__,
        Message.__table__
    ])

setup_admin(app)