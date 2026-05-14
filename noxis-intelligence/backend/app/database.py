"""
NOXIS Intelligence - Database Module (Compatibility Layer)
Este módulo fornece imports de compatibilidade para o código legado.
"""
from app.core.database import engine, Base, SessionLocal, get_db

__all__ = ["engine", "Base", "SessionLocal", "get_db"]
