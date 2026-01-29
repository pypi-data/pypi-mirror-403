from bx_django_utils.test_utils.html_assertion import (
    HtmlAssertionMixin,
    assert_html_response_snapshot,
)
from django.contrib.auth.models import User
from django.http import FileResponse, HttpResponse
from django.test import TestCase, override_settings
from model_bakery import baker

import findmydevice
from findmydevice.views.version import VersionView
from findmydevice.views.web_page import FmdWebPageView


@override_settings(SECURE_SSL_REDIRECT=False)
class FmdWebPageTests(HtmlAssertionMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.normal_user = baker.make(User, is_staff=False, is_active=True, is_superuser=False)

    def test_anonymous(self):
        with self.assertLogs(logger='findmydevice') as logs:
            response = self.client.get('/')
        self.assertEqual(response.resolver_match.func.view_class, FmdWebPageView)
        self.assertRedirects(response, '/admin/login/?next=/')
        self.assertEqual(
            logs.output,
            ["INFO:findmydevice.views.web_page:User not logged in, redirect to login page"]
        )

    def test_normal_user(self):
        self.client.force_login(self.normal_user)
        response = self.client.get('/')
        assert isinstance(response, FileResponse)
        response2 = HttpResponse(response.getvalue())
        self.assert_html_parts(
            response2,
            parts=(
                '<title>Django Find My Device</title>',
                '<a href="/admin/">Go into Django Admin</a>',
                '<link rel="stylesheet" href="./static/fmd_externals/style.css">',
                '<script src="./static/fmd_externals/logic.js"></script>',
            ),
        )
        assert_html_response_snapshot(response2, query_selector=None, validate=False)

    def test_version(self):
        response = self.client.get('/api/v1/version')
        self.assertIsInstance(response, HttpResponse)
        self.assertEqual(response.resolver_match.func.view_class, VersionView)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.content.decode('ASCII'),
            f'v{findmydevice.__version__} (Django Find My Device)',
        )
