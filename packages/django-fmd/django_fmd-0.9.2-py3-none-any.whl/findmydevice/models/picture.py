import logging

from django.db import models

from findmydevice.models import Device
from findmydevice.models.base import FmdBaseModel


logger = logging.getLogger(__name__)


class Picture(FmdBaseModel):
    # TODO: Merge code with Location model!

    device = models.ForeignKey(Device, on_delete=models.CASCADE)
    data = models.TextField(editable=False)

    def save(self, **kwargs):
        super().save(**kwargs)

        # Update "device.update_dt" field: So the admin change list will order the devices
        # by last location update ;)
        self.device.save(update_dt=True)

    def __str__(self):
        return f'Picture {self.uuid} for {self.device} ({self.create_dt})'

    def __repr__(self):
        return f'<{self.__str__()}>'

    class Meta:
        get_latest_by = ['create_dt']
