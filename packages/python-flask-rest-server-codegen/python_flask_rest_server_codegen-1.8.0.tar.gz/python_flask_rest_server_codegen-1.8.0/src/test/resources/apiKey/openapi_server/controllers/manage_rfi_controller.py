from flask import request
import six

from openapi_server import util
from openapi_server.context import create_context
from impl import manage_rfi_controller




def create_rfi(context_):  # noqa: E501
    """Contact form

     # noqa: E501


    :rtype: None
    """
    context = create_context(context_)


    return manage_rfi_controller.create_rfi(context)


