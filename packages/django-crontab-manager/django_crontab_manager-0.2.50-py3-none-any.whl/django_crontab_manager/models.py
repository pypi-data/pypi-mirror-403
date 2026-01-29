import re
import uuid
import logging
import datetime
from django_middleware_global_request.middleware import get_request

import yaml
from fastutils import hashutils
from fastutils import cipherutils

from django.db import models
from django.db.models import Q
from django.utils.translation import gettext as _
from django.utils import timezone
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.conf import settings as global_settings

from django_safe_fields.fields import SafeTextField
from django_safe_fields.fields import SafeCharField

from . import settings as app_settings

logger = logging.getLogger(__name__)
user_projects_cache_key = "django_crontab_manager_user_projects"
role_of_project_cache_key_template = (
    "django_crontab_manager_project_role_of_project_{project_id}"
)
project_member_mapping_cache_key = "django_crontab_manager_project_member_mapping"
project_member_mapping_item_key_template = "project_id={project_id},user_id={user_id}"


class Project(models.Model):
    NOT_RELATED = 200
    OWNER = 300
    MASTER = 10
    WRITER = 20
    READER = 30
    ROLES = [
        (MASTER, _("Project Master")),
        (WRITER, _("Project Writer")),
        (READER, _("Project Reader")),
    ]
    ROLE_DISPLAY_MAPPING = {
        NOT_RELATED: "",
        OWNER: _("Owner"),
        MASTER: _("Project Master"),
        WRITER: _("Project Writer"),
        READER: _("Project Reader"),
    }

    name = models.CharField(max_length=64, verbose_name=_("Project Name"))
    owner = models.ForeignKey(
        global_settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
        verbose_name=_("Owner"),
    )
    variables_data = SafeTextField(
        null=True,
        blank=True,
        password=app_settings.DJANGO_SAFE_FIELD_PASSWORDS[
            "django_crontab_manager.Project.variables_data"
        ],
        verbose_name=_("Variables"),
    )
    members = models.ManyToManyField(
        to=global_settings.AUTH_USER_MODEL,
        through="ProjectMember",
        verbose_name=_("Project Members"),
    )

    class Meta:
        verbose_name = _("Project")
        verbose_name_plural = _("Projects")

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.owner:
            request = get_request()
            if request:
                self.owner = request.user
        return super().save(*args, **kwargs)

    def get_user_role(self, user, project_member_mapping=None):
        cache_key = role_of_project_cache_key_template.format(project_id=self.pk)
        if hasattr(user, cache_key):
            return getattr(user, cache_key)

        if (not user) or (user and (not user.pk)):
            role = self.NOT_RELATED
        elif self.owner and self.owner.pk == user.pk:
            role = self.OWNER
        else:
            try:
                if project_member_mapping:
                    project_member_mapping_cache_key = (
                        project_member_mapping_item_key_template.format(
                            project_id=self.pk, user_id=user.pk
                        )
                    )
                    member = project_member_mapping.get(
                        project_member_mapping_cache_key, None
                    )
                else:
                    member = ProjectMember.objects.get(project=self, user=user)
                if member:
                    role = member.role
                else:
                    role = self.NOT_RELATED
            except ProjectMember.DoesNotExist:
                logger.warn(
                    f"Project.get_user_role not found the relation in project={self.pk} and user={user.pk}"
                )
                role = self.NOT_RELATED
        setattr(user, cache_key, role)
        return role

    def get_user_role_display(self, user):
        role = self.get_user_role(user)
        return self.ROLE_DISPLAY_MAPPING.get(role, "")

    @classmethod
    def get_user_projects(cls, user, request=None):
        request = request or get_request()
        cache_key = user_projects_cache_key

        if request:
            if hasattr(request, cache_key):
                return getattr(request, cache_key)

        projects = cls.objects.all()
        if not user.is_superuser:
            projects = projects.filter(Q(owner=user) | Q(members=user))

        if request:
            setattr(request, cache_key, projects)

        return projects

    @property
    def variables(self):
        if not self.variables_data:
            return {}
        try:
            return yaml.safe_load(self.variables_data)
        except Exception as error:
            msg = f"Project {self.pk} load variables failed: {error}"
            logger.error(msg)
            return {}

    def set_variable(self, key, value):
        vars = self.variables
        vars[key] = value
        self.variables_data = yaml.safe_dump(vars)


