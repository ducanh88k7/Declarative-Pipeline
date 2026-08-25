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


import logging
from pythonjsonlogger import jsonlogger

logger = logging.getLogger("cv_ranker")
handler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter(
    "%(asctime)s %(levelname)s %(name)s %(message)s",
    rename_fields={"asctime": "timestamp", "levelname": "level"}
)
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

trace.set_tracer_provider(TracerProvider())
otlp_exporter = OTLPSpanExporter(endpoint="cv-ranker-jaeger-collector:4317", insecure=True)
trace.get_tracer_provider().add_span_processor(BatchSpanProcessor(otlp_exporter))

FastAPIInstrumentor.instrument_app(app)
tracer = trace.get_tracer(__name__)

@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/")
def root():
    return {"message": "CV Ranker AI - Lab Service"}


@app.get("/db-check")
def db_check():
    try:
        conn = psycopg2.connect(
            host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD
        )
        conn.close()
        logger.info("Ket noi DB thanh cong", extra={"endpoint": "/db-check"})
        return {"db_connection": "success", "host": DB_HOST}
    except Exception as e:
        logger.error(
            "Ket noi DB that bai",
            extra={"endpoint": "/db-check", "error_detail": str(e)}
        )
        return {"db_connection": "failed"}, 500


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


import time
import random


@app.get("/rag-search")
def rag_search(query: str):
    with tracer.start_as_current_span("create_embedding") as span:
        span.set_attribute("query.text", query)
        time.sleep(0.05)
        embedding = [0.1] * 768

    with tracer.start_as_current_span("pgvector_search") as span:
        span.set_attribute("db.system", "postgresql")
        time.sleep(0.03)
        candidates = ["cv_001", "cv_002", "cv_003"]
        span.set_attribute("results.count", len(candidates))

    with tracer.start_as_current_span("gemini_llm_call") as span:
        span.set_attribute("llm.model", "gemini-1.5-flash")
        simulated_latency = random.uniform(0.8, 2.5)
        time.sleep(simulated_latency)
        span.set_attribute("llm.latency_seconds", simulated_latency)

    return {"query": query, "results": candidates}
