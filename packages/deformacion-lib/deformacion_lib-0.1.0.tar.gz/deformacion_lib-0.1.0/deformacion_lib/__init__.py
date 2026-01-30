"""
deformacion_lib - Librería para análisis de deformación en materiales
"""

from .tensile import ejecutar_analisis_tensile
from .estructura3d import ejecutar_analisis_3d

__version__ = "0.1.0"
__all__ = ["ejecutar_analisis_tensile", "ejecutar_analisis_3d"]