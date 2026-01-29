import logging

from django.http import HttpResponseBadRequest, HttpResponseForbidden, JsonResponse
from django.views import View

from findmydevice.json_utils import parse_json
from findmydevice.models import Device
from findmydevice.services.device import new_access_token


logger = logging.getLogger(__name__)


class RequestAccessView(View):
    """
    /requestAccess
    """

    def put(self, request):  # TODO: Add lock here!
        """
        Response access token.
        """
        access_data = parse_json(request)

        hashed_password = access_data.get('HashedPassword') or access_data.get('Data')
        if not hashed_password:
            logger.error('No hashed password from "HashedPassword" or "Data" !')
            return HttpResponseBadRequest()

        raw_short_id = access_data.get('DeviceId') or access_data.get('IDT')
        device = Device.objects.get_by_short_id(raw_short_id=raw_short_id)

        if hashed_password != device.hashed_password:
            logger.error(
                'Wrong password %r is not %r for %s',
                hashed_password,
                device.hashed_password,
                device,
            )
            return HttpResponseForbidden()
        else:
            logger.info('Password OK for %s', device)

        access_token = new_access_token(device=device)
        access_token_reply = {'IDT': device.short_id, 'Data': access_token}
        return JsonResponse(access_token_reply)
