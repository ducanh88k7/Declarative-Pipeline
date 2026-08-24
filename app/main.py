import os
import psycopg2
import redis
from fastapi import FastAPI
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Response
import time

app = FastAPI()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "cvranker")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/")
def root():
    return {"message": "CV Ranker AI - Lab Service"}


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


@app.get("/v2/version")
def get_version():
    return {"version": "1.2.0", "status": "GitOps Rollout Success"}


REQUEST_COUNT = Counter(
    "cv_ranker_requests_total",
    "Tong so request da nhan",
    ["endpoint", "status"]
)
REQUEST_LATENCY = Histogram(
    "cv_ranker_request_duration_seconds",
    "Thoi gian xu ly request",
    ["endpoint"]
)


@app.middleware("http")
async def track_metrics(request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    REQUEST_LATENCY.labels(endpoint=request.url.path).observe(duration)
    REQUEST_COUNT.labels(endpoint=request.url.path, status=response.status_code).inc()
    return response


@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
