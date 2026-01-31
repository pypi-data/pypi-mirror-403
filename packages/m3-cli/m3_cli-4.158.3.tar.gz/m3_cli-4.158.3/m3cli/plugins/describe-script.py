"""
The custom logic for the command m3 describe-script.
This logic is created to convert parameters from the Human readable format to
appropriate for M3 SDK API request.
"""
import json

from m3cli.services.request_service import BaseRequest


def create_custom_request(
        request: BaseRequest,
        view_type: str | None = None,
) -> BaseRequest:
    params = request.parameters

    if params.get('presignedUrl'):
        if view_type != 'full':
            raise ValueError(
                "The flag '--presigned-url' can only be used with '--full' "
                "view type. Please, add the '--full' flag or remove the "
                "'--presigned-url' flag"
            )

        if params.get('fileName') is None:
            raise ValueError(
                "The flag '--presigned-url' can only be used if script is "
                "specified. Please, specify '--script' (-scname) parameter or "
                "remove the '--presigned-url' flag"
            )

    return request


def create_custom_response(
        request: BaseRequest,
        response: list | str,
) -> list | str:
    try:
        response = json.loads(response)
    except json.decoder.JSONDecodeError:
        return response

    if isinstance(response, list) and len(response) == 0:
        return 'No scripts found'

    params = request.parameters
    presigned_url = params.get('presignedUrl')

    # Ensure response is a list for uniform processing
    if isinstance(response, list):
        for each in response:
            if not each:
                return 'There is no script with such name'

            # Handle content display based on presigned URL flag
            if not each.get('content'):
                if presigned_url:
                    each['content'] = (
                        "The content is available through the provided URL. To "
                        "view the content in the CLI output, remove the "
                        "'--presigned-url' flag"
                    )
                else:
                    each['content'] = (
                        'Describe this item separately to get the content'
                    )

    response = remove_none_values(response)

    return response


def remove_none_values(obj):
    """Recursively remove all None/Null values from dicts and lists"""
    if isinstance(obj, dict):
        return {
            k: remove_none_values(v) for k, v in obj.items() if v is not None
        }
    elif isinstance(obj, list):
        return [remove_none_values(item) for item in obj if item is not None]
    else:
        return obj
