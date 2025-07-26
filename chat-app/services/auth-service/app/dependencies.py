from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:admin@localhost:5432/chatdb")
SERVICE_NAME = os.getenv("SERVICE_NAME", "auth") 

engine = create_engine(DATABASE_URL)
Base = declarative_base()

# Schema creation event handler
@event.listens_for(engine, "connect")
def create_schema_if_not_exists(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute(f"CREATE SCHEMA IF NOT EXISTS {SERVICE_NAME}")
    cursor.close()

Base.metadata.schema = SERVICE_NAME
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()