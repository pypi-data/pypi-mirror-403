from flask import request
import six

from openapi_server.models.error import Error  # noqa: E501
from openapi_server.models.pet import Pet  # noqa: E501
from openapi_server import util
from openapi_server.context import create_context
from impl import pets_controller




def create_pets(context_):  # noqa: E501
    """Create a pet

     # noqa: E501


    :rtype: None
    """
    context = create_context(context_)


    return pets_controller.create_pets(context)





def list_pets(context_, limit=None):  # noqa: E501
    """List all pets

     # noqa: E501

    :param limit: How many items to return at one time (max 100)
    :type limit: int

    :rtype: List[Pet]
    """
    context = create_context(context_)


    return pets_controller.list_pets(context, limit)





def show_pet_by_id(context_, pet_id):  # noqa: E501
    """Info for a specific pet

     # noqa: E501

    :param pet_id: The id of the pet to retrieve
    :type pet_id: str

    :rtype: Pet
    """
    context = create_context(context_)


    return pets_controller.show_pet_by_id(context, pet_id)


