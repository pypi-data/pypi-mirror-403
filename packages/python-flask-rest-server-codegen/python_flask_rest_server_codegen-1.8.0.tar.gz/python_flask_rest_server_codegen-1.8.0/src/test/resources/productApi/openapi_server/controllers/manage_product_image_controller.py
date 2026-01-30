from flask import request
import six

from openapi_server import util
from openapi_server.context import create_context
from impl import manage_product_image_controller




def create_product_image(context_, product_id, images=None):  # noqa: E501
    """Upload one or more images

     # noqa: E501

    :param product_id: The id of the product concerned by the request
    :type product_id: int
    :param images: File to upload related to image type (Max 10 Mo)
    :type images: List[str]

    :rtype: None
    """
    context = create_context(context_)


    return manage_product_image_controller.create_product_image(context, product_id, images)





def delete_product_image(context_, product_id, image_id):  # noqa: E501
    """Remove product&#39;s image

     # noqa: E501

    :param product_id: The id of the product concerned by the request
    :type product_id: int
    :param image_id: The id of the product image concerned by the request
    :type image_id: int

    :rtype: None
    """
    context = create_context(context_)


    return manage_product_image_controller.delete_product_image(context, product_id, image_id)


