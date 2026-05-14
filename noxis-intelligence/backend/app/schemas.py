"""
NOXIS Intelligence - Schemas Module (Compatibility Layer)
Este módulo fornece imports de compatibilidade para o código legado.
"""
from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional
from datetime import datetime

# Importa modelos do banco para compatibilidade
from app.models.schemas import AuditLog, Entity, Finding, InvestigationCase

__all__ = ["AuditLog", "Entity", "Finding", "InvestigationCase"]


class SearchRequest(BaseModel):
    """Schema para requisição de busca"""
    query: str = Field(..., description="CPF, Nome ou outro identificador")
    query_type: Optional[str] = Field(None, description="Tipo de query: CPF, NOME, CNPJ, AUTO")
    sources: Optional[List[str]] = Field(
        default=None,
        description="Fontes para buscar: google_dorks, portal_transparencia, bnmp, social_media"
    )
    include_details: bool = Field(True, description="Incluir detalhes completos nos resultados")


class SearchResponse(BaseModel):
    """Schema para resposta de busca"""
    query: str
    query_type: str
    status: str
    sources_consulted: List[str]
    results: Dict[str, Any]
    summary: Dict[str, Any]
    audit_log_id: Optional[int] = None