class ProjectMember(models.Model):
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="project_members",
        verbose_name=_("Project"),
    )
    user = models.ForeignKey(
        global_settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="+",
        verbose_name=_("User"),
    )
    role = models.IntegerField(choices=Project.ROLES, verbose_name=_("Project Role"))
    join_time = models.DateTimeField(auto_now_add=True, verbose_name=_("Join Time"))

    class Meta:
        verbose_name = _("Project Member")
        verbose_name_plural = _("Project Members")

    def __str__(self):
        return str(self.user)

    @classmethod
    def get_project_member_mapping(cls, request):
        cache_key = project_member_mapping_cache_key
        if hasattr(request, cache_key):
            return getattr(request, cache_key)
        mapping = {}
        for member in cls.objects.prefetch_related("project", "user").all():
            item_key = project_member_mapping_item_key_template.format(
                project_id=member.project.pk, user_id=member.user.pk
            )
            mapping[item_key] = member
        setattr(request, cache_key, mapping)
        return mapping


class ServerGroup(models.Model):
    project = models.ForeignKey(
        Project,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Project"),
    )
    name = models.CharField(max_length=64, verbose_name=_("Name"))
    uid = models.CharField(max_length=128, unique=True, verbose_name=_("UUID"))
    aclkey = SafeCharField(
        max_length=128,
        password=app_settings.DJANGO_SAFE_FIELD_PASSWORDS[
            "django_crontab_manager.Server.aclkey"
        ],
        verbose_name=_("Acl Key"),
    )
    description = models.TextField(null=True, blank=True, verbose_name=_("Description"))
    add_time = models.DateTimeField(auto_now_add=True, verbose_name=_("Add Time"))
    modify_time = models.DateTimeField(auto_now=True, verbose_name=_("Modify Time"))
    last_updated_time = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Last Updated Time"),
        help_text=_(
            "It's the latest time that the agent installed on that server got schedule settings."
        ),
    )
    enable = models.BooleanField(default=True, verbose_name=_("Enable"))
    variables_data = SafeTextField(
        null=True,
        blank=True,
        password=app_settings.DJANGO_SAFE_FIELD_PASSWORDS[
            "django_crontab_manager.Server.variables_data"
        ],
        verbose_name=_("Variables"),
        help_text=_("Set variables in yml format."),
    )
    owner = models.ForeignKey(
        global_settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
        verbose_name=_("Owner"),
    )

    class Meta:
        verbose_name = _("Server Group")
        verbose_name_plural = _("Server Groups")

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.uid:
            self.uid = uuid.uuid4()
        if not self.owner:
            request = get_request()
            if request:
                self.owner = request.user
        return super().save(*args, **kwargs)

    @classmethod
    def get_user_servergroups(cls, user, request=None):
        request = request or get_request()
        cache_key = "django_crontab_manager_user_servergroups"

        if request:
            if hasattr(request, cache_key):
                return getattr(request, cache_key)

        servergroups = cls.objects.all()
        if not user.is_superuser:
            my_projects = Project.get_user_projects(user, request)
            servergroups = servergroups.filter(
                Q(owner=user) | Q(project__in=my_projects)
            )

        if request:
            setattr(request, cache_key, servergroups)

        return servergroups

    def update_alive_status(self, save=True):
        nowtime = timezone.now()
        self.last_updated_time = nowtime
        if save:
            if self.pk:
                self.__class__.objects.bulk_update([self], fields=["last_updated_time"])
            else:
                self.save()

    @property
    def variables(self):
        if not self.variables_data:
            return {}
        try:
            return yaml.safe_load(self.variables_data)
        except Exception as error:
            msg = f"ServerGroup {self.pk} load variables failed: {error}"
            logger.error(msg)
            return {}

    def set_variable(self, key, value):
        vars = self.variables
        vars[key] = value
        self.variables_data = yaml.safe_dump(vars)

    def alive_server_number(self):
        counter = 0
        for server in self.servers.all():
            if server.alive():
                counter += 1
        return counter

    alive_server_number.short_description = _("Alive Server Number")


