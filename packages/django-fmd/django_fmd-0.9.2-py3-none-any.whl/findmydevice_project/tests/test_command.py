from django.test import TestCase
from model_bakery import baker

from findmydevice.models import Device
from findmydevice.services.device import new_access_token
from findmydevice.views.command import CommandView


class CommandViewTestCase(TestCase):
    def test_put_command(self):
        with self.assertLogs('django'), self.assertLogs(logger='findmydevice') as logs:
            response = self.client.put(
                '/api/v1/command',
                data={'IDT': 'ktmfs8'},
                content_type='application/json',
            )
        self.assertEqual(response.resolver_match.func.view_class, CommandView)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            logs.output,
            [
                "ERROR:findmydevice.services.device:Token 'ktmfs8' not valid or expired",
            ],
        )

        device = baker.make(Device, short_id='ktmfs8', command_data=None)
        device.full_clean()

        with self.assertLogs(logger='findmydevice'):
            token = new_access_token(device)
            response = self.client.put(
                '/api/v1/command',
                data={'IDT': token},
                content_type='application/json',
            )
        self.assertEqual(response.resolver_match.func.view_class, CommandView)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {})

        device.refresh_from_db()
        self.assertIs(device.command_data, None)

        with self.assertLogs(logger='findmydevice'):
            response = self.client.post(
                '/api/v1/command',
                data={
                    'CmdSig': 'g2Bfr...RrH0',
                    'Data': 'ring',
                    'IDT': token,
                    'UnixTime': 1761599625958,
                },
                content_type='application/json',
            )
        self.assertEqual(response.resolver_match.func.view_class, CommandView)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {})

        device.refresh_from_db()
        self.assertEqual(
            device.command_data,
            {
                'CmdSig': 'g2Bfr...RrH0',
                'Data': 'ring',
                'IDT': token,
                'UnixTime': 1761599625958,
            },
        )
