from passlib.context import CryptContext
from sqlalchemy import Column, Integer, String, Boolean
from app.dependencies import Base

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

class User(Base):
    __tablename__ = "users"
    __table_args__ = {"schema": "auth"}

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String, default="user")
    disabled = Column(Boolean, default=False)