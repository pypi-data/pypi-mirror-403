"""
eco-back - Librería Python
"""

__version__ = "0.2.1"

# Módulos principales
from . import database
from . import api
from . import documento
from . import registro

__all__ = ["database", "api", "documento", "registro", "__version__"]
