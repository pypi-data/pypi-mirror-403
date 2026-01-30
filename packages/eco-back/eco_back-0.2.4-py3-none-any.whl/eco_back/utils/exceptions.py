# Raise custom exception for service validation errors
# - Envía un mensaje y un código HTTP asociado
import datetime
from functools import wraps
from django.http import JsonResponse

from eco_back.utils.logger_generico import _log_warn

class ServiceValidationError(Exception):
    def __init__(self, message: str, code: int = 400, errors=None, extra=None, context=None, user_id=None, request_path=None):
        super().__init__(message)
        self.message = message
        self.code = code
        self.errors = errors
        self.extra = extra
        self.context = context
        self.user_id = user_id
        self.request_path = request_path
        self.timestamp = datetime.datetime.now().isoformat()

def handle_service_validation_error(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        try:
            return view_func(request, *args, **kwargs)
        except ServiceValidationError as e:
            _log_warn(f"Error: {e.message}", level="warning", extra={"errors": e.errors, "extra": e.extra, "context": e.context}, exc_info=True)
            resp = {"status": "error", "message": e.message}
            if e.errors:
                resp["errors"] = e.errors
            if e.extra:
                resp["extra"] = e.extra
            if e.context:
                resp["context"] = e.context
            if e.user_id:
                resp["user_id"] = e.user_id
            if e.request_path:
                resp["request_path"] = e.request_path

            resp["timestamp"] = e.timestamp
            return JsonResponse(resp, status=e.code)
        except Exception as e:
            _log_warn(f"Error inesperado en decorator: {e}", level="error", exc_info=True, extra={"view": view_func.__name__})
            print(f"handle_service_validation_error atrapó excepción: {e}")
            return JsonResponse({"status": "error", "message": "Error interno"}, status=500)
    return _wrapped_view
