import logging

from django.http import JsonResponse
from django.views import View

from findmydevice.json_utils import parse_json
from findmydevice.models import Device
from findmydevice.services.device import get_device_by_token


logger = logging.getLogger(__name__)


def split_argon2_password(hashed_password: str) -> (str, str):
    """
    Split the hashed password into the actual password and the salt.

    >>> split_argon2_password("$argon2id$v=19$m=131072,t=1,p=4$the-salt$the-hashed-password")
    ('the-salt', 'the-hashed-password')
    """
    parts = hashed_password.split('$')[1:]
    assert parts[0] == 'argon2id', f'Unknown hash type: {parts[0]}'
    assert len(parts) == 5, f'Unknown hash format: {len(parts)=}'
    salt, password = parts[-2:]
    return salt, password


class SaltView(View):
    def get(self, request):
        app_data = parse_json(request)

        device_token = app_data['IDT']
        get_device_by_token(token=device_token)

        raise NotImplementedError('Not implemented yet')

    def put(self, request):
        app_data = parse_json(request)

        short_id = app_data['IDT']
        device: Device = Device.objects.get(short_id=short_id)
        hashed_password = device.hashed_password
        salt, password = split_argon2_password(hashed_password)

        response_data = {'Data': salt}
        logger.info('PUT salt: %r', response_data)
        return JsonResponse(response_data)
