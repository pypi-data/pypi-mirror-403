"""Custom logic for the M3 update-recommendation-settings command"""

import json
from m3cli.services.request_service import BaseRequest
from m3cli.plugins import validate_disabled_until_date


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
            "Only one flag can be specified at a time: '-R' (Rightsizer) or "
            "'-SRE' (Syndicate Rule Engine)"
        )

    # Validate flag-specific parameters are not mixed
    if is_sre_flag:
        # Check if -R exclusive parameters are used with -SRE
        if params.get('categories'):
            raise ValueError(
                "Parameter '--category' (-cat) can only be used with '-R' flag,"
                " not with '-SRE' flag"
            )

    if is_r_flag:
        # Check if -SRE exclusive parameters are used with -R
        if params.get('type'):
            raise ValueError(
                "Parameter '--type' (-t) can only be used with '-SRE' flag, not"
                " with '-R' flag"
            )
        if params.get('recId'):
            raise ValueError(
                "Parameter '--recommendation-id' (-recid) can only be used with"
                " '-SRE' flag, not with '-R' flag"
            )
        if params.get('tags'):
            raise ValueError(
                "Parameter '--tag' can only be used with '-SRE' flag, not with"
                " '-R' flag"
            )
        if params.get('nativeResourceId'):
            raise ValueError(
                "Parameter '--nrid' can only be used with '-SRE' flag, not with"
                " '-R' flag"
            )

    # Extract common parameters
    tenant_name = params.get('tenantName')
    cloud = params.get('cloud')
    disabled_until = params.get('disabledUntil')
    action = 'UPDATE'

    # Validate disabledUntil timestamp if provided
    validate_disabled_until_date(disabled_until)

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
                'category': category,
                'disabledUntil': disabled_until,
            }
            settings.append(setting)

    # Handle Syndicate Rule Engine flag
    if is_sre_flag:
        source = 'CUSTODIAN'

        # Get recommendation ID and type
        recommendation_id = params.get('recId')
        rec_type = params.get('type')

        # Validate required parameters for -SRE
        if not recommendation_id:
            raise ValueError(
                "'--recommendation-id' is required when using '-SRE' flag"
            )
        if not rec_type:
            raise ValueError("'--type' is required when using '-SRE' flag")

        # Process based on type
        if rec_type.upper() == 'TAG_FILTER':
            # Validate required parameters for TAG_FILTER
            tags = params.get('tags')
            if not tags:
                raise ValueError(
                    "'--tag' is required when using '-SRE' with "
                    "'--type TAG_FILTER'"
                )

            # Convert tags to list format expected by API
            tags_list = []
            for key, value in tags.items():
                tags_list.append({
                    'key': key,
                    'value': value,
                })

            setting = {
                'source': source,
                'id': recommendation_id,
                'type': 'TAG_FILTER',
                'tags': tags_list,
                'disabledUntil': disabled_until,
            }
            settings.append(setting)

        elif rec_type.upper() == 'RESOURCE':
            # Validate required parameters for RESOURCE
            region = params.get('regionName')
            resource_type = params.get('resourceType')
            resource_id = params.get('resourceId')

            if not region:
                raise ValueError(
                    "'--region' is required when using '-SRE' with "
                    "'--type RESOURCE'"
                )
            if not resource_type:
                raise ValueError(
                    "'--resource-type' is required when using '-SRE' with "
                    "'--type RESOURCE'"
                )
            if not resource_id:
                raise ValueError(
                    "'--resource-id' is required when using '-SRE' with "
                    "'--type RESOURCE'"
                )

            setting = {
                'source': source,
                'id': recommendation_id,
                'type': 'RESOURCE',
                'regionName': region,
                'resourceType': resource_type,
                'resourceId': resource_id,
                'disabledUntil': disabled_until,
            }
            settings.append(setting)

        elif rec_type.upper() == 'NRID':
            # Validate required parameters for NRID (ARN)
            nrid = params.get('nativeResourceId')
            if not nrid:
                raise ValueError(
                    "'--nrid' is required when using '-SRE' with '--type NRID'"
                )

            setting = {
                'source': source,
                'id': recommendation_id,
                'type': 'ARN',
                'resourceId': nrid,
                'disabledUntil': disabled_until,
            }
            settings.append(setting)

        else:
            raise ValueError(
                f"Unknown type: '{rec_type}'. Allowed values: "
                f"TAG_FILTER, RESOURCE, NRID"
            )

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
        'action': action,
    }

    # Update the request with new parameters
    request.parameters = new_parameters
    return request


def create_custom_response(
        request: BaseRequest,
        response,
        # view_type: str | None = None,
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
