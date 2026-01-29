
import uuid
import logging

from django.conf import settings

logger = logging.getLogger(__name__)

SECRET_KEY = settings.SECRET_KEY
DJANGO_SAFE_FIELD_PASSWORDS = {
    "django_crontab_manager.Project.variables_data": SECRET_KEY,
    "django_crontab_manager.Server.variables_data": SECRET_KEY,
    "django_crontab_manager.Server.aclkey": SECRET_KEY,
    "django_crontab_manager.Schedule.script": SECRET_KEY,
    "django_crontab_manager.Schedule.success_determination_config_data": SECRET_KEY,
    "django_crontab_manager.Result.stdout_file": SECRET_KEY,
    "django_crontab_manager.Result.stderr_file": SECRET_KEY,
}
DJANGO_SAFE_FIELD_PASSWORDS.update(getattr(settings, "DJANGO_SAFE_FIELD_PASSWORDS", {}))
DJANGO_CRONTAB_MANAGER_RESULT_FILES = getattr(settings, "DJANGO_CRONTAB_MANAGER_RESULT_FILES", "django_crontab_manager_result_files")
DJANGO_CRONTAB_MANAGER_RESULT_FILES_STORAGE = getattr(settings, "DJANGO_CRONTAB_MANAGER_RESULT_FILES_STORAGE", None)
DJANGO_CRONTAB_MANAGER_SERVER_OFFLINE_SECONDS = getattr(settings, "DJANGO_CRONTAB_MANAGER_SERVER_OFFLINE_SECONDS", 60*5)
DJANGO_CRONTAB_MANAGER_RESULTS_KEEP_NUMBER = getattr(settings, "DJANGO_CRONTAB_MANAGER_RESULTS_KEEP_NUMBER", 10080)
DJANGO_CRONTAB_MANAGER_RESULTS_KEEP_DAYS = getattr(settings, "DJANGO_CRONTAB_MANAGER_RESULTS_KEEP_DAYS", 366)
DJANGO_CRONTAB_MANAGER_APIKEY = getattr(settings, "DJANGO_CRONTAB_MANAGER_APIKEY", None)
if not DJANGO_CRONTAB_MANAGER_APIKEY:
    DJANGO_CRONTAB_MANAGER_APIKEY = str(uuid.uuid4())
    logger.warning(f"DJANGO_CRONTAB_MANAGER_APIKEY is NOT configured, set to RANDOM key {DJANGO_CRONTAB_MANAGER_APIKEY}")


# 如果当前未关联服务器任务数超过该数值，则需要进行任务分配，否则全部当前服务器拿走全部任务。
DJANGO_CRONTAB_MANAGER_SCHEDULES_LOAD_BALANCE_THRESHOLD = getattr(settings, "DJANGO_CRONTAB_MANAGER_SCHEDULES_LOAD_BALANCE_THRESHOLD", 10) 
