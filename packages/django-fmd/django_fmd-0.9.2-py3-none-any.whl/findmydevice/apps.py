from django.apps import AppConfig as BaseAppConfig


class AppConfig(BaseAppConfig):
    name = 'findmydevice'
    verbose_name = 'django-fmd'

    def ready(self):
        import findmydevice.checks  # noqa
