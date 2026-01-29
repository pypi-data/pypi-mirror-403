import logging
from unittest.mock import patch

from django.test import LiveServerTestCase, override_settings

import findmydevice
from findmydevice.client.client import FmdClient
from findmydevice.client.data_classes import ClientDeviceData
from findmydevice.models import Device


@override_settings(SECURE_SSL_REDIRECT=False)
class FmdClientTest(LiveServerTestCase):
    def _get_fmd_client(self) -> FmdClient:
        fmd_client = FmdClient(
            fmd_server_url=self.live_server_url,
            raise_wrong_responses=True,
            ssl_verify=False,
        )
        return fmd_client

    ####################################################################################################
    # Low level requests

    def test_get_version(self):
        fmd_client = self._get_fmd_client()
        version = fmd_client.get_version()
        self.assertEqual(version, f'v{findmydevice.__version__} (Django Find My Device)')

    def test_assume_salt(self):
        device = Device.objects.create(
            name='Test Device 1',
            hashed_password=(
                '$argon2id$v=19$m=131072,t=1,p=4$YeAM+gUcbAdm5UKles3Ldw$W+m4nT7UK/T6h9PUxQRxyEo8AQ9aHr9YgQAlSzspin4'
            ),
        )
        device.full_clean()

        client_device_data = ClientDeviceData(short_id=device.short_id)

        fmd_client = self._get_fmd_client()
        with self.assertLogs('findmydevice', level=logging.INFO) as cm:
            fmd_client.assume_salt(client_device_data=client_device_data)
        self.assertEqual(client_device_data.password_salt, 'YeAM+gUcbAdm5UKles3Ldw')
        self.assertEqual(
            cm.output,
            ["INFO:findmydevice.views.salt:PUT salt: {'Data': 'YeAM+gUcbAdm5UKles3Ldw'}"],
        )

    def test_assume_hash_password4login(self):
        device = Device.objects.create(
            name='Test Device 1',
            hashed_password=(
                '$argon2id$v=19$m=131072,t=1,p=4$YeAM+gUcbAdm5UKles3Ldw$W+m4nT7UK/T6h9PUxQRxyEo8AQ9aHr9YgQAlSzspin4'
            ),
        )
        device.full_clean()

        client_device_data = ClientDeviceData(
            short_id=device.short_id,
            plaintext_password='pp',
        )

        fmd_client = self._get_fmd_client()
        with self.assertLogs('findmydevice', level=logging.INFO) as cm:
            fmd_client.assume_hash_password4login(client_device_data=client_device_data)
        self.assertEqual(
            client_device_data.hashed_password,
            '$argon2id$v=19$m=131072,t=1,p=4$YeAM+gUcbAdm5UKles3Ldw$W+m4nT7UK/T6h9PUxQRxyEo8AQ9aHr9YgQAlSzspin4',
        )
        self.assertEqual(
            cm.output,
            [
                "INFO:findmydevice.views.salt:PUT salt: {'Data': 'YeAM+gUcbAdm5UKles3Ldw'}",
                'INFO:findmydevice.client.client:Calculate hashed password...',
            ],
        )

    def test_get_access_token(self):
        device = Device.objects.create(
            name='Test Device 1',
            hashed_password=(
                '$argon2id$v=19$m=131072,t=1,p=4$YeAM+gUcbAdm5UKles3Ldw$W+m4nT7UK/T6h9PUxQRxyEo8AQ9aHr9YgQAlSzspin4'
            ),
        )
        device.full_clean()

        client_device_data = ClientDeviceData(
            short_id=device.short_id,
            hashed_password=device.hashed_password,
        )

        fmd_client = self._get_fmd_client()
        with (
            patch('findmydevice.services.device.get_random_string', return_value='ABC12345'),
            self.assertLogs('findmydevice', level=logging.INFO) as cm,
        ):
            access_token = fmd_client.get_access_token(client_device_data=client_device_data)
        self.assertEqual(access_token, 'ABC12345')
        self.assertEqual(
            cm.output,
            [
                f'INFO:findmydevice.views.request_access:Password OK for Test Device 1 ({device.short_id})',
                (
                    'INFO:findmydevice.services.device:'
                    f"Store access token 'ABC12345' for Test Device 1 ({device.short_id}) (timeout: 300 sec)"
                ),
            ],
        )
