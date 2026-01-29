from django.contrib import admin
from django.db.models import Count
from django.utils.translation import gettext_lazy as _

from findmydevice.admin.fmd_admin_site import fmd_admin_site
from findmydevice.admin.mixins import NoAddPermissionsMixin
from findmydevice.models import Device


@admin.register(Device, site=fmd_admin_site)
class DeviceModelAdmin(NoAddPermissionsMixin, admin.ModelAdmin):
    readonly_fields = (
        'uuid',
        'short_id',
        'hashed_password',
        'privkey',
        'pubkey',
        'user_agent',
        'command_data',
        'create_dt',
        'update_dt',
    )
    list_display = (
        'short_id',
        'name',
        'location_count',
        'last_location_date',
        'picture_count',
        'last_picture_date',
        'create_dt',
        'update_dt',
    )
    list_filter = ('name',)
    date_hierarchy = 'create_dt'
    ordering = ('-update_dt',)
    fieldsets = (
        (_('internals'), {'classes': ('collapse',), 'fields': ('uuid',)}),
        (
            _('Device info'),
            {'fields': ('short_id', 'name', 'user_agent', 'push_url', 'command_data')},
        ),
        (
            _('FMD data'),
            {
                'classes': ('collapse',),
                'fields': ('hashed_password', 'privkey', 'pubkey'),
            },
        ),
        (_('Timestamps'), {'fields': ('create_dt', 'update_dt')}),
    )

    @admin.display(description=_('Last Location'))
    def last_location_date(self, obj):
        return obj.location_set.latest().create_dt

    @admin.display(description=_('Location count'))
    def location_count(self, obj):
        return obj.location_count

    @admin.display(description=_('Picture count'))
    def picture_count(self, obj):
        return obj.picture_count

    @admin.display(description=_('Last Picture'))
    def last_picture_date(self, obj):
        return obj.picture_set.latest().create_dt

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.annotate(
            location_count=Count('location', distinct=True),
            picture_count=Count('picture', distinct=True),
        )
        return qs
