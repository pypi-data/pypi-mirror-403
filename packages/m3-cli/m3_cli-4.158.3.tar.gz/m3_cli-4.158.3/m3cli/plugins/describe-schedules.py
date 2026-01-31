"""
The custom logic for the command m3 describe-schedules.
This logic is created to convert M3 SDK API response to the Human readable
format.
"""
import json

from m3cli.utils.utilities import timestamp_to_iso
from m3cli.services.request_service import BaseRequest


def create_custom_request(
        request: BaseRequest,
) -> BaseRequest:
    """
    Transforms the command parameters if necessary for M3 SDK API request.

    :param request: Dictionary with command information.
    :return: Transformed or original request for M3 SDK API.
    """
    params = request.parameters

    # Check if schedule-name is provided without region
    schedule_name = params.get('scheduleName')
    region = params.get('region')

    if schedule_name and not region:
        raise ValueError(
            "Schedule can be described by name only if region is specified. "
            "Please, specify --region (-r) parameter"
        )

    params['scheduleGroup'] = 'ALL'

    return request


def create_custom_response(request, response):
    """ Transform the command 'describe-schedules' response from M3 SDK API
    to the more human readable format.

    :param response: Server response with data as a string representation
    of a dictionary
    """
    try:
        response = json.loads(response)
    except json.decoder.JSONDecodeError:
        return response
    for item in response:
        if item.get('nextRun'):
            item['nextRun'] = timestamp_to_iso(item.get('nextRun'))
        if item.get('lastRun'):
            item['lastRun'] = timestamp_to_iso(item.get('lastRun'))

        if item.get('instances'):
            item['instances'] = [
                inst['instanceId'] for inst in item['instances']
                if inst.get('instanceId')
            ]

        if item.get('tag'):
            tag = item['tag']['key']
            if item['tag'].get('value'):
                tag += f'={item["tag"]["value"]}'
            item['tag'] = tag

        if 'region' in request.parameters:
            item.pop('region', None)
    return response
