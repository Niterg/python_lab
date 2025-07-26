from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.dependencies import Base

class Room(Base):
    __tablename__ = "rooms"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True)
    description = Column(String, nullable=True)
    
    # Relationship with messages (one-to-many)
    messages = relationship("Message", back_populates="room")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Message(Base):
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True)
    content = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Room relationship (within same service)
    room_id = Column(Integer, ForeignKey("rooms.id"))
    room = relationship("Room", back_populates="messages")
    
    # User reference (loose coupling)
    user_id = Column(Integer)  # No ForeignKey - just stores ID
    username = Column(String)  # Denormalized copy