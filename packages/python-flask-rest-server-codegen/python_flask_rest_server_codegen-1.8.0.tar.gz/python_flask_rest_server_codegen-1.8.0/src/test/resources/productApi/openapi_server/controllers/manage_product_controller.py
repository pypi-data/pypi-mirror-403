from flask import request
import six

from openapi_server.models.product import Product  # noqa: E501
from openapi_server.models.product_creation_or_update_parameters import ProductCreationOrUpdateParameters  # noqa: E501
from openapi_server.models.rest_error import RestError  # noqa: E501
from openapi_server.models.update_vidal_package_parameters import UpdateVidalPackageParameters  # noqa: E501
from openapi_server import util
from openapi_server.context import create_context
from impl import manage_product_controller




def create_product(context_, body):  # noqa: E501
    """Create product from product form

    Required parameters for creation of vidal synchronized product :  - vidalPackageId  Required parameters for creation of product from scratch :  - name  - barcodes  - dci  - laboratoryId  - unitWeight  - vatId  - unitPrice  - typeId  # noqa: E501

    :param body: Product to add
    :type body: dict | bytes

    :rtype: Product
    """
    context = create_context(context_)

    product_creation_or_update_parameters = body
    if request.is_json:
        product_creation_or_update_parameters = ProductCreationOrUpdateParameters.from_dict(request.get_json())  # noqa: E501

    return manage_product_controller.create_product(context, product_creation_or_update_parameters)





def set_product_vidal_package(context_, product_id, body=None):  # noqa: E501
    """Synchronize product against vidal id

     # noqa: E501

    :param product_id: The id of the product concerned by the request
    :type product_id: int
    :param body: 
    :type body: dict | bytes

    :rtype: None
    """
    context = create_context(context_)

    update_vidal_package_parameters = body
    if request.is_json:
        update_vidal_package_parameters = UpdateVidalPackageParameters.from_dict(request.get_json())  # noqa: E501

    return manage_product_controller.set_product_vidal_package(context, product_id, update_vidal_package_parameters)





def update_product(context_, product_id, body):  # noqa: E501
    """Update product from product form

    Administrator can update every fields (override allowed) Other users can only update the following fields if empty :   - unitWeight   - vat   - unitPrice   - type  # noqa: E501

    :param product_id: The id of the product concerned by the request
    :type product_id: int
    :param body: Modifications to apply
    :type body: dict | bytes

    :rtype: Product
    """
    context = create_context(context_)

    product_creation_or_update_parameters = body
    if request.is_json:
        product_creation_or_update_parameters = ProductCreationOrUpdateParameters.from_dict(request.get_json())  # noqa: E501

    return manage_product_controller.update_product(context, product_id, product_creation_or_update_parameters)


