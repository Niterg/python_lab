from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from app import models, schemas, dependencies
from app.dependencies import engine, Base
from app.models import User, hash_password
from app.schemas import UserCreate
import os
import requests

# Initialize FastAPI
app = FastAPI()

# Security configurations
SECRET_KEY = os.getenv("SECRET_KEY", "NyDc4fb1c5EXYe5jY6fozs8qcnMb3R8_wK_C7DYaQvA")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Database dependency
def get_db():
    db = dependencies.SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Authentication functions
def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# RBAC
def RoleChecker(allowed_roles: list):
    async def checker(
        token: str = Depends(oauth2_scheme),
        db: Session = Depends(get_db)
    ):
        credentials_exception = HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            username: str = payload.get("sub")
            role: str = payload.get("role")
            if role not in allowed_roles:
                raise credentials_exception
        except JWTError:
            raise credentials_exception
        
        user = db.query(User).filter(User.username == username).first()
        if user is None:
            raise credentials_exception
        return user
    return checker

CHAT_SERVICE_URL = "http://localhost:8001/internal/create_user" 

def sync_user_to_chat(username: str):
    try:
        response = requests.post(CHAT_SERVICE_URL, json={"username": username})
        response.raise_for_status()
    except Exception as e:
        print(f"[WARN] Failed to sync user to chat service: {e}")

# Routes
@app.post("/signup")
def signup(user: UserCreate, db: Session = Depends(get_db)):
    # Check if user with email already exists
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # If not exist, create user
    new_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hash_password(user.password),
        role=user.role,
        disabled=False,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    sync_user_to_chat(user.username)
    return new_user

@app.post("/token")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me", response_model=schemas.User)
def read_users_me(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=400, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=400, detail="Invalid token")
    
    user = db.query(models.User).filter(models.User.username == username).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.on_event("startup")
def startup():
    models.Base.metadata.create_all(bind=engine)

@app.get("/")
async def root():
    return {
        "message": "Auth Service Running",
        "docs": "/docs",
        "redoc": "/redoc"
    }