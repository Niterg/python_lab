from datetime import datetime
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException, Query
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from app import models, manager
from sqlalchemy.orm import Session, joinedload
from app.dependencies import get_db, engine, Base
from app.models import Message, Room, User
from app.admin import setup_admin
from typing import List, Optional
from pydantic import BaseModel
from jose import jwt, ExpiredSignatureError
import os

app = FastAPI()

# Security
SECRET_KEY = os.getenv("SECRET_KEY", "NyDc4fb1c5EXYe5jY6fozs8qcnMb3R8_wK_C7DYaQvA")
ALGORITHM = "HS256"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

connection_manager = manager.ConnectionManager()

# For debugging 
def get_current_user(token: str = Depends(oauth2_scheme)):
    print("TOKEN:", token)
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        print("PAYLOAD:", payload)
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=400, detail="Invalid token")
        return username
    except JWTError as e:
        print("JWT ERROR:", e)
        raise HTTPException(status_code=400, detail="Invalid token")

# Fetches the users of auth-service
@app.post("/internal/create_user")
def create_user_sync(payload: dict, db: Session = Depends(get_db)):
    username = payload.get("username")
    if not username:
        raise HTTPException(status_code=400, detail="Username is required")

    user = db.query(User).filter_by(username=username).first()
    if not user:
        new_user = User(username=username)
        db.add(new_user)
        db.commit()
    return {"message": f"user '{username}' synced successfully"}

class RoomCreate(BaseModel):
    name: str
    description: Optional[str] = None

class RoomOut(BaseModel):
    id: int
    name: str
    description: Optional[str]
    created_at: datetime

    class Config:
        orm_mode = True

# Route for rooms
@app.post("/rooms", response_model=RoomOut)
def create_room(
    room: RoomCreate,
    db: Session = Depends(get_db),
    username: str = Depends(get_current_user),
):
    existing = db.query(Room).filter(Room.name == room.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Room already exists")

    new_room = Room(name=room.name, description=room.description)
    db.add(new_room)
    db.commit()
    db.refresh(new_room)
    return new_room


@app.get("/rooms", response_model=List[RoomOut])
def list_rooms(db: Session = Depends(get_db)):
    return db.query(Room).all()

# Route for websocket
@app.websocket("/ws/{room_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    room_id: int,
    token: str = Query(...),
    db: Session = Depends(get_db)
):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[HS256])
        username = payload.get("sub")
        await websocket.accept()
        if not username:
            await websocket.close(code=1008)
            return
    except JWTError as e:
        await websocket.close(code=4403, reason="Invalid token")
        return
    except Exception as e:
        await websocket.close(code=1011, reason="Internal error")

    except ExpiredSignatureError:
        await websocket.close(code=4401, reason="Token expired")

    user = db.query(User).filter(User.username == username).first()
    if not user:
        await websocket.close(code=1008)
        return

    # Optional: check if room exists
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        await websocket.close(code=1008)
        return

    await connection_manager.connect(websocket, room_id)
    try:
        messages = db.query(Message).filter(Message.room_id == room_id).order_by(Message.timestamp.desc()).limit(50).all()
        for msg in reversed(messages):
            await websocket.send_json({
                "content": msg.content,
                "username": username,  # or msg.user.username if relationship loaded
                "timestamp": msg.timestamp.isoformat()
            })

        while True:
            data = await websocket.receive_text()
            db_message = Message(
                content=data,
                room_id=room_id,
                user_id=user.id,
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
    
    # Accepts Websocket Connection
    await websocket.accept()

@app.on_event("startup")
async def startup():
    # Create tables in proper order
    Base.metadata.create_all(bind=engine, tables=[
        Room.__table__,  
        User.__table__,
        Message.__table__
    ])

setup_admin(app)