from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://admin:password@localhost:5432/moderaai")
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "postgresql://admin:password@localhost:5432/moderaai_test")

# Check if running tests
if "PYTEST_CURRENT_TEST" in os.environ:
    DATABASE_URL = TEST_DATABASE_URL  # Switch to test DB

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
