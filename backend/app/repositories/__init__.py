"""Módulo de repositorios para acceso a datos."""

from .base import BaseRepository
from .empresa_repository import EmpresaRepository
from .establecimiento_repository import EstablecimientoRepository
from .chacra_repository import ChacraRepository
from .destino_repository import DestinoRepository

__all__ = [
    "BaseRepository",
    "EmpresaRepository", 
    "EstablecimientoRepository",
    "ChacraRepository",
    "DestinoRepository",
]
