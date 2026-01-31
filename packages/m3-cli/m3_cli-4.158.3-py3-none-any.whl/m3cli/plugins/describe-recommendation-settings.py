"""Custom logic for the M3 describe-recommendation-settings command"""

import json
from m3cli.services.request_service import BaseRequest
from m3cli.utils.utilities import timestamp_to_iso


def create_custom_request(
        request: BaseRequest,
) -> BaseRequest:
    """
    Transforms the command parameters if necessary for M3 SDK API request.

    :param request: Dictionary with command information.
    :return: Transformed or original request for M3 SDK API.
    """
    params = request.parameters

    # Check which flags are used
    is_r_flag = params.get('R')
    is_sre_flag = params.get('SRE')

    # Validate that at least one flag is used
    if not is_r_flag and not is_sre_flag:
        raise ValueError(
            "At least one flag must be specified: '-R' (Rightsizer) or '-SRE' "
            "(Syndicate Rule Engine)"
        )

    # Extract common parameters
    tenant_name = params.get('tenantName')
    cloud = params.get('cloud')

    # Extract resource-related parameters
    region = params.get('regionName')
    resource_type = params.get('resourceType')
    resource_id = params.get('resourceId')

    # Validate interdependent resource parameters
    resource_params = [region, resource_type, resource_id]
    resource_params_set = [p for p in resource_params if p is not None]

    if resource_params_set and len(resource_params_set) != 3:
        raise ValueError(
            "If any of '--region', '--resource-type', or '--resource-id' is "
            "specified, all three must be provided"
        )

    # Build sources array based on flags
    sources = []
    if is_r_flag:
        sources.append('RIGHTSIZER')
    if is_sre_flag:
        sources.append('CUSTODIAN')

    # Build the request parameters
    new_parameters = {
        'tenantName': tenant_name,
        'cloud': cloud,
        'sources': sources
    }

    # Add optional resource parameters if all are provided
    if region and resource_type and resource_id:
        new_parameters['region'] = region
        new_parameters['resourceType'] = resource_type
        new_parameters['resourceId'] = resource_id

    # Handle Rightsizer-specific parameters
    if is_r_flag:
        categories = params.get('categories')
        if categories:
            new_parameters['categories'] = categories

    # Handle Syndicate Rule Engine-specific parameters
    if is_sre_flag:
        types = params.get('type')
        if types:
            # Map NRID to ARN for API compatibility
            mapped_types = []
            for t in types:
                if t == 'NRID':
                    mapped_types.append('ARN')
                else:
                    mapped_types.append(t)
            new_parameters['types'] = mapped_types

    # Update the request with new parameters
    request.parameters = new_parameters
    return request


def create_custom_response(
        request: BaseRequest,
        response,
):
    """
    Process the response from the API.

    :param request: The original request
    :param response: The response from the API
    :return: Processed response with converted timestamps
    """
    try:
        response = json.loads(response)
    except json.decoder.JSONDecodeError:
        return response

    # If response is a list, process each item
    if isinstance(response, list):
        for item in response:
            if isinstance(item, dict) and 'disabledUntil' in item:
                # Convert Unix timestamp to ISO format using existing function
                item['disabledUntil'] = timestamp_to_iso(item['disabledUntil'])

    # If response is a single dict object
    elif isinstance(response, dict) and 'disabledUntil' in response:
        response['disabledUntil'] = timestamp_to_iso(response['disabledUntil'])

    return response
