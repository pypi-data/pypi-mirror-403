"""
The custom logic for the command m3 describe-resources.
This logic is created to convert M3 SDK API response to the Human readable
format.
"""
import json


def create_custom_request(request):
    params = request.parameters
    cloud = params.get('cloud')
    params['resourceType'] = 'INSTANCE'

    # todo remove
    params['categories'] = []
    availability_zone = params.get('availabilityZone')
    resource_group = params.get('resourceGroup')
    if cloud == 'GOOGLE' and not availability_zone:
        raise AssertionError(
            "Parameter 'availability-zone' is required for GOOGLE cloud"
        )
    if cloud == 'AZURE' and not resource_group:
        raise AssertionError(
            "Parameter 'resource-group' is required for AZURE cloud"
        )
    return request


def create_custom_response(request, response):
    # Try to parse JSON if it's a string
    if isinstance(response, str):
        try:
            response = json.loads(response)
        except json.decoder.JSONDecodeError:
            return []

    # Return empty list if not a list
    if not isinstance(response, list):
        return []

    # Transform the response
    return [
        {
            "Category": item.get('category', ''),
            "Rist index": item.get('impact', 'UNKNOWN'),
            "Solution": item.get('solution', 'UNKNOWN'),
            "Source": item.get('source', 'UNKNOWN'),
        }
        for item in response
    ]
