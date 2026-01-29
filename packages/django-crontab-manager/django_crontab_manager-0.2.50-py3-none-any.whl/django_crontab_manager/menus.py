from django.urls import reverse
from django.utils.translation import gettext_lazy as _

django_crontab_manager_menu_item_of_project = {
    "title": _("Manage Project"),
    "icon": "fas fa-boxes",
    "model": "django_crontab_manager.project",
    "permissions": ["django_crontab_manager.view_project"],
}
django_crontab_manager_menu_item_of_schedule = {
    "title": _("Manage Schedule"),
    "icon": "fas fa-list",
    "model": "django_crontab_manager.schedule",
    "permissions": ["django_crontab_manager.view_schedule"],
}
django_crontab_manager_menu_item_of_result = {
    "title": _("View Results"),
    "icon": "fas fa-file",
    "model": "django_crontab_manager.result",
    "permissions": ["django_crontab_manager.view_result"],
}
django_crontab_manager_menu_item_of_server_group = {
    "title": _("Manage Server Group"),
    "icon": "fas fa-server",
    "model": "django_crontab_manager.servergroup",
    "permissions": ["django_crontab_manager.view_servergroup"],
}


def default_global_menus(request=None):
    return [
        {
            "title": _("Home"),
            "icon": "fas fa-home",
            "url": reverse("admin:index"),
        },
        {
            "title": _("Crontab Manager"),
            "icon": "fas fa-edit",
            "children": [
                django_crontab_manager_menu_item_of_schedule,
                django_crontab_manager_menu_item_of_result,
            ],
        },
        {
            "title": _("Settings"),
            "icon": "fa fa-cogs",
            "children": [
                {
                    "title": _("Manage System User"),
                    "icon": "fas fa-user",
                    "model": "auth.user",
                    "permissions": [
                        "auth.view_user",
                    ],
                },
                {
                    "title": _("Manage System Group"),
                    "icon": "fas fa-users",
                    "model": "auth.group",
                    "permissions": [
                        "auth.view_group",
                    ],
                },
                django_crontab_manager_menu_item_of_server_group,
                django_crontab_manager_menu_item_of_project,
            ],
        },
    ]
