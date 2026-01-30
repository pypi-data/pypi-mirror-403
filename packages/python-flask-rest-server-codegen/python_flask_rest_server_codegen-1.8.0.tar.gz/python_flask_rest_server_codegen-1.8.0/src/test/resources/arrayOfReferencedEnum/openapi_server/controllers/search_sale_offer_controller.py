from flask import request
import six

from openapi_server.models.sale_offer_status import SaleOfferStatus  # noqa: E501
from openapi_server import util
from openapi_server.context import create_context
from impl import search_sale_offer_controller




def get_sale_offers(context_, st_eq=None):  # noqa: E501
    """Search sale offers

     # noqa: E501

    :param st_eq: Filter on status to include in the search (can be given multiple time which result in a OR condition)
    :type st_eq: list | bytes

    :rtype: str
    """
    context = create_context(context_)

    if request.is_json:
        st_eq = [SaleOfferStatus.from_dict(d) for d in request.get_json()]  # noqa: E501


    return search_sale_offer_controller.get_sale_offers(context, st_eq)





def get_sale_offers_by_status(context_, sale_offer_status):  # noqa: E501
    """Search sale offers by status

     # noqa: E501

    :param sale_offer_status: 
    :type sale_offer_status: dict | bytes

    :rtype: None
    """
    context = create_context(context_)

    if request.is_json:
        sale_offer_status =  SaleOfferStatus.from_dict(request.get_json())  # noqa: E501

    return search_sale_offer_controller.get_sale_offers_by_status(context, sale_offer_status)


