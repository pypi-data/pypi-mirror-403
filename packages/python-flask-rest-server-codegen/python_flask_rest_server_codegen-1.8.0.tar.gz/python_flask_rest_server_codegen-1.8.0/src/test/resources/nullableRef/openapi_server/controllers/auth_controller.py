from flask import request
import six

from openapi_server import util
from openapi_server.context import create_context
from impl import auth_controller




def get_sessions(context_):  # noqa: E501
    """get_sessions

     # noqa: E501


    :rtype: List
    """
    context = create_context(context_)


    return auth_controller.get_sessions(context)


