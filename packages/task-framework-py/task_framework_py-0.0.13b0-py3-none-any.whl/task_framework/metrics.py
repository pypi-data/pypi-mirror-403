"""Prometheus metrics infrastructure."""

from prometheus_client import Counter, Gauge, Histogram

# Thread execution metrics
threads_total = Counter(
    "task_framework_threads_total",
    "Total number of threads created",
    ["state"],
)

thread_execution_duration_seconds = Histogram(
    "task_framework_thread_execution_duration_seconds",
    "Thread execution duration in seconds",
    buckets=[0.1, 0.5, 1.0, 5.0, 10.0, 30.0, 60.0, 300.0, 600.0, 1800.0],
)

threads_current = Gauge(
    "task_framework_threads_current",
    "Current number of threads in each state",
    ["state"],
)

# Library initialization metrics
library_initializations_total = Counter(
    "task_framework_library_initializations_total",
    "Total number of library initializations",
)

task_function_registrations_total = Counter(
    "task_framework_task_function_registrations_total",
    "Total number of task function registrations",
)

# API request metrics
api_requests_total = Counter(
    "task_framework_api_requests_total",
    "Total number of API requests",
    ["method", "endpoint", "status"],
)

api_request_duration_seconds = Histogram(
    "task_framework_api_request_duration_seconds",
    "API request duration in seconds",
    ["method", "endpoint", "status"],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
)

# Artifact metrics
artifacts_created_total = Counter(
    "task_framework_artifacts_created_total",
    "Total number of artifacts created",
    ["kind"],
)

artifacts_deleted_total = Counter(
    "task_framework_artifacts_deleted_total",
    "Total number of artifacts deleted",
)

artifacts_archived_total = Counter(
    "task_framework_artifacts_archived_total",
    "Total number of artifacts archived",
)

# File storage metrics
file_uploads_total = Counter(
    "task_framework_file_uploads_total",
    "Total number of file uploads (includes both pre-signed URL requests and direct uploads)",
)

file_downloads_total = Counter(
    "task_framework_file_downloads_total",
    "Total number of file downloads",
)

file_upload_duration_seconds = Histogram(
    "task_framework_file_upload_duration_seconds",
    "File upload duration in seconds",
    buckets=[1.0, 5.0, 10.0, 30.0, 60.0, 300.0, 600.0],
)

file_download_duration_seconds = Histogram(
    "task_framework_file_download_duration_seconds",
    "File download duration in seconds",
    buckets=[0.1, 0.5, 1.0, 5.0, 10.0, 30.0, 60.0],
)

files_total = Gauge(
    "task_framework_files_total",
    "Total number of files stored",
)

files_total_bytes = Gauge(
    "task_framework_files_total_bytes",
    "Total size of all files stored in bytes",
)

# Schedule metrics
schedule_runs_total = Counter(
    "task_framework_schedule_runs_total",
    "Total number of scheduled runs triggered",
    ["schedule_id", "state"],
)

schedules_active = Gauge(
    "task_framework_schedules_active",
    "Current number of active schedules",
)

# Webhook metrics
webhook_deliveries_total = Counter(
    "task_framework_webhook_deliveries_total",
    "Total number of webhook delivery attempts",
    ["webhook_id", "status"],
)

webhook_delivery_duration_seconds = Histogram(
    "task_framework_webhook_delivery_duration_seconds",
    "Webhook delivery duration in seconds",
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0],
)

# Worker pool metrics
workers_active = Gauge(
    "task_framework_workers_active",
    "Current number of active workers",
)

workers_idle = Gauge(
    "task_framework_workers_idle",
    "Current number of idle workers",
)

# Metadata endpoint metrics
metadata_requests_total = Counter(
    "task_framework_metadata_requests_total",
    "Total number of metadata endpoint requests",
    ["status"],
)

metadata_response_duration_seconds = Histogram(
    "task_framework_metadata_response_duration_seconds",
    "Metadata endpoint response duration in seconds",
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0],
)

