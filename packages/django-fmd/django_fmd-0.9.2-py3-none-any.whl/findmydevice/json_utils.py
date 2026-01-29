import json
import logging
from json import JSONDecodeError


logger = logging.getLogger(__name__)


def parse_json(request):
    content_type = request.content_type
    assert content_type == 'application/json', f'Wrong content type: {content_type!r}'
    encoding = request.encoding or 'utf-8'
    json_data = request.body.decode(encoding)
    try:
        data = json.loads(json_data)
    except JSONDecodeError as err:
        logger.error('JSON decode error: "%s" Data: %r', err, json_data)
        raise
    return data
