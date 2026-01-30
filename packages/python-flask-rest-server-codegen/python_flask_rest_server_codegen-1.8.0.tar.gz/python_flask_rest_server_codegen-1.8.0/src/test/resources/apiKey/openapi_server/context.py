from flask import request

def create_context(context_):
    # Get decoded token from request
    token_info = context_.get('token_info', None)

    security_context = None
    if token_info:
        str_id = token_info.get('id', None)
        security_context = SecurityContext(
            int(str_id) if str_id else str_id,
            token_info.get('role', None),
            token_info.get('capabilities', None)
        )

    # Return context according token
    return Context(security_context, request)

class Context:
    def __init__(self, security_context, request):
        self.security_context = security_context
        self.request = request

    def get_http_request(self):
        return self.request

    def get_security_context(self):
        return self.security_context

class SecurityContext:
    def __init__(self, id, role, capabilities):
        self.id = id
        self.role = role
        self.capabilities = capabilities

    def get_id(self):
        return self.id

    def get_role(self):
        return self.role

    def get_capabilities(self):
        return self.capabilities