from django.utils.timezone import now

from .models import RequestLog


def dbreqresp(function):
    def wrapper(request, *args, **kwargs):
        start = now()
        response = function(request, *args, **kwargs)
        RequestLog.store(request, response, start)
        return response
    return wrapper
