import datetime
from unittest import mock
from uuid import UUID

from bx_django_utils.test_utils.datetime import MockDatetimeGenerator
from bx_django_utils.test_utils.html_assertion import (
    HtmlAssertionMixin,
    assert_html_response_snapshot,
    get_django_name_suffix,
)
from django.contrib.auth.models import User
from django.template.defaulttags import CsrfTokenNode
from django.test import TestCase, override_settings
from django.utils import timezone
from model_bakery import baker

from findmydevice import __version__
from findmydevice.models import Device, Location


class AdminAnonymousTests(TestCase):
    """
    Anonymous will be redirected to the login page.
    """

    def test_admin_append_slash_redirect(self):
        response = self.client.get('/admin', secure=True)
        self.assertRedirects(
            response,
            expected_url='/admin/',
            fetch_redirect_response=False,
            status_code=301,  # Permanent redirect
        )

    def test_login_en(self):
        response = self.client.get('/admin/', secure=True, headers={"accept-language": 'en'})
        self.assertRedirects(
            response, expected_url='/admin/login/?next=/admin/', fetch_redirect_response=False
        )

    def test_login_de(self):
        response = self.client.get('/admin/', secure=True, headers={"accept-language": 'de'})
        self.assertRedirects(
            response, expected_url='/admin/login/?next=/admin/', fetch_redirect_response=False
        )


@override_settings(SECURE_SSL_REDIRECT=False)
class AdminUserTests(HtmlAssertionMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.superuser = baker.make(User, is_staff=True, is_active=True, is_superuser=True)

    def test_superuser_access(self):
        self.client.force_login(self.superuser)

        with mock.patch.object(CsrfTokenNode, 'render', return_value='MockedCsrfTokenNode'):
            response = self.client.get('/admin/')
        self.assertTemplateUsed(response, 'admin/index.html')

        self.assert_html_parts(
            response,
            parts=(
                '<title>Site administration | Find My Device admin</title>',
                f'<a href="/admin/">Django Find My Device v{__version__}</a>',
                '<a href="/admin/findmydevice/device/">Devices</a>',
                '<a href="/admin/findmydevice/location/">Locations</a>',
            ),
        )
        assert_html_response_snapshot(response, validate=False, name_suffix=get_django_name_suffix())

    @mock.patch.object(timezone, 'now', MockDatetimeGenerator(datetime.timedelta(minutes=1)))
    def test_superuser_device(self):
        device = baker.make(Device, uuid=UUID(int=1), short_id='xyz012', name='Smartphone John')
        baker.make(Location, device=device)

        self.client.force_login(self.superuser)

        with mock.patch.object(CsrfTokenNode, 'render', return_value='MockedCsrfTokenNode'):
            response = self.client.get('/admin/findmydevice/device/')
        self.assertTemplateUsed(response, 'admin/change_list.html')

        self.assert_html_parts(
            response,
            parts=('<title>Select device to change | Find My Device admin</title>',),
        )
        assert_html_response_snapshot(response, validate=False, name_suffix=get_django_name_suffix())

    def test_superuser_location(self):
        self.client.force_login(self.superuser)

        with mock.patch.object(CsrfTokenNode, 'render', return_value='MockedCsrfTokenNode'):
            response = self.client.get('/admin/findmydevice/location/')
        self.assertTemplateUsed(response, 'admin/change_list.html')

        self.assert_html_parts(
            response,
            parts=('<title>Select location to change | Find My Device admin</title>',),
        )
        assert_html_response_snapshot(response, validate=False, name_suffix=get_django_name_suffix())
