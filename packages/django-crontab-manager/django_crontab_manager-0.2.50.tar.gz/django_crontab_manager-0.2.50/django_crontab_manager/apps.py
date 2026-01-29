from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

class DjangoCrontabManagerConfig(AppConfig):
    name = 'django_crontab_manager'
    verbose_name = _("Django Crontab Manager")
    default_auto_field = "django.db.models.BigAutoField"
