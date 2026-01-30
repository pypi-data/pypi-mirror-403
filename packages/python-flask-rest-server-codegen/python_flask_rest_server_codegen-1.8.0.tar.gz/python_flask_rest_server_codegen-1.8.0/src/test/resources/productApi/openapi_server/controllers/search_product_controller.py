from flask import request
import six

from openapi_server.models.paginated_products import PaginatedProducts  # noqa: E501
from openapi_server.models.product import Product  # noqa: E501
from openapi_server.models.product_status import ProductStatus  # noqa: E501
from openapi_server.models.rest_error import RestError  # noqa: E501
from openapi_server import util
from openapi_server.context import create_context
from impl import search_product_controller




def get_product(context_, product_id):  # noqa: E501
    """Retrieve a product with ID

     # noqa: E501

    :param product_id: The id of the product concerned by the request
    :type product_id: int

    :rtype: Product
    """
    context = create_context(context_)


    return search_product_controller.get_product(context, product_id)





def get_products(context_, q=None, vidal_package_eq=None, st_eq=None, pt_eq=None, spt_eq=None, lab_eq=None, s_waiting_sale_offer_count_gte=None, order_by=None, p=None, pp=None):  # noqa: E501
    """Search for products with his name or status

     # noqa: E501

    :param q: Any field in the product contains &#39;q&#39;
    :type q: str
    :param vidal_package_eq: Vidal package equal this one
    :type vidal_package_eq: int
    :param st_eq: Filter on status to include in the search (can be given multiple time which result in a OR condition)
    :type st_eq: list | bytes
    :param pt_eq: Product type to search on
    :type pt_eq: str
    :param spt_eq: Secondary product type to search on
    :type spt_eq: str
    :param lab_eq: Laboratory to search on (can be given multiple time which result in a OR condition)
    :type lab_eq: List[int]
    :param s_waiting_sale_offer_count_gte: Waiting sale offers count greater than or equal
    :type s_waiting_sale_offer_count_gte: int
    :param order_by: Sort by
    :type order_by: str
    :param p: Page number to search for (start at 0)
    :type p: int
    :param pp: Number of user per page
    :type pp: int

    :rtype: PaginatedProducts
    """
    context = create_context(context_)

    if request.is_json:
        st_eq = [ProductStatus.from_dict(d) for d in request.get_json()]  # noqa: E501


    return search_product_controller.get_products(context, q, vidal_package_eq, st_eq, pt_eq, spt_eq, lab_eq, s_waiting_sale_offer_count_gte, order_by, p, pp)





def test_free_access(context_):  # noqa: E501
    """Test generation without bearer

     # noqa: E501


    :rtype: None
    """
    context = create_context(context_)


    return search_product_controller.test_free_access(context)


