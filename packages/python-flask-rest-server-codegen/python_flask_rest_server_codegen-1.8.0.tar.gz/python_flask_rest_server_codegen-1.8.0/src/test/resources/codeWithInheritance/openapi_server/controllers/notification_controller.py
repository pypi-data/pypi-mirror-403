from flask import request
import six

from openapi_server.models.notification_sending import NotificationSending  # noqa: E501
from openapi_server import util
from openapi_server.context import create_context
from impl import notification_controller




def get_notifications(context_, authorization=None, number=None, page=None):  # noqa: E501
    """Request all notifications

     # noqa: E501

    :param authorization: 
    :type authorization: str
    :param number: Number of notifications
    :type number: int
    :param page: Page number to search for
    :type page: int

    :rtype: List[NotificationSending]
    """
    context = create_context(context_)


    return notification_controller.get_notifications(context, authorization, number, page)


