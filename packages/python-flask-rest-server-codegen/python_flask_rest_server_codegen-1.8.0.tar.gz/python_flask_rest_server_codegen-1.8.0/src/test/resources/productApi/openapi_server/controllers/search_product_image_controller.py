from flask import request
import six

from openapi_server.models.image import Image  # noqa: E501
from openapi_server.models.rest_error import RestError  # noqa: E501
from openapi_server import util
from openapi_server.context import create_context
from impl import search_product_image_controller




def get_product_image(context_, product_id, image_id):  # noqa: E501
    """Return product&#39;s images

     # noqa: E501

    :param product_id: The id of the product concerned by the request
    :type product_id: int
    :param image_id: The id of the product image concerned by the request
    :type image_id: int

    :rtype: Image
    """
    context = create_context(context_)


    return search_product_image_controller.get_product_image(context, product_id, image_id)





def get_product_images(context_, product_id):  # noqa: E501
    """Return product&#39;s images

     # noqa: E501

    :param product_id: The id of the product concerned by the request
    :type product_id: int

    :rtype: List[Image]
    """
    context = create_context(context_)


    return search_product_image_controller.get_product_images(context, product_id)


