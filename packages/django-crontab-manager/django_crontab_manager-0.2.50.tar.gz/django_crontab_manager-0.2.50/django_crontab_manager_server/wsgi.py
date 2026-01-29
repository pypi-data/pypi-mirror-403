"""
WSGI config for django_crontab_manager_server project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/2.2/howto/deployment/wsgi/
"""

import os
import logging

from django.core.wsgi import get_wsgi_application

logger = logging.getLogger(__name__)

logger.info("creating wsgi application...")
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_crontab_manager_server.settings')
application = get_wsgi_application()
logger.info("wsgi application created.")
