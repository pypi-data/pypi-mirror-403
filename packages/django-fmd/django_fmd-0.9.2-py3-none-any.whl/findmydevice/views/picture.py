import logging

from django.http import HttpResponse, JsonResponse
from django.views import View

from findmydevice.json_utils import parse_json
from findmydevice.models import Picture
from findmydevice.services.device import get_device_by_token


logger = logging.getLogger(__name__)


class PictureView(View):
    """
    /picture
    """

    def post(self, request):
        """
        Store a new picture from the device
        """
        user_agent = request.headers.get('User-Agent')
        logger.info('Store new picture, user agent: %r', user_agent)

        picture_data = parse_json(request)
        access_token = picture_data['IDT']
        device = get_device_by_token(token=access_token)

        data = picture_data['Data']
        assert data, 'Picture data is empty'

        picture = Picture.objects.create(
            device=device,
            data=data,
            user_agent=user_agent,
        )
        picture.full_clean()
        logger.info('New picture stored: %s', picture)

        return HttpResponse(content=b'')

    def put(self, request):
        """
        Send one picture back to the FMD web page
        """
        picture_data = parse_json(request)
        access_token = picture_data['IDT']
        raw_index = picture_data.get('Data', '-1')
        if raw_index == 'NaN':
            logger.warning('Convert picture index "NaN" to -1')
            index = -1
        else:
            index = int(picture_data['Data'])
        logger.info('Picture index: %r', index)

        device = get_device_by_token(token=access_token)

        queryset = Picture.objects.filter(device=device).order_by('create_dt')
        count = queryset.count()
        if index >= count:
            logger.error('Picture index %r is more than count: %r', index, count)
            index = count - 1

        if index == -1:
            logger.info('Use latest picture (index=-1)')
            picture = queryset.latest()
        else:
            picture = queryset[index]

        return HttpResponse(picture.data)


class PictureSizeView(View):
    def put(self, request):
        picture_data = parse_json(request)
        access_token = picture_data['IDT']
        device = get_device_by_token(token=access_token)
        location_count = Picture.objects.filter(device=device).count()
        response_data = {'Data': location_count}
        logger.info('PUT PictureSize: %r', response_data)
        return JsonResponse(response_data)
