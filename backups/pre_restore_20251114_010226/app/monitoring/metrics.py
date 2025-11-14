from prometheus_client import Counter, Histogram, Gauge, Info
from functools import wraps
import time

# Counters
emails_sent_total = Counter(
    'emails_sent_total',
    'Total emails sent',
    ['org_id', 'status', 'priority']
)

emails_received_total = Counter(
    'emails_received_total',
    'Total emails received',
    ['org_id', 'spam_status']
)

# Histograms
email_send_duration = Histogram(
    'email_send_duration_seconds',
    'Time to send email',
    ['destination_domain'],
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 5.0, 10.0]
)

api_request_duration = Histogram(
    'api_request_duration_seconds',
    'API request duration',
    ['method', 'endpoint', 'status'],
    buckets=[0.001, 0.01, 0.05, 0.1, 0.5, 1.0, 5.0]
)

queue_processing_duration = Histogram(
    'queue_processing_duration_seconds',
    'Queue message processing time',
    buckets=[0.1, 0.5, 1.0, 5.0, 10.0, 30.0, 60.0]
)

# Gauges
queue_depth = Gauge(
    'queue_depth',
    'Current queue depth',
    ['queue_name', 'priority']
)

active_workers = Gauge(
    'active_workers',
    'Number of active worker processes'
)

database_connections = Gauge(
    'database_connections',
    'Active database connections',
    ['shard_id']
)

smtp_connection_pool_size = Gauge(
    'smtp_connection_pool_size',
    'SMTP connection pool size',
    ['host']
)

redis_memory_usage = Gauge(
    'redis_memory_usage_bytes',
    'Redis memory usage in bytes'
)

# Info
app_info = Info('app', 'Application info')

# Decorators
def track_time(metric, labels=None):
    """Decorator to track execution time"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start
                
                if labels:
                    metric.labels(**labels).observe(duration)
                else:
                    metric.observe(duration)
                
                return result
            except Exception as e:
                duration = time.time() - start
                if labels:
                    metric.labels(**labels).observe(duration)
                raise
        return wrapper
    return decorator