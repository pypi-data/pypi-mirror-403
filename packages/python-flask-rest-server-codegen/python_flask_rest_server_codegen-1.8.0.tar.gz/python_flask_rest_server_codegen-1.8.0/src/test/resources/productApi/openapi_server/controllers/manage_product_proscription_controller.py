from flask import request
import six

from openapi_server.models.product_proscription import ProductProscription  # noqa: E501
from openapi_server.models.product_proscription_creation_parameters import ProductProscriptionCreationParameters  # noqa: E501
from openapi_server.models.rest_error import RestError  # noqa: E501
from openapi_server import util
from openapi_server.context import create_context
from impl import manage_product_proscription_controller




def create_product_proscription(context_, product_id, body=None):  # noqa: E501
    """Create a product proscription

    **! WARNING !** this method can change the status of one or more sales-offers  # noqa: E501

    :param product_id: The id of the product concerned by the request
    :type product_id: int
    :param body: 
    :type body: dict | bytes

    :rtype: ProductProscription
    """
    context = create_context(context_)

    product_proscription_creation_parameters = body
    if request.is_json:
        product_proscription_creation_parameters = ProductProscriptionCreationParameters.from_dict(request.get_json())  # noqa: E501

    return manage_product_proscription_controller.create_product_proscription(context, product_id, product_proscription_creation_parameters)





def delete_product_proscription(context_, product_id, proscription_id):  # noqa: E501
    """Delete this product proscription

     # noqa: E501

    :param product_id: The id of the product concerned by the request
    :type product_id: int
    :param proscription_id: The id of the product proscription
    :type proscription_id: int

    :rtype: None
    """
    context = create_context(context_)


    return manage_product_proscription_controller.delete_product_proscription(context, product_id, proscription_id)


