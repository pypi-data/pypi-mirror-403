
import copy
import logging

from magic_import import import_from_string

from django.contrib import admin
from django.utils.translation import gettext as _
from django.forms import ModelForm
from django.forms import ValidationError
from django.db.models import Q
from django.conf import settings
from django.contrib.admin import RelatedFieldListFilter
from django.contrib.admin.filters import BooleanFieldListFilter
from django.contrib.auth import get_user_model
from django.template.loader import render_to_string

from django_power_admin.admin import get_power_admin_class
from django_power_admin.widgets import ConfigTable
from django_power_admin.widgets import Select2
from django_fastadmin.widgets import AceWidget
from django_power_admin.widgets import AllUsersSelect
from django_power_admin.filters import DateRangeFilter
from django_middleware_global_request.middleware import get_request

from .models import ServerGroup
from .models import Server
from .models import Schedule
from .models import Result
from .models import Project
from .models import ProjectMember

from .actions import redo_success_determination
from .actions import recompute_schedule_code

BaseAdminClass = None
BaseAdminClassPath = getattr(settings, "DJANGO_CRONTAB_MANAGER_BASE_ADMIN_CLASS", None)
if BaseAdminClassPath:
    BaseAdminClass = import_from_string(BaseAdminClassPath)
if not BaseAdminClass:
    BaseAdminClass = get_power_admin_class()


User = get_user_model()
logger = logging.getLogger(__name__)

class UserPorjectsFieldListFilter(RelatedFieldListFilter):
    def field_choices(self, field, request, model_admin):
        my_projects = Project.get_user_projects(request.user, request)
        choices = []
        for project in my_projects:
            choices.append((project.pk, project.name))
        return choices

class UserServerGroupsFieldListFilter(RelatedFieldListFilter):
    def field_choices(self, field, request, model_admin):
        my_servergroups = ServerGroup.get_user_servergroups(request.user, request)
        choices = []
        for servergroup in my_servergroups:
            choices.append((servergroup.pk, servergroup.name))
        return choices

class UserServersFieldListFilter(RelatedFieldListFilter):
    def field_choices(self, field, request, model_admin):
        my_servers = Server.get_user_servers(request.user, request)
        choices = []
        for server in my_servers:
            choices.append((server.pk, server.node))
        return choices

class UserSchedulesFieldListFilter(RelatedFieldListFilter):
    def field_choices(self, field, request, model_admin):
        my_schedules = Schedule.get_user_schedules(request.user, request)
        choices = []
        for schedule in my_schedules:
            choices.append((schedule.pk, schedule.title))
        return choices

class UserProjectsSelect(Select2):
    def get_context(self, name, value, attrs):
        self.choices = [("", "-"*10)]
        request = get_request()
        my_projects = Project.get_user_projects(request.user, request)
        for project in my_projects:
            self.choices.append((project.pk, project.name))
        return super().get_context(name, value, attrs)

class UserServerGroupsSelect(Select2):
    def get_context(self, name, value, attrs):
        self.choices = [("", "-"*10)]
        request = get_request()
        my_servergroups = ServerGroup.get_user_servergroups(request.user, request)
        for servergroup in my_servergroups:
            self.choices.append((servergroup.pk, servergroup.name))
        return super().get_context(name, value, attrs)

class UserScheduleSelect(Select2):
    def get_context(self, name, value, attrs):
        self.choices = [("", "-"*10)]
        request = get_request()
        my_schedules = Schedule.get_user_schedules(request.user, request)
        for schedule in my_schedules:
            self.choices.append((schedule.pk, schedule.title))
        return super().get_context(name, value, attrs)

class ServerGroupForm(ModelForm):
    class Meta:
        widgets = {
            "project": UserProjectsSelect(),
            "variables_data": ConfigTable(),
        }

class ServerInline(admin.TabularInline):
    model = Server
    extra = 0

