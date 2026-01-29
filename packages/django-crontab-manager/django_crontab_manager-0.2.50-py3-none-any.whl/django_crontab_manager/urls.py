from django.urls import path
from . import views

urlpatterns = [
    path('get_servergroup_schedules', views.get_servergroup_schedules, name="django_crontab_manager.get_servergroup_schedules"),
    path('get_schedule_info', views.get_schedule_info, name="django_crontab_manager.get_schedule_info"),
    path('report_result', views.report_result, name="django_crontab_manager.report_result"),
    path('report_results', views.report_results, name="django_crontab_manager.report_results"),
    path('clean_old_results', views.clean_old_results, name="django_crontab_manager.clean_old_results"),
]
