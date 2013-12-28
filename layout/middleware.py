from api import get_layout


class LayoutMiddleware(object):
    def process_request(self, request):
        get_layout(request)