class ServerGroupAdmin(BaseAdminClass):
    form = ServerGroupForm
    list_display = ["name", "enable", "last_updated_time", "alive_server_number", "project"]
    list_filter = [
        "enable",
        ("project", UserPorjectsFieldListFilter),
    ]
    search_fields = ["name", "description", "uid"]
    readonly_fields = ["last_updated_time"]
    inlines = [
        ServerInline,
    ]

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        if not request.user.is_superuser:
            my_projects = Project.get_user_projects(request.user, request)
            queryset = queryset.filter(Q(owner=request.user) | Q(project__in=my_projects))
        queryset = queryset.prefetch_related("servers")
        return queryset
    
    def get_readonly_fields(self, request, obj=None):
        fields = super().get_readonly_fields(request, obj)
        if not request.user.is_superuser:
            if not "owner" in fields:
                fields = list(fields)
                fields.append("owner")
        return fields

class ScheduleForm(ModelForm):
    class Meta:
        model = Schedule
        fields = "__all__"
        widgets = {
            "project": UserProjectsSelect(),
            "servergroup": UserServerGroupsSelect(),
            "script": AceWidget(ace_options={
                "mode": "ace/mode/sh",
            }),
            "success_determination_config_data": AceWidget(ace_options={
                "mode": "ace/mode/yaml",
            }),
        }

    def clean_script(self):
        script = self.cleaned_data.get("script", "")
        project = self.cleaned_data.get("project", None)
        servergroup = self.cleaned_data.get("servergroup", None)
        params = {}
        if project:
            params.update(project.variables)
        if servergroup:
            params.update(servergroup.variables)
        try:
            script.format(**params)
        except Exception as error:
            raise ValidationError(_("Script variables replace failed: {error}").format(error=error))
        return script

class ScheduleAdmin(BaseAdminClass):
    form = ScheduleForm
    list_filter = [
        ("project", UserPorjectsFieldListFilter),
        ("servergroup", UserServerGroupsFieldListFilter),
        ("server", UserServersFieldListFilter),
        "enable",
    ]
    list_display = ["title", "schedule", "enable", "project", "servergroup", "script_status"]
    search_fields = ["title", "description", "uid", "schedule", "user", "script", "code"]
    readonly_fields = ["uid", "code"]

    actions = [
        recompute_schedule_code,
    ]

    def script_status(self, obj):
        try:
            obj.get_script(raise_errors=True)
            return True
        except Exception as error:
            return False
    script_status.short_description = _("Script Status")
    script_status.boolean = True

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        if not request.user.is_superuser:
            my_projects = Project.get_user_projects(request.user, request)
            queryset = queryset.filter(Q(owner=request.user) | Q(project__in=my_projects))
        queryset = queryset.prefetch_related("servergroup")
        return queryset

    def get_readonly_fields(self, request, obj=None):
        fields = super().get_readonly_fields(request, obj)
        fields = list(fields)
        if not request.user.is_superuser:
            if not "owner" in fields:
                fields.append("owner")
            if not "server" in fields:
                fields.append("server")
            if not "server_assign_time" in fields:
                fields.append("server_assign_time")
        return fields


class ResultForm(ModelForm):
    class Meta:
        widgets = {
            "project": UserProjectsSelect(),
            "schedule": UserScheduleSelect(),
        }

