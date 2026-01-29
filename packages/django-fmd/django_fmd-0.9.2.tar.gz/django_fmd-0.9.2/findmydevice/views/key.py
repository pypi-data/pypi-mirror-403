import logging

from django.http import JsonResponse
from django.views import View

from findmydevice.json_utils import parse_json
from findmydevice.models import Device
from findmydevice.services.device import get_device_by_token


logger = logging.getLogger(__name__)


class KeyView(View):
    """
    /key
    """

    def put(self, request):
        """
        The WebPage/Client requests the private key.
        """
        put_data = parse_json(request)
        access_token = put_data['IDT']

        data = put_data.get('Data')
        logger.debug('Ignore Data=%r', data)

        device: Device = get_device_by_token(token=access_token)
        privkey = device.privkey

        response_data = {
            'IDT': access_token,
            'Data': privkey
        }
        logger.info('PUT key: %r', response_data)
        return JsonResponse(response_data)
