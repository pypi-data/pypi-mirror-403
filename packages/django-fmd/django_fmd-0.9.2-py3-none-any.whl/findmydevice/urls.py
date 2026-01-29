from django.conf import settings
from django.urls import path
from django.views.static import serve

import findmydevice
from findmydevice.views.command import CommandView
from findmydevice.views.device import DeviceView
from findmydevice.views.key import KeyView
from findmydevice.views.location import GetAllLocationsView, LocationView
from findmydevice.views.location_data_size import LocationDataSizeView
from findmydevice.views.picture import PictureSizeView, PictureView
from findmydevice.views.push import PushView
from findmydevice.views.request_access import RequestAccessView
from findmydevice.views.salt import SaltView
from findmydevice.views.version import VersionView
from findmydevice.views.web_page import FmdWebPageView


VERSION_PREFIX = 'api/v1'

urlpatterns = [
    path(f'{VERSION_PREFIX}/salt', SaltView.as_view(), name='salt'),
    path(f'{VERSION_PREFIX}/command', CommandView.as_view(), name='command'),
    path(f'{VERSION_PREFIX}/location', LocationView.as_view(), name='location'),
    path(f'{VERSION_PREFIX}/locations', GetAllLocationsView.as_view(), name='locations'),
    path(f'{VERSION_PREFIX}/locationDataSize', LocationDataSizeView.as_view(), name='location_data_size'),
    path(f'{VERSION_PREFIX}/picture', PictureView.as_view(), name='picture'),
    path(f'{VERSION_PREFIX}/pictureSize', PictureSizeView.as_view(), name='picture'),
    path(f'{VERSION_PREFIX}/key', KeyView.as_view(), name='key'),
    path(f'{VERSION_PREFIX}/device', DeviceView.as_view(), name='device'),
    path(f'{VERSION_PREFIX}/push', PushView.as_view(), name='push'),
    path(f'{VERSION_PREFIX}/requestAccess', RequestAccessView.as_view(), name='request_access'),
    path(f'{VERSION_PREFIX}/version', VersionView.as_view(), name='version'),
    path('', FmdWebPageView.as_view(), name='fmd-web-page'),
]
if settings.SERVE_FILES:
    # Serve static files for development / testing purposes
    urlpatterns.append(path('<path:path>', serve, {'document_root': findmydevice.WEB_PATH}))
