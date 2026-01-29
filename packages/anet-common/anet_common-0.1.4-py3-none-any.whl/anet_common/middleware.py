import uuid
import threading
from django.utils.deprecation import MiddlewareMixin

_thread_locals = threading.local()

def get_current_request_id():
    return getattr(_thread_locals, "request_id", None)

class RequestIdMiddleware(MiddlewareMixin):
    """
    Har bir requestga noyob X-Request-ID biriktiradi.
    Bu ID loglarda va error responselarda ishlatiladi.
    """
    def process_request(self, request):
        request_id = request.headers.get("X-Request-ID")
        if not request_id:
            request_id = str(uuid.uuid4())
        
        request.id = request_id
        _thread_locals.request_id = request_id

    def process_response(self, request, response):
        if hasattr(request, "id"):
            response["X-Request-ID"] = request.id
        return response
