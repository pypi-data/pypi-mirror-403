
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Response

# Metrics
REQUEST_COUNT = Counter("devrpa_requests_total", "Total HTTP requests", ["method", "endpoint", "status"])
REQUEST_LATENCY = Histogram("devrpa_request_duration_seconds", "Request latency", ["endpoint"])
WORKFLOW_RUNS = Counter("devrpa_workflow_runs_total", "Workflow runs", ["workflow", "status"])

def metrics_endpoint():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