class Server(models.Model):
    servergroup = models.ForeignKey(
        ServerGroup,
        on_delete=models.CASCADE,
        related_name="servers",
        verbose_name=_("Server Group"),
    )
    node = models.CharField(max_length=64, verbose_name=_("Node Name"))
    first_report_time = models.DateTimeField(
        null=True, blank=True, verbose_name=_("First Report Time")
    )
    last_report_time = models.DateTimeField(
        null=True, blank=True, verbose_name=_("Last Report Time")
    )

    class Meta:
        verbose_name = _("Server")
        verbose_name_plural = _("Servers")

    def __str__(self):
        return self.node

    def update_alive_status(self, save=True):
        nowtime = timezone.now()
        if not self.first_report_time:
            self.first_report_time = nowtime
        self.last_report_time = nowtime
        if save:
            if self.pk:
                self.__class__.objects.bulk_update(
                    [self], fields=["first_report_time", "last_report_time"]
                )
            else:
                self.save()

    def alive(self):
        if not self.last_report_time:
            return False
        delta = timezone.now() - self.last_report_time
        seconds = delta.total_seconds()
        if seconds > app_settings.DJANGO_CRONTAB_MANAGER_SERVER_OFFLINE_SECONDS:
            return False
        else:
            return True

    alive.short_description = _("Alive")
    alive.boolean = True

    @classmethod
    def get_user_servers(cls, user, request=None):
        request = request or get_request()
        cache_key = "django_crontab_manager_user_servers"

        if request:
            if hasattr(request, cache_key):
                return getattr(request, cache_key)

        servers = cls.objects.all()
        if not user.is_superuser:
            my_servergroups = ServerGroup.get_user_servergroups(user, request)
            servers = servers.filter(servergroup__in=my_servergroups)

        if request:
            setattr(request, cache_key, servers)

        return servers


def zero_exit_code_means_success(schedule, result, code=None, stdout=None, stderr=None):
    if code is None:
        code = result.code
    if stdout is None:
        stdout = result.stdout()
    if stderr is None:
        stderr = result.stderr()
    if code is None:
        return None
    elif code == 0:
        return True
    else:
        return False


def stdout_icontains(schedule, result, code=None, stdout=None, stderr=None):
    if code is None:
        code = result.code
    if stdout is None:
        stdout = result.stdout()
    if stderr is None:
        stderr = result.stderr()
    keyword = schedule.success_determination_config.get("keyword", None)
    if keyword is None:
        return None
    return keyword.lower() in stdout.lower()


def stdout_not_icontains(schedule, result, code=None, stdout=None, stderr=None):
    if code is None:
        code = result.code
    if stdout is None:
        stdout = result.stdout()
    if stderr is None:
        stderr = result.stderr()
    keyword = schedule.success_determination_config.get("keyword", None)
    if keyword is None:
        return None
    return not keyword.lower() in stdout.lower()


def stdout_regex_match(schedule, result, code=None, stdout=None, stderr=None):
    if code is None:
        code = result.code
    if stdout is None:
        stdout = result.stdout()
    if stderr is None:
        stderr = result.stderr()
    pattern = schedule.success_determination_config.get("pattern", None)
    if pattern is None:
        return None
    if re.findall(pattern, stdout):
        return True
    else:
        return False


def randuid():
    return str(uuid.uuid4())


