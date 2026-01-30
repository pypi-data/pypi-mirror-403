from flask import request
import six

from openapi_server import util
from openapi_server.context import create_context
from impl import auth_controller




def delete_route(context_):  # noqa: E501
    """Delete route

     # noqa: E501


    :rtype: None
    """
    context = create_context(context_)


    return auth_controller.delete_route(context)





def get_route(context_):  # noqa: E501
    """Get route

     # noqa: E501


    :rtype: str
    """
    context = create_context(context_)


    return auth_controller.get_route(context)





def post_route(context_):  # noqa: E501
    """Create route

     # noqa: E501


    :rtype: str
    """
    context = create_context(context_)


    return auth_controller.post_route(context)


