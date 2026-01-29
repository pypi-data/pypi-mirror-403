from bx_django_utils.admin_extra_views.registry import extra_view_registry
from django.conf import settings
from django.conf.urls import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

from findmydevice.admin.fmd_admin_site import fmd_admin_site


admin.autodiscover()

urlpatterns = [  # Don't use i18n_patterns() here
    path('admin', RedirectView.as_view(url='/admin/', permanent=True)),
    path('admin/', include(extra_view_registry.get_urls())),
    path('admin/', fmd_admin_site.urls),
    path('', include('findmydevice.urls')),
]


if settings.SERVE_FILES:
    urlpatterns += static.static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)


if 'debug_toolbar' in settings.INSTALLED_APPS:
    import debug_toolbar

    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
