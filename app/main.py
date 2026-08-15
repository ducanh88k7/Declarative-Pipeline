import os
import psycopg2
import redis
from fastapi import FastAPI

app = FastAPI()

# Đọc thông tin kết nối từ biến môi trường - KHÔNG hardcode trong code
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "cvranker")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")

@app.get("/")
def root():
    return {"message": "CV Ranker AI - Lab Service"}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/db-check")
def db_check():
    conn = psycopg2.connect(
        host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD
    )
    conn.close()
    return {"db_connection": "success", "host": DB_HOST}

@app.get("/cache-check")
def cache_check():
    r = redis.Redis(host=REDIS_HOST, port=6379, decode_responses=True)
    r.set("lab_key", "hello from compose")
    value = r.get("lab_key")
    return {"cache_value": value, "host": REDIS_HOST}