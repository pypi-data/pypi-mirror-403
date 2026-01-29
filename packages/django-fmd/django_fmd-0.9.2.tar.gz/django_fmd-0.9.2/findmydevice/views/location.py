import logging

from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.views import View

from findmydevice.json_utils import parse_json
from findmydevice.models import Location
from findmydevice.services.device import get_device_by_token


logger = logging.getLogger(__name__)


class LocationView(View):
    """
    /location
    """

    def post(self, request):
        """
        Store a new location from device
        """
        user_agent = request.headers.get('User-Agent')
        logger.info('Store new location, user agent: %r', user_agent)

        location_data = parse_json(request)

        access_token = location_data['IDT']
        device = get_device_by_token(token=access_token)

        data = location_data['Data']
        assert data, 'Location data is empty'

        now = timezone.now()
        past = now - timezone.timedelta(seconds=settings.FMD_MIN_LOCATION_DATE_RANGE_SEC)
        qs = Location.objects.filter(device=device)
        qs = qs.filter(create_dt__gt=past)
        if qs.exists():
            logger.warning(
                'Skip location, because of FMD_MIN_LOCATION_DATE_RANGE_SEC=%i',
                settings.FMD_MIN_LOCATION_DATE_RANGE_SEC,
            )
        else:
            location = Location.objects.create(
                device=device,
                data=data,
                user_agent=user_agent,
            )
            location.full_clean()
            logger.info('New location stored: %s', location)

        return HttpResponse(content=b'')

    def put(self, request):
        """
        Send one location back to the FMD web page
        """
        location_data = parse_json(request)
        access_token = location_data['IDT']
        raw_index = location_data.get('Data', '-1')
        if raw_index == 'NaN':
            logger.warning('Convert location index "NaN" to -1')
            index = -1
        else:
            index = int(location_data['Data'])
        logger.info('Location index: %r', index)

        device = get_device_by_token(token=access_token)

        queryset = Location.objects.filter(device=device).order_by('create_dt')
        count = queryset.count()
        if index >= count:
            logger.error('Location index %r is more than count: %r', index, count)
            index = count - 1

        if index == -1:
            logger.info('Use latest location (index=-1)')
            location = queryset.latest()
        else:
            location = queryset[index]

        response_data = {'Data': location.data}
        logger.info('PUT location (index:%r pk:%r): %r', index, location.pk, response_data)
        return JsonResponse(response_data)


class GetAllLocationsView(View):
    """
    /locations
    """

    def post(self, request):
        """
        Web page request to get all locations for a device
        """
        location_data = parse_json(request)
        access_token = location_data['IDT']
        device = get_device_by_token(token=access_token)

        locations = Location.objects.filter(device=device).order_by('create_dt').values_list('data', flat=True)
        response_data = list(locations)
        return JsonResponse(
            response_data,
            safe=False,  # Allow to serialize non-dict objects
        )
