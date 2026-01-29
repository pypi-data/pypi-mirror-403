# django-crontab-manager

Manage crontab tasks on web. Update crontab file on system while changes made on manager. Work with django-crontab-agent.

## Install

```
pip install django-crontab-manager
```

## Usage

*settings.py*

```
INSTALLED_APPS = [
    ...
    "django_apiview",
    "django_power_admin",
    "django_fastadmin",
    "django_middleware_global_request",
    "django_horizontal_list_filter",
    'django_crontab_manager',
    ...
]
```

## Usage

1. Setup django-crontab-manager at server side. django-crontab-manager is a simple django application, include it in django project.
1. Install django-crontab-agent on all target linux server.

## Releases


### v0.2.50

- Change Server to ServerGroup, so that Schedules many delivered to multiple servers.
- Store stdout and stderr info into file.
- Add Project to hodler Schedules access permission. All memebers in the same project share access permission for the Schedules under the project.
- `WARNING` Not compatible with v0.1.x. So start new server and add the Schedules to the new server and stop the old server.

### v0.1.33

- Fix getServerSettings api, add enable=True filter.

### v0.1.32

- Delete stdout/stderr columns from changelist view.

### v0.1.31

- Ignore add_time, modify_time in schedules exporting.

### v0.1.30

- Add schedules export and import.

### v0.1.26

- Add server.variables. You can use the variable in script in python format way, e.g. `curl http://{api_server}/api/xxx`.
- Add result success determination.
- Add data encryption.

### v0.1.13

- First release.
