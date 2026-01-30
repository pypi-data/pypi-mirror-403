"""
eco-back - Librería Python
"""

__version__ = "0.2.4"

# Módulos principales
from . import database
from . import api
from . import documento
from . import registro
from . import utils

__all__ = ["database", "api", "documento", "registro", "utils", "__version__"]
