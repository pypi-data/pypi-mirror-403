from django.conf import settings


class NoAddPermissionsMixin:
    """
    User can add only if DEBUG is on
    """

    def has_add_permission(self, request):
        if settings.DEBUG:
            return super().has_add_permission(request)
        return False
