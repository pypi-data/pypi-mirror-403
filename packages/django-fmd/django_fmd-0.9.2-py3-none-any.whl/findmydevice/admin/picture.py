from django.conf import settings
from django.contrib import admin
from django.db.models.functions import Length
from django.template.defaultfilters import filesizeformat
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from findmydevice.admin.fmd_admin_site import fmd_admin_site
from findmydevice.admin.mixins import NoAddPermissionsMixin
from findmydevice.models import Picture


@admin.register(Picture, site=fmd_admin_site)
class PictureModelAdmin(NoAddPermissionsMixin, admin.ModelAdmin):
    # TODO: Merge code with LocationModelAdmin!

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(data_size_bytes=Length('data'))

    @admin.display(description=_('Data size'))
    def data_size_display(self, obj):
        return filesizeformat(obj.data_size_bytes or 0)

    readonly_fields = (
        'uuid',
        'device',
        'user_agent',
        'create_dt',
        'update_dt',
        'data',
        'data_size_display',
    )
    list_display = ('uuid', 'data_size_display', 'device', 'create_dt', 'update_dt')
    list_filter = ('device',)
    date_hierarchy = 'create_dt'
    ordering = ('-update_dt',)
    fieldsets = (
        (
            _('Device info'),
            {'fields': ('uuid', 'device', 'user_agent')},
        ),
        (
            _('FMD data'),
            {
                'classes': ('collapse',),
                'fields': ('data',),
            },
        ),
        (
            None,
            {'fields': ('data_size_display',)},
        ),
        (_('Timestamps'), {'fields': ('create_dt', 'update_dt')}),
    )

    def has_delete_permission(self, request, obj=None):
        """
        Should be always deleted via device deletion
        to remove all location entries for the device.
        """
        # Enable deletion in DEBUG mode:
        normal_delete = settings.DEBUG is True

        if not normal_delete:
            # A Device should be deleted via admin page.
            # Don't stop this action here:
            device_admin_url = reverse('admin:findmydevice_device_changelist')
            normal_delete = request.path == device_admin_url

        if normal_delete:
            return super().has_delete_permission(request, obj=None)

        # Deny deleting location direct:
        return False
