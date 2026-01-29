
import datetime
import bizerror

from django_apiview.views import apiview

from .models import ServerGroup
from .models import Server
from .models import Schedule

from . import services
from . import settings as app_settings

def aclkey_check(servergroup, node, aclkey):
    try:
        servergroup = ServerGroup.objects.get(uid=servergroup)
    except Server.DoesNotExist:
        raise bizerror.AppAuthFailed()
    if servergroup.aclkey != aclkey:
        raise bizerror.AppAuthFailed()
    try:
        server = Server.objects.get(servergroup=servergroup, node=node)
    except Server.DoesNotExist:
        server = Server(servergroup=servergroup, node=node)
    return servergroup, server

@apiview
def get_servergroup_schedules(servergroup, node, aclkey):
    servergroup, server = aclkey_check(servergroup, node, aclkey)
    services.update_server_alive_status(server, servergroup) # update server and servergroup's update time
    if not servergroup.enable: # if servergroup is disabled, all schedules are disabled
        return {}
    return services.get_servergroup_schedules(servergroup, server)

@apiview
def get_schedule_info(servergroup, node, aclkey, schedule):
    aclkey_check(servergroup, node, aclkey)
    schedule = Schedule.objects.get(uid=schedule)
    return schedule.info()

@apiview
def report_result(servergroup, node, aclkey, schedule, run_time=None, code=None, stdout=None, stderr=None):
    aclkey_check(servergroup, node, aclkey)
    services.report_result(schedule, run_time, code, stdout, stderr)
    return True

@apiview
def report_results(servergroup, node, aclkey, results):
    aclkey_check(servergroup, node, aclkey)
    services.report_results(results)
    return True

@apiview
def clean_old_results(apikey, keep_number=None, keep_days=None):
    if apikey != app_settings.DJANGO_CRONTAB_MANAGER_APIKEY:
        raise bizerror.AppAuthFailed()

    count = 0

    keep_days = keep_days or app_settings.DJANGO_CRONTAB_MANAGER_RESULTS_KEEP_DAYS
    too_old_date = datetime.datetime.now() - datetime.timedelta(days=keep_days)
    for schedule in Schedule.objects.all():
        for result in schedule.results.filter(run_time__lt=too_old_date):
            result.delete()
            count += 1

    keep_number = keep_number or app_settings.DJANGO_CRONTAB_MANAGER_RESULTS_KEEP_NUMBER
    for schedule in Schedule.objects.all():
        for result in schedule.results.order_by("-run_time")[keep_number:]:
            result.delete()
            count += 1

    return count
