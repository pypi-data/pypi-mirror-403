"""Prometheus metrics for proxy functionality."""

from prometheus_client import Counter, Gauge, Histogram

# Proxy request metrics
proxy_requests_total = Counter(
    "proxy_requests_total",
    "Total number of proxied requests",
    ["server_id", "method", "code"],
)

proxy_request_latency_seconds = Histogram(
    "proxy_request_latency_seconds",
    "Request latency distributions per server",
    ["server_id"],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
)

proxy_upstream_errors_total = Counter(
    "proxy_upstream_errors_total",
    "Count of upstream errors",
    ["server_id", "reason"],
)

# Task type metrics
proxy_tasktype_requests_total = Counter(
    "proxy_tasktype_requests_total",
    "Count of proxied requests per task type and server",
    ["task_type", "server_id", "code"],
)

proxy_tasktype_active_connections = Gauge(
    "proxy_tasktype_active_connections",
    "Current active proxied connections per server (for least-connections LB visibility)",
    ["task_type", "server_id"],
)

# Load balancing metrics
proxy_lb_selection_total = Counter(
    "proxy_lb_selection_total",
    "Counts of selections by LB strategy to aid tuning",
    ["task_type", "server_id", "strategy"],
)

# Health check metrics
proxy_server_health_checks_total = Counter(
    "proxy_server_health_checks_total",
    "Health check results per server",
    ["server_id", "status"],
)

