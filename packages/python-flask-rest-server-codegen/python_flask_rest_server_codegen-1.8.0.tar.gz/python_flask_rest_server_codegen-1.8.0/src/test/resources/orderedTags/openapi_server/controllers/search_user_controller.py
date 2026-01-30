from flask import request
import six

from openapi_server import util
from openapi_server.context import create_context
from impl import search_user_controller




def get_user(context_, user_id):  # noqa: E501
    """Retrieve one user

     # noqa: E501

    :param user_id: The id of the user concerned by the request
    :type user_id: int

    :rtype: None
    """
    context = create_context(context_)


    return search_user_controller.get_user(context, user_id)


