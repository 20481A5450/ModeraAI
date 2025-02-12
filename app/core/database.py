from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv
from sqlalchemy.ext.declarative import declarative_base

load_dotenv()  # Load environment variables

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:root@localhost/moderaai")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()  # Move this above the imports

# Import models after defining Base to avoid circular import issues
from app.models import moderation
