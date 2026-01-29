import logging

from django.http import HttpResponse, JsonResponse
from django.views import View

from findmydevice.json_utils import parse_json
from findmydevice.services.device import get_device_by_token


logger = logging.getLogger(__name__)


class PushView(View):
    def post(self, request):
        """
        Web page requests the push URL for the device.
        """
        app_data = parse_json(request)
        device_token = app_data['IDT']
        device = get_device_by_token(token=device_token)
        return HttpResponse(device.push_url or '')

    def put(self, request):
        """
        Register push services from the FMD app.
        """
        user_agent = request.headers.get('User-Agent')
        logger.info('Register push services, user agent: %r', user_agent)

        app_data = parse_json(request)

        device_token = app_data['IDT']
        device = get_device_by_token(token=device_token)

        push_url = app_data['Data']
        if not push_url:
            logger.error('No push URL send!')
        elif push_url == device.push_url:
            logger.info('Push URL %r already stored for %s', push_url, device)
        else:
            logger.info('Store new push URL: %r for %s', push_url, device)
            device.push_url = push_url
            if user_agent:
                device.user_agent = user_agent
            device.full_clean()
            device.save()
            device.push_notification(message='Registered FMD services successful 😀')

        response_data = {
            # TODO
        }
        return JsonResponse(response_data)