class Schedule(models.Model):
    ZERO_EXIT_CODE_MEANS_SUCCESS = 0
    STDOUT_ICONTAINS = 10
    STDOUT_NOT_ICONTAINS = 20
    STDOUT_REGEX_MATCH = 30

    SUCCESS_RULES = [
        (ZERO_EXIT_CODE_MEANS_SUCCESS, _("An 0 exit code is considered successful")),
        (STDOUT_ICONTAINS, _("Stdout contains given keyword is considered successful")),
        (
            STDOUT_NOT_ICONTAINS,
            _("Stdout NOT contains given keyword is considered successful"),
        ),
        (
            STDOUT_REGEX_MATCH,
            _("Stdout matchs the regex pattern is considered successful"),
        ),
    ]
    SUCCESS_RULE_FUNCTIONS = {
        ZERO_EXIT_CODE_MEANS_SUCCESS: zero_exit_code_means_success,
        STDOUT_ICONTAINS: stdout_icontains,
        STDOUT_NOT_ICONTAINS: stdout_not_icontains,
        STDOUT_REGEX_MATCH: stdout_regex_match,
    }

    schedule_help_text = _(
        """Linux crontab schedule settings: minute, hour, day, month, weekday. e.g. * * * * *"""
    )
    code_help_text = _("MD5 code of the schedule settings. It will be auto computed.")

    project = models.ForeignKey(
        Project,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Project"),
    )
    servergroup = models.ForeignKey(
        ServerGroup,
        on_delete=models.CASCADE,
        related_name="schedules",
        verbose_name=_("Server Group"),
    )
    uid = models.CharField(
        max_length=64, null=True, blank=True, default=randuid, verbose_name=_("UUID")
    )
    title = models.CharField(
        max_length=128,
        verbose_name=_("Title"),
        help_text=_("Describe the scheduled task, so that we know what it is."),
    )
    description = models.TextField(null=True, blank=True, verbose_name=_("Description"))
    schedule = models.CharField(
        max_length=256,
        default="* * * * *",
        verbose_name=_("Schedule Settings"),
        help_text=schedule_help_text,
    )
    user = models.CharField(
        max_length=64, default="root", verbose_name=_("Running User")
    )
    script = SafeTextField(
        null=True,
        blank=True,
        password=app_settings.DJANGO_SAFE_FIELD_PASSWORDS[
            "django_crontab_manager.Schedule.script"
        ],
        verbose_name=_("Shell Script"),
    )
    enable = models.BooleanField(default=True, verbose_name=_("Enable"))
    code = models.CharField(
        max_length=32,
        null=True,
        blank=True,
        verbose_name=_("Setting Code"),
        help_text=code_help_text,
    )

    add_time = models.DateTimeField(auto_now_add=True, verbose_name=_("Add Time"))
    modify_time = models.DateTimeField(auto_now=True, verbose_name=_("Modify Time"))

    success_determination_rule = models.IntegerField(
        choices=SUCCESS_RULES,
        default=ZERO_EXIT_CODE_MEANS_SUCCESS,
        verbose_name=_("Success Determination Rule"),
    )
    success_determination_config_data = SafeTextField(
        null=True,
        blank=True,
        password=app_settings.DJANGO_SAFE_FIELD_PASSWORDS[
            "django_crontab_manager.Schedule.success_determination_config_data"
        ],
        verbose_name=_("Success Determination Rule Settings"),
    )

    server = models.ForeignKey(
        Server,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Server"),
    )
    server_assign_time = models.DateTimeField(
        null=True, blank=True, verbose_name=_("Server Assign Time")
    )

    owner = models.ForeignKey(
        global_settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
        verbose_name=_("Owner"),
    )

    class Meta:
        verbose_name = _("Schedule")
        verbose_name_plural = _("Schedules")
        permissions = [("export_filtered_schedules", _("Export Filtered Schedules"))]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.uid:
            self.uid = uuid.uuid4()
        self.script = self.script and self.script.replace("\r\n", "\n") or ""

        if self.owner is None:
            request = get_request()
            if request:
                self.owner = request.user

        result = super().save(*args, **kwargs)

        new_code = self.get_code()
        if self.code != new_code:
            self.code = new_code
            self.__class__.objects.bulk_update([self], fields=["code"])

        return result

    @classmethod
    def get(cls, schedule):
        if isinstance(schedule, cls):
            return schedule
        if isinstance(schedule, int):
            return cls.objects.get(pk=schedule)
        if isinstance(schedule, str):
            return cls.objects.get(uid=schedule)
        raise KeyError(
            "Schedule query key type must be one of int, str or Schedule, but got type {}...".fromat(
                type(schedule)
            )
        )

    def get_success_determination_rule_code(self):
        return self.success_determination_rule

    def get_script(self, raise_errors=False):
        params = {}
        if self.project:
            params.update(self.project.variables)
        if self.servergroup:
            params.update(self.servergroup.variables)
        try:
            return self.script.format(**params)
        except Exception as error:
            msg = f"Schedule {self.pk} get script failed on missing variables: {error}"
            logger.error(msg)
            if raise_errors:
                raise error
            else:
                return ""

    def get_core_info(self):
        return {
            "id": self.pk,
            "uid": self.uid,
            "title": self.title,
            "description": self.description,
            "schedule": self.schedule,
            "user": self.user,
            "script": self.get_script(),
            "enable": self.enable,
            "add_time": str(self.add_time),
            "mod_time": str(self.modify_time),
        }

    def get_code(self):
        info = self.get_core_info()
        text = ""
        keys = list(info.keys())
        keys.sort()
        for key in keys:
            text += str(key)
            text += str(info[key])
        return hashutils.get_md5_hexdigest(text)

    def info(self):
        info = self.get_core_info()
        info["code"] = self.code
        return info

    def get_success_determination_config(self):
        if not self.success_determination_config_data:
            return {}
        try:
            return yaml.safe_load(self.success_determination_config_data)
        except:
            return {}

    def set_success_determination_config(self, value):
        self.success_determination_config_data = yaml.safe_dump(value)

    success_determination_config = property(
        get_success_determination_config, set_success_determination_config
    )

    def success_determination(self, result, code=None, stdout=None, stderr=None):
        return self.SUCCESS_RULE_FUNCTIONS.get(self.success_determination_rule)(
            self, result, code, stdout, stderr
        )

    def assign_server(self, server, nowtime=None, save=False):
        nowtime = nowtime or timezone.now()
        self.server = server
        self.server_assign_time = nowtime
        if save:
            self.save()

    @classmethod
    def get_user_schedules(cls, user, request=None):
        request = request or get_request()
        cache_key = "django_crontab_manager_user_schedules"

        if request:
            if hasattr(request, cache_key):
                return getattr(request, cache_key)

        schedules = cls.objects.all()
        if not user.is_superuser:
            my_projects = Project.get_user_projects(user, request)
            schedules = schedules.filter(Q(owner=user) | Q(project__in=my_projects))

        if request:
            setattr(request, cache_key, schedules)

        return schedules


