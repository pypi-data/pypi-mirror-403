from bx_django_utils.admin_extra_views.site import ExtraViewAdminSite
from django.conf import settings

from findmydevice import __version__


# Set by YunoHost app settings:
path_url = getattr(settings, 'PATH_URL', '')


class FmdAdminSite(ExtraViewAdminSite):
    site_header = f'Django Find My Device v{__version__}'
    site_title = 'Find My Device admin'
    site_url = f'/{path_url}'  # The FmdWebPageView


fmd_admin_site = FmdAdminSite(name='fmd-admin')
