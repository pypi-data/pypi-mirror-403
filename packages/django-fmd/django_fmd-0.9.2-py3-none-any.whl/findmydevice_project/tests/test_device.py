from django.conf import settings
from django.test import TestCase

from findmydevice.models import Device
from findmydevice.views.device import DeviceView


class DeviceViewTestCase(TestCase):

    def test_register_new_device_with_valid_data(self):
        response = self.client.put(
            '/api/v1/device',
            data={
                'hashedPassword': '$argon2id$v=19$m=131072,t=1,p=4$the-salt$the-hashed-password',
                'privkey': 'private-key',
                'pubkey': 'public-key',
                'registrationToken': settings.REGISTRATION_TOKEN,
            },
            content_type='application/json',
        )
        self.assertEqual(response.resolver_match.func.view_class, DeviceView)
        self.assertEqual(response.status_code, 200)
        access_token = response.json()
        short_id = access_token['DeviceId']
        self.assertEqual(access_token['AccessToken'], '')

        device = Device.objects.get()
        self.assertEqual(device.short_id, short_id)
        self.assertEqual(device.privkey, 'private-key')
        self.assertEqual(device.pubkey, 'public-key')
        self.assertEqual(device.hashed_password, '$argon2id$v=19$m=131072,t=1,p=4$the-salt$the-hashed-password')
