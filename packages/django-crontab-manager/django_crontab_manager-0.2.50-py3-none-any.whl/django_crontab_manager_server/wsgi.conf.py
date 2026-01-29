import psutil

bind = ["0.0.0.0:9313"]
workers = psutil.cpu_count()
threads = 60
daemon = True
accesslog = "./logs/gunicorn.access.log"
errorlog = "./logs/gunicorn.error.log"
keepalive = 300
timeout = 300
graceful_timeout = 300
loglevel = "info"
