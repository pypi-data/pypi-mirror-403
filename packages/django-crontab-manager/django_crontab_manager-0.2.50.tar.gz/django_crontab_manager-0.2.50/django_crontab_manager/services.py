
import math
import logging
import datetime

from dateutil.parser import parse as parse_datetime

from django.utils import timezone
from django.core.files.base import ContentFile

from . import settings as app_settings

from .models import Schedule
from .models import Result

logger = logging.getLogger(__name__)


def get_servergroup_schedules(servergroup, server):
    result = {}
    not_assigned_schedules = []
    for schedule in Schedule.objects.filter(servergroup=servergroup, enable=True):
        if schedule.server and schedule.server.pk == server.pk:
            result[schedule.uid] = schedule.code
        else:
            if not schedule.server:
                not_assigned_schedules.append(schedule)
            elif not schedule.server.alive():
                not_assigned_schedules.append(schedule)
    if not_assigned_schedules:
        not_assigned_schedules_number = len(not_assigned_schedules)
        alived_server_number = 0
        servers = servergroup.servers.all()
        for server in servers:
            if server.alive():
                alived_server_number += 1
        if not_assigned_schedules_number > app_settings.DJANGO_CRONTAB_MANAGER_SCHEDULES_LOAD_BALANCE_THRESHOLD:
            assign_number = math.ceil(not_assigned_schedules_number / alived_server_number)
        else:
            assign_number = not_assigned_schedules_number
        assign_schedules = not_assigned_schedules[:assign_number]
        for schedule in assign_schedules:
            schedule.assign_server(server, save=True)
            result[schedule.uid] = schedule.code
    return result

def update_server_alive_status(server, servergorup=None):
    servergorup = servergorup or server.servergorup
    server.update_alive_status(save=True)
    servergorup.update_alive_status(save=True)

def update_schedules_code(items):
    changed_items = []
    for item in items:
        old_code = item.code
        new_code = item.get_code()
        if old_code != new_code:
            item.code = new_code
        changed_items.append(item)
    if changed_items:
        Schedule.objects.bulk_update(changed_items, fields=["code"])
    return changed_items

def update_results_success_determination(items):
    changed_items = []
    for item in items:
        old_success_value = item.success
        new_success_value = item.success_determination()
        if old_success_value != new_success_value:
            changed_items.append(item)
    if changed_items:
        Result.objects.bulk_update(changed_items, fields=["success"])
    return changed_items

def report_result(schedule, runtime=None, code=None, stdout=None, stderr=None, save=True):
    nowtime = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    schedule = Schedule.get(schedule)
    result = Result()
    result.project = schedule.project
    result.schedule = schedule
    result.run_time = runtime or timezone.now()
    result.code = code
    result.success_determination(code, stdout, stderr, save=False)
    stdout = stdout and Result.get_stdout_file_cipher().encrypt(stdout) or None
    stderr = stderr and Result.get_stderr_file_cipher().encrypt(stderr) or None
    if stdout:
        stdout_filename = f"{schedule.uid}-{nowtime}-stdout.txt"
        result.stdout_file.save(stdout_filename, ContentFile(stdout))
    if stderr:
        stderr_filename = f"{schedule.uid}-{nowtime}-stderr.txt"
        result.stderr_file.save(stderr_filename, ContentFile(stderr))
    if save:
        result.save()
    return result

def report_results(results):
    schedule_mapping = {}
    for schedule in Schedule.objects.prefetch_related("project").all():
        schedule_mapping[schedule.uid] = schedule
    instances = []
    for result in results:
        try:
            schedule_uid = result["schedule"]
            schedule = schedule_mapping.get(schedule_uid, None)
            if not schedule:
                logger.warn(f"schedule with uid={schedule_uid} is not exist or deleted...")
                continue
            runtime = parse_datetime(result["runtime"])
            returncode = int(result.get("returncode", -1))
            stdout = result.get("stdout", "")
            stderr = result.get("stderr", "")
            instance = report_result(schedule, runtime, returncode, stdout, stderr)
            instances.append(instance)
        except Exception as error:
            logger.error(f"report_result failed: schedule_uid={schedule_uid}, info={result}, error={error}...")
    return len(instances)
