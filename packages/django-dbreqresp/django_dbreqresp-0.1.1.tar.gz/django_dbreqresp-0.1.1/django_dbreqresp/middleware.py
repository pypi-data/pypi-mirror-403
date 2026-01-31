import logging
import time
from django.utils.timezone import now
from .models import RequestLog
from django.conf import settings

class DbreqrespMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.paths = getattr(settings, "DBREQRESP_MIDDLEWARE_PATHS", [])

    def __call__(self, request):
        start = now()
        response = self.get_response(request)
        if any([request.path.startswith(path) for path in self.paths]):
            RequestLog.store(request, response, start)
        return response
