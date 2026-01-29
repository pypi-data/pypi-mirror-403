import json
import logging
import secrets
from uuid import UUID

import requests
from django.conf import settings
from django.core import validators
from django.db import IntegrityError, models, transaction
from django.utils.translation import gettext_lazy as _

from findmydevice.exceptions import InvalidShortIdError
from findmydevice.models.base import FmdBaseModel


logger = logging.getLogger(__name__)

RANDOM_STRING_CHARS = 'bcdfghjklmnpqrstvwxyz0123456789'
SHORT_ID_LENGTH = 6


def get_short_id() -> str:
    short_id = ''.join(secrets.choice(RANDOM_STRING_CHARS) for _ in range(SHORT_ID_LENGTH))
    return short_id


class DeviceManager(models.Manager):
    def create(self, **kwargs):
        """
        Create a new object with a unique "short_id"
        """
        round = 0
        for round in range(1, settings.SHORT_ID_MAX_ROUNDS + 1):
            try:
                with transaction.atomic():
                    return super().create(short_id=get_short_id(), **kwargs)
            except IntegrityError as err:
                if 'short_id' not in str(err):
                    # Some other error happens
                    raise
                logger.warning(f'short_id collision, round: {round}')

        # If we really didn't find a unique ID, we have to increase SHORT_ID_LENGTH!
        raise RuntimeError(
            f'Can not find a unique "short_id" after {round} rounds!'
            f' (Please report this error to the project!)'
        )

    def get_by_short_id(self, raw_short_id):
        if not raw_short_id:
            logger.error('No "DeviceId" aka "IDT" aka "Short ID" !')
            raise InvalidShortIdError()  # -> BadRequest

        if len(raw_short_id) == 36:  # UUID / pk?
            # TODO: Remove in the future!
            try:
                uuid = UUID(raw_short_id)
            except ValueError as err:
                logger.error('Short ID %r is no UUID: %s', raw_short_id, err)
            else:
                device = Device.objects.filter(uuid=uuid).first()
                if device:
                    logger.warning('Found device by UUID: Will be removed in the future!')
                    return device

        max_length = Device._meta.get_field('short_id').max_length
        if len(raw_short_id) > max_length:
            logger.error(
                'Short ID %r length %i is more than max length: %i',
                raw_short_id,
                len(raw_short_id),
                max_length,
            )
            raise InvalidShortIdError()  # -> BadRequest

        device = Device.objects.filter(short_id=raw_short_id).first()
        if not device:
            logger.error('Device entry not found for: %r', raw_short_id)
            raise InvalidShortIdError()  # -> BadRequest
        else:
            return device


class Device(FmdBaseModel):
    """
    In FMD project it's named "user"
    """

    short_id = models.CharField(
        max_length=SHORT_ID_LENGTH,
        unique=True,
        db_index=True,
        editable=False,
        help_text=_('Device ID used for the App and Web page to identify this device'),
        validators=[validators.MinLengthValidator(SHORT_ID_LENGTH)],
    )
    name = models.CharField(
        max_length=64,
        unique=True,
        null=True,
        blank=True,
        help_text=_('Optional Name for this Device. e.g.: Username ;) Just displayed in the admin'),
    )
    hashed_password = models.CharField(max_length=128, editable=False)
    privkey = models.TextField(editable=False)
    pubkey = models.TextField(editable=False)
    push_url = models.URLField(
        help_text=_('Push notification URL (Set by FMD app)'), blank=True, null=True
    )

    command_data = models.JSONField(
        blank=True,
        null=True,
        editable=False,
    )

    objects = DeviceManager()

    def push_notification(self, message: str, priority: int = 5):
        if not self.push_url:
            logger.error('No push URL registered for %s', self)
        else:
            json_data = {'message': message, 'priority': priority}
            logger.debug('Send push notification data for %s: %r', self, json_data)

            # Do the same "fake" encrypted WebPush request then the origin FMD server ;)
            headers = {
                'Content-Encoding': 'aes128gcm',
                'TTL': '86400',
                'Urgency': 'high',
            }
            try:
                response = requests.post(self.push_url, data=json.dumps(json_data), headers=headers)
                response.raise_for_status()
            except Exception as err:
                logger.exception('Push notification failed for %s: %s', self, err)
            else:
                logger.info('Push notification sent for %s: %r', self, response)

    def __str__(self):
        name = self.name or '>no name<'
        return f'{name} ({self.short_id or self.uuid})'
