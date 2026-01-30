from flask import request
import six

from openapi_server.models.product_secondary_type import ProductSecondaryType  # noqa: E501
from openapi_server.models.product_type import ProductType  # noqa: E501
from openapi_server.models.rest_error import RestError  # noqa: E501
from openapi_server import util
from openapi_server.context import create_context
from impl import search_product_metadata_controller




def get_product_secondary_types(context_):  # noqa: E501
    """Get product secondary types

     # noqa: E501


    :rtype: List[ProductSecondaryType]
    """
    context = create_context(context_)


    return search_product_metadata_controller.get_product_secondary_types(context)





def get_product_types(context_):  # noqa: E501
    """Get product types

     # noqa: E501


    :rtype: List[ProductType]
    """
    context = create_context(context_)


    return search_product_metadata_controller.get_product_types(context)


