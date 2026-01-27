"""Gunicorn configuration for production deployment"""
import os

# Server socket
bind = f"0.0.0.0:{os.environ.get('PORT', '8080')}"

# Worker processes
workers = int(os.environ.get('GUNICORN_WORKERS', '2'))
worker_class = 'sync'
threads = int(os.environ.get('GUNICORN_THREADS', '4'))

# Timeout
timeout = 300  # 5 minutes for long-running spectrum generation
graceful_timeout = 30
keepalive = 5

# Logging
accesslog = '-'
errorlog = '-'
loglevel = os.environ.get('LOG_LEVEL', 'info')
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = 'nmr-simulator'

# Server mechanics
daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

# SSL (if needed)
# keyfile = None
# certfile = None
