from flask import request
import six

from openapi_server.models.paginated_product_proscriptions import PaginatedProductProscriptions  # noqa: E501
from openapi_server.models.rest_error import RestError  # noqa: E501
from openapi_server import util
from openapi_server.context import create_context
from impl import search_product_proscription_controller




def get_product_proscriptions(context_, product_id, order_by=None, p=None, pp=None):  # noqa: E501
    """Get product proscriptions

     # noqa: E501

    :param product_id: The id of the product concerned by the request
    :type product_id: int
    :param order_by: Sort by
    :type order_by: str
    :param p: Page number to search for (start at 0)
    :type p: int
    :param pp: Number of proscriptions per page
    :type pp: int

    :rtype: PaginatedProductProscriptions
    """
    context = create_context(context_)


    return search_product_proscription_controller.get_product_proscriptions(context, product_id, order_by, p, pp)


