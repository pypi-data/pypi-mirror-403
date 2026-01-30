import openapi_server.token as token_manager
from connexion.resolver import RestyResolver, Resolver
import re


class ApiResolver(RestyResolver):
    """
    Customized resolver for python convention written endpoints
    """

    def __init__(self, default_module_name, collection_endpoint_name='search'):
        """
        :param default_module_name: Default module name for operations
        :type default_module_name: str
        """
        RestyResolver.__init__(self, default_module_name, collection_endpoint_name=collection_endpoint_name)

    def resolve_operation_id(self, operation):
        """
        Resolves the operationId using REST semantics unless explicitly configured in the spec

        :type operation: connexion.operations.AbstractOperation
        """
        operation_id = super().resolve_operation_id(operation)
        token_manager.flask_endpoint_to_restrict[operation_id] = operation._operation.get("x-restrict")
        return operation_id
