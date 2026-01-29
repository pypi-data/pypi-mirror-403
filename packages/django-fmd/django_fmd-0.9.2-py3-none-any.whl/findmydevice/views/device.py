import logging

from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.views import View

from findmydevice.json_utils import parse_json
from findmydevice.models import Device
from findmydevice.services.device import get_device_by_token


logger = logging.getLogger(__name__)


class DeviceView(View):
    """
    /device
    """

    def put(self, request):
        """
        Register a new Device
        """
        user_agent = request.headers.get('User-Agent')
        logger.info('New device register, user agent: %r', user_agent)

        data = parse_json(request)

        # Check the optional registration token:
        if server_token := settings.REGISTRATION_TOKEN:
            client_token = data.get('registrationToken')
            if server_token != client_token:
                logger.error(f'Wrong registration token: {client_token=} is not {server_token=}')
                return JsonResponse({'error': 'wrong registration token'}, status=400)
            else:
                logger.info('Registration token is correct')

        hashed_password = data['hashedPassword']

        device = Device.objects.create(
            hashed_password=hashed_password,
            privkey=data['privkey'],
            pubkey=data['pubkey'],
            user_agent=user_agent,
        )
        device.full_clean()
        access_token = {'DeviceId': device.short_id, 'AccessToken': ''}
        return JsonResponse(access_token)

    def post(self, request):
        """
        Delete a device
        """
        post_data = parse_json(request)

        access_token = post_data['IDT']
        device = get_device_by_token(token=access_token)
        logger.info('Delete device: %s', device)
        info = device.delete()
        logger.info('Delete info: %s', info)
        return HttpResponse(content=b'')
