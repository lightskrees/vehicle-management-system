class BearerTokenMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        auth_header = request.headers.get("Authorization")
        if auth_header and not auth_header.startswith("Bearer "):
            request.META["HTTP_AUTHORIZATION"] = f"Bearer {auth_header}"

        response = self.get_response(request)
        return response
