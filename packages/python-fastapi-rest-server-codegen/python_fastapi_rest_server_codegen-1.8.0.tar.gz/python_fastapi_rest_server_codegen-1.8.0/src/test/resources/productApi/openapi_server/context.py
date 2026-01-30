
def create_empty_context(db_manager):
    # Return context without any security context
    return Context(None, db_manager=db_manager)

def create_service_context(user, db_manager):
    security_context = SecurityContext(
        user.id,
        user.role,
        [] # TODO : User DTO do not provide capabilities yet
    )

    # Return context according token
    return Context(security_context, db_manager=db_manager)

def create_context(request, token_bearerAuth=None, **kwargs):
    security_context = None
    if token_bearerAuth:
        str_id = token_bearerAuth.get('id', None)
        security_context = SecurityContext(
            int(str_id) if str_id else str_id,
            token_bearerAuth.get('role', None),
            token_bearerAuth.get('capabilities', None)
        )

    # Return context according token
    return Context(security_context, request=request)

class Context:
    def __init__(self, security_context, request=None, db_manager=None):
        self.security_context = security_context
        self.request = request
        self.db_manager = db_manager if db_manager else request.state.db_manager

    def get_http_request(self):
        return self.request

    def get_security_context(self):
        return self.security_context

    def get_db_session(self):
        return self.db_manager.get_session()

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