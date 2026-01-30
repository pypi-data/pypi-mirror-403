"""Middleware handling the HEAD requests"""

class HeadRequestMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        """If request is head, make a get request, return empty get request"""
        if request.method != 'HEAD':
            return self.get_response(request)

        # Perform your specific HEAD functionality here
        # For example, you could handle it as a GET
        request.method = 'GET'
        request.META['REQUEST_METHOD'] = 'GET'
        response = self.get_response(request)
        response['Content-Length'] = len(response.content)
        response.content = ''
        return response
