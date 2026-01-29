from django.core.exceptions import BadRequest


class InvalidShortIdError(BadRequest):
    """
    Device "short_id" is invalid.
    """

    pass
