"""
The custom logic for the command m3 describe-shapes.
This logic is created to convert parameters from the Human readable format to
appropriate for M3 SDK API request.
"""

import json
from m3cli.services.request_service import BaseRequest


def create_custom_request(
        request: BaseRequest,
        # view_type: str | None = None,
) -> BaseRequest:
    """
    Transforms the command parameters if necessary for M3 SDK API request.

    :param request: Dictionary with command information.
    :return: Transformed or original request for M3 SDK API.
    """
    return request


def create_custom_response(request, response):
    try:
        response = json.loads(response)
    except json.decoder.JSONDecodeError:
        return response

    for item in response:
        memory = item.get('memory')
        if memory:
            item['memoryGb'] = memory
    return response
