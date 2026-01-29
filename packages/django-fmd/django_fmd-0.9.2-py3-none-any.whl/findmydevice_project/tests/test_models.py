import datetime
from unittest import mock

from bx_django_utils.test_utils.assert_queries import AssertQueries
from bx_django_utils.test_utils.datetime import MockDatetimeGenerator
from django.test import TestCase
from django.utils import timezone
from model_bakery import baker

from findmydevice.models import Device, Location


class ModelTests(TestCase):
    @mock.patch.object(timezone, 'now', MockDatetimeGenerator(datetime.timedelta(minutes=1)))
    def test_location_updates_device(self):
        with AssertQueries(query_explain=True) as queries:
            device = baker.make(Device)
        device.refresh_from_db()
        assert device.update_dt.isoformat() == '2000-01-01T00:01:00+00:00'

        queries.assert_queries(table_counts={'findmydevice_device': 1})

        with AssertQueries(query_explain=True) as queries:
            location = baker.make(Location, device=device)
        location.refresh_from_db()
        assert location.update_dt.isoformat() == '2000-01-01T00:02:00+00:00'

        # Device update datetime updated?
        device.refresh_from_db()
        assert device.update_dt.isoformat() == '2000-01-01T00:03:00+00:00'

        queries.assert_queries(table_counts={'findmydevice_location': 1, 'findmydevice_device': 1})
