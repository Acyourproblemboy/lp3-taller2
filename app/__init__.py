"""
Paquete principal de la aplicación API de Películas.
Este módulo inicializa el paquete y expone los componentes principales.
"""

# Importar los componentes principales para facilitar su uso
# Ejemplo:
from .database import get_session, engine
from .models import Usuario, Pelicula, Favorito
from .config import settings

__version__ = "1.0.0"
__author__ = "Andres Stivens Cortes Ponce"  # Reemplazar con tu nombre

# Opcional - Definir __all__ para controlar qué se exporta
__all__ = [
    "get_session",
    "engine",
    "Usuario",
    "Pelicula",
    "Favorito",
    "settings",
   
 ]

