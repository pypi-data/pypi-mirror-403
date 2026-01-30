from flask import request
import six

from openapi_server.models.any_mode import AnyMode  # noqa: E501
from openapi_server import util
from openapi_server.context import create_context
from impl import default_controller




def get_mode(context_):  # noqa: E501
    """get_mode

     # noqa: E501


    :rtype: AnyMode
    """
    context = create_context(context_)


    return default_controller.get_mode(context)