class ResultAdmin(BaseAdminClass):
    form = ResultForm
    list_per_page = 10
    list_select_related = (None,)
    list_display = ["id", "schedule", "run_time", "success", "code", "project"]
    list_filter = [
        ("project", UserPorjectsFieldListFilter),
        ("schedule", UserSchedulesFieldListFilter),
        ("run_time", DateRangeFilter),
        ("success", BooleanFieldListFilter),
        "code",
    ]
    fieldsets = [
        (None, {
            "fields": ["project", "schedule", "run_time", "success", "code", "stdout_display", "stderr_display", "stdout_file", "stderr_file"]
        })
    ]
    actions = [
        redo_success_determination,
    ]

    class Media:
        css = {
            "all": [
                "django-crontab-manager/css/django-crontab-manager.css",
            ]
        }

    def get_fieldsets(self, request, obj=None):
        fieldsets = copy.deepcopy(super().get_fieldsets(request, obj))
        if self.has_change_permission(request, obj):
            if "stdout_display" in fieldsets[0][1]["fields"]:
                fieldsets[0][1]["fields"].remove("stdout_display")
            if "stderr_display" in fieldsets[0][1]["fields"]:
                fieldsets[0][1]["fields"].remove("stderr_display")
        else:
            if "stdout_file" in fieldsets[0][1]["fields"]:
                fieldsets[0][1]["fields"].remove("stdout_file")
            if "stderr_file" in fieldsets[0][1]["fields"]:
                fieldsets[0][1]["fields"].remove("stderr_file")
        return fieldsets

    def stdout_display(self, obj):
        text = obj.stdout()
        if text is None:
            return "-"
        else:
            return render_to_string("django_crontab_manager/output.html", {
                "text": text,
            })
    stdout_display.short_description = _("Stdout")

    def stderr_display(self, obj):
        text = obj.stderr()
        if text is None:
            return "-"
        else:
            return render_to_string("django_crontab_manager/output.html", {
                "text": text,
            })
    stderr_display.short_description = _("Stderr")

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        if not request.user.is_superuser:
            my_projects = Project.get_user_projects(request.user, request)
            queryset = queryset.filter(project__in=my_projects)
        return queryset

    def has_add_permission(self, request):
        result = super().has_add_permission(request)
        if not request.user.is_superuser:
            return False
        else:
            return result

    def has_change_permission(self, request, obj=None):
        result = super().has_change_permission(request, obj)
        if not request.user.is_superuser:
            return False
        else:
            return result

    def get_changelist_instance(self, request):
        cl = super().get_changelist_instance(request)
        schedule_ids = set()
        project_ids = set()
        schedule_mapping = {}
        project_mapping = {}
        for result in cl.result_list:
            schedule_ids.add(result.schedule_id)
            project_ids.add(result.project_id)
        if schedule_ids:
            for schedule in Schedule.objects.filter(pk__in=schedule_ids):
                schedule_mapping[schedule.pk] = schedule
        if project_ids:
            for project in Project.objects.filter(pk__in=project_ids):
                project_mapping[project.pk] = project
        for result in cl.result_list:
            result.schedule = schedule_mapping.get(result.schedule_id, None)
            result.project = project_mapping.get(result.project_id, None)
        return cl

class ProjectMemberForm(ModelForm):
    class Meta:
        widgets = {
            "user": AllUsersSelect()
        }

class ProjectMemberInline(admin.TabularInline):
    form = ProjectMemberForm
    list_display = ["user", "role", "join_time"]
    readonly_fields = ["join_time"]
    model = ProjectMember
    extra = 0

class ProjectForm(ModelForm):
    class Meta:
        widgets = {
            "owner": AllUsersSelect(),
            "variables_data": ConfigTable(),
        }


class ProjectAdmin(BaseAdminClass):
    form = ProjectForm
    list_display = ["name", "current_user_role_display"]
    search_fields = ["name"]

    inlines = [
        ProjectMemberInline,
    ]

    def current_user_role_display(self, obj):
        request = get_request()
        return obj.get_user_role_display(request.user)
    current_user_role_display.short_description = _("My Role")

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        if not request.user.is_superuser:
            queryset = queryset.filter(Q(owner=request.user) | Q(members=request.user))
        return queryset

    def get_readonly_fields(self, request, obj=None):
        fields = super().get_readonly_fields(request, obj)
        if not request.user.is_superuser:
            if not "owner" in fields:
                fields = list(fields)
                fields.append("owner")
        return fields

    def has_change_permission(self, request, obj=None):
        result = super().has_change_permission(request, obj=obj)
        if request.user.is_superuser:
            return result
        if obj is None:
            return result
        project_member_mapping = ProjectMember.get_project_member_mapping(request)
        role = obj.get_user_role(request.user, project_member_mapping)
        if role in [Project.OWNER, Project.MASTER]:
            return result
        else:
            return False

    def has_delete_permission(self, request, obj=None):
        result = super().has_change_permission(request, obj=obj)
        if request.user.is_superuser:
            return result
        if obj is None:
            return result
        project_member_mapping = ProjectMember.get_project_member_mapping(request)
        role = obj.get_user_role(request.user, project_member_mapping)
        if role in [Project.OWNER]:
            return result
        else:
            return False

admin.site.register(ServerGroup, ServerGroupAdmin)
admin.site.register(Schedule, ScheduleAdmin)
admin.site.register(Result, ResultAdmin)
admin.site.register(Project, ProjectAdmin)
