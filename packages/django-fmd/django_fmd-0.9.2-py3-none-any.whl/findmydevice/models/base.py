import uuid as uuid

from bx_django_utils.models.timetracking import TimetrackingBaseModel
from django.db import models


class FmdBaseModel(TimetrackingBaseModel):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4)
    user_agent = models.CharField(max_length=512, blank=True, null=True, editable=False)

    class Meta:
        abstract = True
