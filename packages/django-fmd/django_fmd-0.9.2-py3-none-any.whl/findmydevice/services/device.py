import logging

from django.conf import settings
from django.core.cache import cache
from django.http import Http404
from django.utils.crypto import get_random_string

from findmydevice.models import Device


logger = logging.getLogger(__name__)


ACCESS_TOKEN_LENGTH = 12


def _make_cache_key(token):
    cache_key = f'access_token_{token}'
    logger.debug('Cache key: %r', cache_key)
    return cache_key


def get_device_by_token(token):
    device_uuid = cache.get(key=_make_cache_key(token))
    if device_uuid:
        logger.debug('Token %r == %r', token, device_uuid)
        device = Device.objects.filter(uuid=device_uuid).first()
        if device:
            logger.debug('Found device %s for token %r', device, token)
            return device
        else:
            logger.error('Device not found for token: %r', token)
    else:
        logger.error('Token %r not valid or expired', token)

    raise Http404


def new_access_token(device: Device):
    token = get_random_string(length=ACCESS_TOKEN_LENGTH)
    timeout = settings.FMD_ACCESS_TOKEN_TIMEOUT_SEC
    cache.set(key=_make_cache_key(token), value=device.uuid, timeout=timeout)
    logger.info('Store access token %r for %s (timeout: %i sec)', token, device, timeout)
    return token
