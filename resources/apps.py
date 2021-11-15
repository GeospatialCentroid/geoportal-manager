from django.apps import AppConfig

from django.contrib.admin.apps import AdminConfig

class MyAdminConfig(AdminConfig):
    default_site = 'resources.admin.MyAdminSite'

class ResourcesConfig(AppConfig):
    name = 'resources'
