from fastapi import FastAPI
from core.database import *

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Welcome to ModeraAI"}

@app.get("/health")
def read_health():
    if engine:
        from sqlalchemy import text
        db = SessionLocal()
        tables = db.execute(text("SELECT * FROM information_schema.tables WHERE table_schema='public'")).fetchall()
        db.close()
        return {"status": "Database connection Successful", "tables": [table[0] for table in tables]}
    else:
        return {"status": "Database connection Failed"}