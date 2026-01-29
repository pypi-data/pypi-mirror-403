from bx_django_utils.admin_extra_views.utils import reverse_admin_extra_view
from bx_django_utils.test_utils.html_assertion import HtmlAssertionMixin
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.test import TestCase
from model_bakery import baker

from findmydevice.admin_views import WebPageRedirectView
from findmydevice.views.web_page import FmdWebPageView


class AdminViewsTestCase(HtmlAssertionMixin, TestCase):
    def test_web_page_redirect_view(self):
        url = reverse_admin_extra_view(WebPageRedirectView)
        self.assertEqual(url, '/admin/public/find-my-device-location-web-page/')

        user = baker.make(User, is_staff=True)
        self.client.force_login(user)

        response = self.client.get(url, follow=False)
        self.assertRedirects(
            response,
            expected_url='/',
            fetch_redirect_response=False,
        )
        response = self.client.get('/', follow=False)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.resolver_match.func.view_class, FmdWebPageView)
        self.assert_html_parts(
            response=HttpResponse(b''.join(response.streaming_content)),
            parts=(
                '<title>Django Find My Device</title>',
                '<link rel="stylesheet" href="./static/fmd_externals/style.css">',
                '<script src="./static/fmd_externals/logic.js"></script>',
            ),
        )
