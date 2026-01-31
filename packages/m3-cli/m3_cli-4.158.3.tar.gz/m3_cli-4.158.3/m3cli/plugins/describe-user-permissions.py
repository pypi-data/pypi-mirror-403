import json


def create_custom_response(request, response):
    try:
        response = json.loads(response)
    except json.decoder.JSONDecodeError:
        return response
    message = response.get('message', None)
    if response.get('permissionGroups'):
        response = response['permissionGroups']
    elif response.get('cloudServiceAccessDto'):
        response = response['cloudServiceAccessDto']
    # If there's a message, add it as metadata for the table view
    if message:
        # Add the message as a special marker that table view can recognize
        return {
            '_table_data': response,
            '_message': message
        }
    return response
