from starlette.exceptions import HTTPException
from openapi_server.token import decode_jwt, validate_roles_and_capabilities

def info_from_apiKeyAuth(api_key, required_scopes):
    """
    Check and retrieve authentication information from api_key.
    Returned value will be passed in 'token_info' parameter of your operation function, if there is one.
    'sub' or 'uid' will be set in 'user' parameter of your operation function, if there is one.

    :param api_key API key provided by Authorization header
    :type api_key: str
    :param required_scopes Always None. Used for other authentication method
    :type required_scopes: None
    :return: Information attached to provided api_key or None if api_key is invalid or does not allow access to called API
    :rtype: dict | None
    """
    return resole_api_key_auth('apiKeyAuth', api_key, required_scopes)

def resole_api_key_auth(name, api_key, required_scopes):
    if name == 'apiKeyAuth':
        # Do magic
        raise NotImplemented()
    elif name == 'apiKeyCaptcha':
        # Do magic
        raise NotImplemented()

    raise NotImplemented()


def info_from_bearerAuth(token, required_scopes, request):

    # Check for roles and capabilities
    validate_roles_and_capabilities(token, request._starlette_request.scope['extensions']['connexion_routing']['operation_id'])

    try:
        # Return decoded token
        return decode_jwt(token)
    except Exception as ex:
        raise HTTPException(401, detail="Unauthorized")



def info_from_captchaApiKey(api_key, required_scopes):
    """
    Check and retrieve authentication information from api_key.
    Returned value will be passed in 'token_info' parameter of your operation function, if there is one.
    'sub' or 'uid' will be set in 'user' parameter of your operation function, if there is one.

    :param api_key API key provided by Authorization header
    :type api_key: str
    :param required_scopes Always None. Used for other authentication method
    :type required_scopes: None
    :return: Information attached to provided api_key or None if api_key is invalid or does not allow access to called API
    :rtype: dict | None
    """
    return resole_api_key_auth('captchaApiKey', api_key, required_scopes)


