"""django_crontab_manager_server URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.urls import include
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.views.generic import RedirectView
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

admin.site.site_header = _("Django Crontab Manager")
admin.site.site_title = _("Django Crontab Manager")

DJANGO_CRONTAB_MANAGER_ADMIN_SITE_PREFIX = getattr(settings, "DJANGO_CRONTAB_MANAGER_ADMIN_SITE_PREFIX", "crontab-manager")

urlpatterns = [
    path('', RedirectView.as_view(url=reverse_lazy("admin:index"))),
    path(f'{DJANGO_CRONTAB_MANAGER_ADMIN_SITE_PREFIX}/', admin.site.urls),
    path(f'captcha/', include("captcha.urls")),
    path(f'{DJANGO_CRONTAB_MANAGER_ADMIN_SITE_PREFIX}/api/', include("django_crontab_manager.urls")),
] + staticfiles_urlpatterns()


