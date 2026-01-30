from starlette.exceptions import HTTPException
from openapi_server.token import decode_jwt, validate_roles_and_capabilities


def info_from_bearerAuth(token, required_scopes, request):

    # Check for roles and capabilities
    validate_roles_and_capabilities(token, request._starlette_request.scope['extensions']['connexion_routing']['operation_id'])

    try:
        # Return decoded token
        return decode_jwt(token)
    except Exception as ex:
        raise HTTPException(401, detail="Unauthorized")



