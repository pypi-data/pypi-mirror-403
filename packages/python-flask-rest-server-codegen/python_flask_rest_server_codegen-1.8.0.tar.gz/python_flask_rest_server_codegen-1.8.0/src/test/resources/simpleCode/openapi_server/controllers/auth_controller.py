from flask import request
import six

from openapi_server.models.credential import Credential  # noqa: E501
from openapi_server import util
from openapi_server.context import create_context
from impl import auth_controller




def login(context_, body):  # noqa: E501
    """Create a new session

     # noqa: E501

    :param body: Credentials to use in order to create the session
    :type body: dict | bytes

    :rtype: str
    """
    context = create_context(context_)

    credential = body
    if request.is_json:
        credential = Credential.from_dict(request.get_json())  # noqa: E501

    return auth_controller.login(context, credential)





def logout(context_, session_id, authorization=None):  # noqa: E501
    """Delete an existing session

     # noqa: E501

    :param session_id: Session id to delete
    :type session_id: int
    :param authorization: 
    :type authorization: str

    :rtype: None
    """
    context = create_context(context_)


    return auth_controller.logout(context, session_id, authorization)


