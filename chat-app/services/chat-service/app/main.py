from datetime import datetime
import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException, Query
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from app import models, manager
from sqlalchemy.orm import Session, joinedload
from app.dependencies import get_db, engine, Base
from app.models import Message, Room
from app.admin import setup_admin
from typing import List, Optional
from pydantic import BaseModel
from jose import jwt, ExpiredSignatureError, JWTError
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
        # Validate token first
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        user_id: int = payload.get("user_id")
        if not username:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        # Check room exists
        room = db.query(Room).filter(Room.id == room_id).first()
        if not room:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        # Accept the connection 
        await websocket.accept()
        
        await connection_manager.connect(websocket, room_id)

        messages = (
            db.query(Message)
            .filter(Message.room_id == room_id)
            .order_by(Message.timestamp.asc())
            .limit(50)
            .all()
        )

        for msg in reversed(messages):
            await websocket.send_json({
                "type": "chat_message",
                "content": msg.content,
                "username": msg.username,
                "timestamp": msg.timestamp.isoformat()
            })

        while True:
            data = await websocket.receive_text()
            try:
                message_data = json.loads(data)
                if message_data.get("type") != "chat_message":
                    continue

                db_message = Message(
                    content=message_data["content"],
                    room_id=room_id,
                    user_id=user_id,
                    username=username,
                    timestamp=datetime.utcnow()
                )
                db.add(db_message)
                db.commit()

                await connection_manager.broadcast({
                    "type": "chat_message",
                    "content": message_data["content"],
                    "username": username,
                    "timestamp": db_message.timestamp.isoformat()
                }, room_id)

            except json.JSONDecodeError:
                await websocket.send_json({"error": "Invalid message format"})
            except KeyError:
                await websocket.send_json({"error": "Missing required fields"})

    except Exception as e:
        print(f"WebSocket error: {str(e)}")
        try:
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
        except:
            pass
        connection_manager.disconnect(websocket, room_id)

@app.on_event("startup")
async def startup():
    # Create tables in proper order
    Base.metadata.create_all(bind=engine, tables=[
        Room.__table__,  
        Message.__table__
    ])

setup_admin(app)