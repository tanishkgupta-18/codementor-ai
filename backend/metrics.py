from prometheus_client import Counter, Histogram

REQUEST_COUNT = Counter(
    "fastapi_requests_total",
    "Total FastAPI Requests",
    ["method", "endpoint"]
)

REQUEST_LATENCY = Histogram(
    "fastapi_request_latency_seconds",
    "Latency of FastAPI endpoints",
    ["endpoint"]
)
