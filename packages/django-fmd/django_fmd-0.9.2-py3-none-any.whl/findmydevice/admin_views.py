from bx_django_utils.admin_extra_views.base_view import AdminExtraViewMixin
from bx_django_utils.admin_extra_views.datatypes import AdminExtraMeta, PseudoApp
from bx_django_utils.admin_extra_views.registry import register_admin_view
from django.urls import reverse
from django.views.generic import RedirectView


public_app = PseudoApp(meta=AdminExtraMeta(name='public'))


@register_admin_view(pseudo_app=public_app)
class WebPageRedirectView(AdminExtraViewMixin, RedirectView):
    meta = AdminExtraMeta(name='Find My Device - Location Web Page')

    def get_redirect_url(self):
        return reverse('fmd-web-page')
