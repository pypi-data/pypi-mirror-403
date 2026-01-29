import logging

from django.http import HttpResponseBadRequest, JsonResponse
from django.views import View

from findmydevice.json_utils import parse_json
from findmydevice.models import Location
from findmydevice.services.device import get_device_by_token


logger = logging.getLogger(__name__)


class LocationDataSizeView(View):
    """
    /locationDataSize
    """

    def put(self, request):
        """
        Send information how many location are stored for one device
        to the FMD web page.
        """
        put_data = parse_json(request)
        try:
            access_token = put_data['IDT']
        except KeyError:
            # https://gitlab.com/fmd-foss/fmd-server/-/issues/11
            logger.warning('No "IDT" in: %r', put_data)
            return HttpResponseBadRequest()

        data = put_data.get('Data')
        if data != 'unused':
            logger.warning('Get locationDataSize with Data!="unused" ... Data is: %r', data)

        device = get_device_by_token(token=access_token)
        location_count = Location.objects.filter(device=device).count()
        response_data = {'Data': location_count}
        logger.info('PUT locationDataSize: %r', response_data)
        return JsonResponse(response_data)
