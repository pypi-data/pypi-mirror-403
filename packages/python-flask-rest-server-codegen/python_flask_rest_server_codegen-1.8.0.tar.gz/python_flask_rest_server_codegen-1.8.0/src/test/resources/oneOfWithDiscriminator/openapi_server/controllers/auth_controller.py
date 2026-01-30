from flask import request
import six

from openapi_server.models.any_authentication_credential import AnyAuthenticationCredential  # noqa: E501
from openapi_server import util
from openapi_server.context import create_context
from impl import auth_controller




def login(context_, body):  # noqa: E501
    """Create a new session

     # noqa: E501

    :param body: Credentials to use in order to create the session
    :type body: dict | bytes

    :rtype: None
    """
    context = create_context(context_)

    any_authentication_credential = body
    if request.is_json:
        any_authentication_credential = AnyAuthenticationCredential.from_dict(request.get_json())  # noqa: E501

    return auth_controller.login(context, any_authentication_credential)


