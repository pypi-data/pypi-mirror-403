"""Custom logic for the M3 remove-recommendation-settings command"""

import json
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

    # Check which flags are used
    is_r_flag = params.get('R')
    is_sre_flag = params.get('SRE')

    # Validate that at least one flag is used
    if not is_r_flag and not is_sre_flag:
        raise ValueError(
            "At least one flag must be specified: '-R' (Rightsizer) or '-SRE' "
            "(Syndicate Rule Engine)"
        )

    # Validate that only one flag is used at a time
    if is_r_flag and is_sre_flag:
        raise ValueError(
            "Only one flag can be specified at a time: '-R' (Rightsizer) or '-SRE' "
            "(Syndicate Rule Engine)"
        )

    # Extract common parameters
    tenant_name = params.get('tenantName')
    cloud = params.get('cloud')
    action = 'REMOVE'

    settings = []

    # Handle Rightsizer flag
    if is_r_flag:
        source = 'RIGHTSIZER'

        # Validate required parameters for -R
        region = params.get('regionName')
        resource_type = params.get('resourceType')
        resource_id = params.get('resourceId')
        categories = params.get('categories', [])

        if not region:
            raise ValueError("'--region' is required when using '-R' flag")
        if not resource_type:
            raise ValueError(
                "'--resource-type' is required when using '-R' flag"
            )
        if not resource_id:
            raise ValueError("'--resource-id' is required when using '-R' flag")
        if not categories:
            raise ValueError("'--category' is required when using '-R' flag")

        # Build settings for each category
        for category in categories:
            setting = {
                'regionName': region,
                'source': source,
                'resourceType': resource_type,
                'resourceId': resource_id,
                'category': category
            }
            settings.append(setting)

    # Handle Syndicate Rule Engine flag
    if is_sre_flag:
        source = 'CUSTODIAN'

        # Get the recommendation IDs list
        rec_ids = params.get('recId')
        if not rec_ids:
            raise ValueError(
                "'--recommendation-id' is required when using '-SRE' flag"
            )

        # Process each recommendation ID
        for recommendation_id in rec_ids:
            setting = {
                'source': source,
                'id': recommendation_id,
            }
            settings.append(setting)

    # Validate that we have at least one setting
    if not settings:
        raise ValueError(
            "No valid settings were created. Please check your parameters"
        )

    # Build the new parameters structure
    new_parameters = {
        'tenantName': tenant_name,
        'cloud': cloud,
        'settings': settings,
        'action': action
    }

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
    :return: Processed response
    """
    try:
        response = json.loads(response)
    except json.decoder.JSONDecodeError:
        return response
    return response
