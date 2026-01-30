from flask import request
import six

from openapi_server import util
from openapi_server.context import create_context
from impl import search_user_feature_controller




def get_user_features(context_):  # noqa: E501
    """Get features relatives to an user

     # noqa: E501


    :rtype: None
    """
    context = create_context(context_)


    return search_user_feature_controller.get_user_features(context)


