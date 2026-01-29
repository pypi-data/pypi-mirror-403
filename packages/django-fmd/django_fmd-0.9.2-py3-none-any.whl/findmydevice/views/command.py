import logging

from django.http import JsonResponse
from django.views import View

from findmydevice.json_utils import parse_json
from findmydevice.models import Device
from findmydevice.services.device import get_device_by_token


logger = logging.getLogger(__name__)


class CommandView(View):
    def post(self, request):
        """
        Store a new command from the Web Page
        """
        command_data = parse_json(request)
        # e.g.: command_data = {
        #     'CmdSig': 'g2Bfr...RrH0',
        #     'Data': 'ring',
        #     'IDT': 'IIWt809IwFDc',
        #     'UnixTime': 1761599625958,
        # }

        command = command_data['Data']

        device_token = command_data['IDT']
        device: Device = get_device_by_token(token=device_token)

        device.command_data = command_data
        device.full_clean()
        device.save(update_fields=('command_data',))

        device.push_notification(message=command)

        response_data = {
            # TODO
        }
        return JsonResponse(response_data)

    def put(self, request):
        """
        Send current command back to the FMD app
        """
        app_data = parse_json(request)

        device_token = app_data['IDT']
        device: Device = get_device_by_token(token=device_token)
        command_data = device.command_data or {}
        logger.info('Send command back: %r', command_data)
        return JsonResponse(command_data)
