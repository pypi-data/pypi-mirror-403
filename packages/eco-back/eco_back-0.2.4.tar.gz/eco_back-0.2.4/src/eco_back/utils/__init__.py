"""
Módulo de utilidades para eco-back
Incluye manejo de excepciones y logging
"""

from .exceptions import ServiceValidationError, handle_service_validation_error
from .logger_generico import _log_warn

__all__ = [
    "ServiceValidationError",
    "handle_service_validation_error",
    "_log_warn"
]
