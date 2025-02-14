from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import time
import sys
import os
from fastapi import FastAPI
from app.api.v1.routes import router
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST  
sys.path.append(os.path.abspath(os.path.dirname(__file__)))


app = FastAPI(title="ModeraAI")

app.include_router(router, prefix="/api/v1")

# Prometheus Metrics
REQUEST_COUNT = Counter("http_requests_total", "Total number of HTTP requests", ["method", "endpoint", "http_status"])
REQUEST_LATENCY = Histogram("http_request_latency_seconds", "Latency of HTTP requests", ["method", "endpoint"])

class PrometheusMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        
        # Update Prometheus Metrics
        REQUEST_COUNT.labels(request.method, request.url.path, response.status_code).inc()
        REQUEST_LATENCY.labels(request.method, request.url.path).observe(process_time)
        
        return response

# Add middleware to capture metrics for all routes
app.add_middleware(PrometheusMiddleware)

@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    """Middleware to measure request count and latency."""
    start_time = time.time()
    response = await call_next(request)
    latency = time.time() - start_time

    # Increment request counter
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        http_status=response.status_code
    ).inc()

    # Record request latency
    REQUEST_LATENCY.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(latency)

    return response

@app.get("/metrics")
async def metrics():
    """Expose Prometheus metrics."""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
