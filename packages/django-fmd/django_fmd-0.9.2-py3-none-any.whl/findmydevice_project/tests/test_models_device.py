import logging
from unittest.mock import patch
from uuid import UUID

from django.test import TestCase, override_settings
from model_bakery import baker

from findmydevice.models import Device, device
from findmydevice.models.device import SHORT_ID_LENGTH, get_short_id
from findmydevice_project.tests.utilities import ShortIdGenerator


class DeviceModelTests(TestCase):
    def test_str_repr(self):
        device = baker.make(Device, short_id='012345', name=None)
        device.full_clean()
        assert str(device) == '>no name< (012345)'
        assert repr(device) == '<Device: >no name< (012345)>'

        device.name = 'Smartphone John'
        device.full_clean()
        assert str(device) == 'Smartphone John (012345)'
        assert repr(device) == '<Device: Smartphone John (012345)>'

    def test_get_short_id(self):
        ids = set()
        for _ in range(10):
            id = get_short_id()
            assert len(id) >= 6 >= SHORT_ID_LENGTH
            assert id not in ids  # can collide in very, very rare cases ;)
            ids.add(id)

    def test_short_id(self):
        with override_settings(SHORT_ID_MAX_ROUNDS=2), patch.object(
            device, 'get_short_id', ShortIdGenerator(ids=['000001', '000002'])
        ), self.assertRaisesMessage(
            RuntimeError, 'Can not find a unique "short_id" after 2 rounds!'
        ), self.assertLogs(
            logger='findmydevice', level=logging.WARNING
        ) as logs:
            for no in range(3):
                Device.objects.create(
                    uuid=UUID(int=no),
                    privkey=f'privkey{no}',
                    pubkey=f'pubkey{no}',
                )

        assert logs.output == [
            'WARNING:findmydevice.models.device:short_id collision, round: 1',
            'WARNING:findmydevice.models.device:short_id collision, round: 2',
        ]
        created = sorted(Device.objects.values_list('uuid', 'short_id'))
        assert created == [
            (UUID('00000000-0000-0000-0000-000000000000'), '000001'),
            (UUID('00000000-0000-0000-0000-000000000001'), '000002'),
        ]
