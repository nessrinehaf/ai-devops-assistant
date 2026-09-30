"""Demo app for the AI DevOps Assistant project.

Exposes Prometheus metrics and endpoints that deliberately cause problems,
so we get real alerts and error logs for the assistant to analyze.
"""
import logging
import os
import random
import time

from flask import Flask, Response, g, jsonify, request
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s demo-app %(message)s",
)
log = logging.getLogger("demo-app")

VERSION = os.getenv("APP_VERSION", "dev")[:7]

app = Flask(__name__)

REQUESTS = Counter(
    "http_requests_total", "Total HTTP requests", ["method", "path", "status"]
)
LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["path"],
    buckets=(0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10),
)
LEAKED_MB = Gauge("demo_leaked_memory_megabytes", "Memory deliberately leaked by /leak")

_leak: list[bytearray] = []


def _route() -> str:
    # Use the route pattern, not the raw URL, to keep metric labels bounded
    # (bots hitting random URLs would otherwise create endless label values).
    return request.url_rule.rule if request.url_rule else "unmatched"


@app.before_request
def _start_timer():
    g.start = time.perf_counter()


@app.after_request
def _record_metrics(response):
    path = _route()
    if path != "/metrics":
        LATENCY.labels(path).observe(time.perf_counter() - g.start)
        REQUESTS.labels(request.method, path, str(response.status_code)).inc()
    return response


@app.get("/")
def index():
    return jsonify(status="ok", version=VERSION)


@app.get("/healthz")
def healthz():
    return "ok"


@app.get("/error")
def error():
    log.error(
        "database query failed: connection timeout after 5s host=db.internal:5432 "
        "query=SELECT * FROM orders"
    )
    return jsonify(error="internal server error"), 500


@app.get("/slow")
def slow():
    delay = random.uniform(2, 5)
    time.sleep(delay)
    log.warning("slow response: upstream payment API took %.2fs", delay)
    return jsonify(status="ok", delay=round(delay, 2))


@app.get("/leak")
def leak():
    _leak.append(bytearray(20 * 1024 * 1024))  # 20 MB per call, never freed
    total = len(_leak) * 20
    LEAKED_MB.set(total)
    log.warning("cache grew without eviction: %d MB held in memory", total)
    return jsonify(leaked_mb=total)


@app.get("/crash")
def crash():
    log.critical("unrecoverable error: config file /etc/app/config.yaml is corrupted, exiting")
    os._exit(1)


@app.get("/metrics")
def metrics():
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)