def get_result_file_upload_to(instance, filename):
    nowtime = datetime.datetime.now()
    year = nowtime.year
    month = nowtime.month
    day = nowtime.day
    timestr = nowtime.strftime("%Y%m%d%H%M%S")
    return "{prefix}/{year}/{month}/{day}/{timestr}.{filename}".format(
        prefix=app_settings.DJANGO_CRONTAB_MANAGER_RESULT_FILES,
        year=year,
        month=month,
        day=day,
        timestr=timestr,
        filename=filename,
    )


class Result(models.Model):
    project = models.ForeignKey(
        Project,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Project"),
    )
    schedule = models.ForeignKey(
        Schedule,
        on_delete=models.CASCADE,
        related_name="results",
        verbose_name=_("Schedule"),
    )
    run_time = models.DateTimeField(verbose_name=_("Run Time"))
    success = models.BooleanField(null=True, verbose_name=_("Success"))
    code = models.IntegerField(
        null=True, blank=True, verbose_name=_("Script Exit Code")
    )
    stdout_file = models.FileField(
        storage=app_settings.DJANGO_CRONTAB_MANAGER_RESULT_FILES_STORAGE,
        upload_to=get_result_file_upload_to,
        null=True,
        blank=True,
        verbose_name=_("Script Output Message"),
    )
    stderr_file = models.FileField(
        storage=app_settings.DJANGO_CRONTAB_MANAGER_RESULT_FILES_STORAGE,
        upload_to=get_result_file_upload_to,
        null=True,
        blank=True,
        verbose_name=_("Script Error Message"),
    )

    class Meta:
        verbose_name = _("Result")
        verbose_name_plural = _("Results")

    def __str__(self):
        return str(self.pk)

    def save(self, *args, **kwargs):
        if not self.project:
            if self.schedule:
                self.project = self.schedule.project
        return super().save(*args, **kwargs)

    def success_determination(self, code=None, stdout=None, stderr=None, save=False):
        if code is None:
            code = self.code
        if stdout is None:
            stdout = self.stdout
        if stderr is None:
            stderr = self.stderr
        self.success = self.schedule.success_determination(self, code, stdout, stderr)
        if save:
            self.save()
        return self.success

    @classmethod
    def get_stdout_file_cipher(cls):
        password = app_settings.DJANGO_SAFE_FIELD_PASSWORDS[
            "django_crontab_manager.Result.stdout_file"
        ]
        return cipherutils.AesCipher(
            password=password,
            result_encoder=cipherutils.Base64Encoder(),
            force_text=True,
        )

    @classmethod
    def get_stderr_file_cipher(cls):
        password = app_settings.DJANGO_SAFE_FIELD_PASSWORDS[
            "django_crontab_manager.Result.stdout_file"
        ]
        return cipherutils.AesCipher(
            password=password,
            result_encoder=cipherutils.Base64Encoder(),
            force_text=True,
        )

    def stdout(self):
        if not self.stdout_file:
            return ""
        with self.stdout_file.open("rb") as fobj:
            return self.get_stdout_file_cipher().decrypt(fobj.read().decode("utf-8"))

    def stderr(self):
        if not self.stderr_file:
            return ""
        with self.stderr_file.open("rb") as fobj:
            return self.get_stderr_file_cipher().decrypt(fobj.read().decode("utf-8"))

    @classmethod
    def get_user_results(cls, user, request=None):
        request = request or get_request()
        cache_key = "django_crontab_manager_user_results"

        if request:
            if hasattr(request, cache_key):
                return getattr(request, cache_key)

        results = cls.objects.all()
        if not user.is_superuser:
            my_projects = Project.get_user_projects(user, request)
            results = results.filter(project__in=my_projects)

        if request:
            setattr(request, cache_key, results)

        return results


@receiver(post_save, sender=ServerGroup)
def do_update_schedules_code(sender, **kwargs):
    from .services import update_schedules_code

    instance = kwargs.get("instance", None)
    if instance:
        changed_items = update_schedules_code(instance.schedules.all())
        for item in changed_items:
            logger.info(
                "Schedule id={} title={} update code after server settings changed.".format(
                    item.pk, item.title
                )
            )
