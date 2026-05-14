"""
NOXIS Intelligence - Search Router
Endpoint principal de busca que integra múltiplas fontes de OSINT.
"""
import asyncio
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Header, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.core.logging_config import logger
from app.scrapers import (
    GoogleDorksScraper,
    PortalTransparenciaScraper,
    BNMPScraper,
    SocialMediaScraper,
)
from app.models.schemas import AuditLog, Entity, Finding


router = APIRouter(prefix="/api/v1", tags=["Search"])


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


@router.post("/search", response_model=SearchResponse)
async def search_endpoint(
    request_body: SearchRequest,
    db: Session = Depends(get_db),
    x_operator_id: str = Header("anonymous", alias="X-Operator-ID"),
    x_operator_name: str = Header("Anonymous", alias="X-Operator-Name"),
    http_request: Request = None,
):
    """
    **Endpoint Principal de Busca OSINT**
    
    Realiza busca paralela em múltiplas fontes:
    - Google Dorks (buscas automatizadas)
    - Portal da Transparência (dados governamentais)
    - BNMP/CNJ (mandados de prisão)
    - Redes Sociais (menções em Surface Web)
    
    Requer header X-Operator-ID para auditoria.
    """
    
    logger.info(f"Iniciando busca para '{request_body.query}' solicitada por {x_operator_id}")
    
    # Determina tipo de query se não especificado
    query_type = request_body.query_type or _auto_detect_query_type(request_body.query)
    
    # Define fontes a serem consultadas
    sources = request_body.sources or [
        "google_dorks",
        "portal_transparencia", 
        "bnmp",
        "social_media"
    ]
    
    # Inicializa scrapers
    scrapers = {
        "google_dorks": GoogleDorksScraper(),
        "portal_transparencia": PortalTransparenciaScraper(),
        "bnmp": BNMPScraper(),
        "social_media": SocialMediaScraper(),
    }
    
    # Filtra scrapers baseado nas fontes solicitadas
    active_scrapers = {k: v for k, v in scrapers.items() if k in sources}
    
    results = {}
    sources_consulted = []
    errors = []
    
    # Executa todas as buscas em paralelo
    try:
        tasks = []
        
        for source_name, scraper in active_scrapers.items():
            task = _execute_scraper(scraper, request_body.query, query_type, request_body.include_details)
            tasks.append((source_name, task))
        
        # Aguarda todas as tarefas completarem
        for source_name, task in tasks:
            try:
                result = await task
                results[source_name] = result
                sources_consulted.append(source_name)
                logger.info(f"Fonte {source_name} completada com sucesso")
            except Exception as e:
                error_msg = f"Erro na fonte {source_name}: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)
                results[source_name] = {"error": str(e), "status": "failed"}
        
    except Exception as e:
        logger.error(f"Erro geral na busca: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro na execução das buscas: {str(e)}")
    
    # Gera resumo dos resultados
    summary = _generate_summary(results, query_type)
    
    # Determina status geral
    if len(errors) == len(active_scrapers):
        status = "error"
    elif len(errors) > 0:
        status = "partial"
    else:
        status = "success"
    
    # Cria entidade se encontrar resultados relevantes
    entity_id = None
    if summary.get("has_critical_findings", False) or summary.get("total_findings", 0) > 0:
        entity_id = _create_or_update_entity(
            db=db,
            query=request_body.query,
            query_type=query_type,
            results=results,
            summary=summary,
        )
    
    # Atualiza log de auditoria com resultados
    audit_log_id = _update_audit_log(
        db=db,
        operator_id=x_operator_id,
        operator_name=x_operator_name,
        query=request_body.query,
        query_type=query_type,
        sources_consulted=sources_consulted,
        results_summary=summary,
        status=status,
    )
    
    return SearchResponse(
        query=request_body.query,
        query_type=query_type,
        status=status,
        sources_consulted=sources_consulted,
        results=results,
        summary=summary,
        audit_log_id=audit_log_id,
    )


async def _execute_scraper(
    scraper, 
    query: str, 
    query_type: str, 
    include_details: bool
) -> Dict[str, Any]:
    """Executa um scraper específico com timeout"""
    
    # Prepara kwargs específicos baseado no scraper
    kwargs = {"include_details": include_details}
    
    if query_type == "CPF":
        kwargs["search_type"] = "cpf"
    elif query_type == "NOME":
        kwargs["search_type"] = "nome"
    
    # Executa com timeout de 60 segundos
    result = await asyncio.wait_for(
        scraper.scrape(query, **kwargs),
        timeout=60.0
    )
    
    return result


def _auto_detect_query_type(query: str) -> str:
    """Detecta automaticamente o tipo de query"""
    
    clean_query = "".join(filter(str.isdigit, query))
    
    if len(clean_query) == 11:
        return "CPF"
    elif len(clean_query) == 14:
        return "CNPJ"
    elif "@" in query:
        return "EMAIL"
    else:
        return "NOME"


def _generate_summary(results: Dict[str, Any], query_type: str) -> Dict[str, Any]:
    """Gera resumo consolidado dos resultados"""
    
    summary = {
        "total_findings": 0,
        "has_critical_findings": False,
        "risk_indicators": [],
        "sources_with_results": [],
    }
    
    # Analisa resultados do BNMP
    bnmp_data = results.get("bnmp", {}).get("data", {})
    if bnmp_data:
        has_warrants = bnmp_data.get("has_warrants", False)
        active_warrants = bnmp_data.get("active_warrants_count", 0)
        
        if has_warrants:
            summary["has_critical_findings"] = True
            summary["risk_indicators"].append(f"{active_warrants} mandado(s) ativo(s)")
            summary["total_findings"] += active_warrants
        
        if bnmp_data.get("status") == "mandados_encontrados":
            summary["sources_with_results"].append("bnmp")
    
    # Analisa resultados do Portal da Transparência
    pt_data = results.get("portal_transparencia", {}).get("data", {})
    if pt_data:
        total_registros = pt_data.get("total_registros", 0)
        if total_registros > 0:
            summary["total_findings"] += total_registros
            summary["sources_with_results"].append("portal_transparencia")
            
            # Verifica se há muitas despesas (possível indicador de risco)
            despesas = pt_data.get("despesas", [])
            if len(despesas) > 100:
                summary["risk_indicators"].append("Volume elevado de despesas")
    
    # Analisa Google Dorks
    gd_data = results.get("google_dorks", {}).get("data", {})
    if gd_data:
        total_results = gd_data.get("total_results", 0)
        if total_results > 0:
            summary["total_findings"] += total_results
            summary["sources_with_results"].append("google_dorks")
            
            # Muitos resultados podem indicar notoriedade
            if total_results > 50:
                summary["risk_indicators"].append("Alta presença digital")
    
    # Analisa Social Media
    sm_data = results.get("social_media", {}).get("data", {})
    if sm_data:
        total_mentions = sm_data.get("total_mentions", 0)
        if total_mentions > 0:
            summary["total_findings"] += total_mentions
            summary["sources_with_results"].append("social_media")
    
    # Calcula score de risco simples
    risk_score = 0
    if summary["has_critical_findings"]:
        risk_score += 50
    risk_score += min(len(summary["risk_indicators"]) * 10, 30)
    risk_score += min(summary["total_findings"], 20)
    
    summary["risk_score"] = min(risk_score, 100)
    
    return summary


def _create_or_update_entity(
    db: Session,
    query: str,
    query_type: str,
    results: Dict[str, Any],
    summary: Dict[str, Any],
) -> int:
    """Cria ou atualiza entidade no banco de dados"""
    
    # Tenta encontrar entidade existente
    existing_entity = None
    if query_type == "CPF":
        existing_entity = db.query(Entity).filter(
            Entity.document == "".join(filter(str.isdigit, query))
        ).first()
    
    if not existing_entity:
        # Cria nova entidade
        entity = Entity(
            entity_type="PERSON" if query_type in ["CPF", "NOME", "RG"] else "COMPANY",
            name=query,
            document="".join(filter(str.isdigit, query)) if query_type in ["CPF", "CNPJ"] else None,
            document_type=query_type,
            risk_level=_calculate_risk_level(summary.get("risk_score", 0)),
            risk_score=summary.get("risk_score", 0),
            additional_data=summary,
        )
        db.add(entity)
        db.commit()
        db.refresh(entity)
        logger.info(f"Entidade criada: ID={entity.id}, name={query}")
        return entity.id
    else:
        # Atualiza entidade existente
        existing_entity.risk_score = summary.get("risk_score", 0)
        existing_entity.risk_level = _calculate_risk_level(summary.get("risk_score", 0))
        existing_entity.updated_at = None  # Trigger update timestamp
        db.commit()
        logger.info(f"Entidade atualizada: ID={existing_entity.id}, name={query}")
        return existing_entity.id


def _calculate_risk_level(risk_score: float) -> str:
    """Calcula nível de risco baseado no score"""
    
    if risk_score >= 80:
        return "CRITICAL"
    elif risk_score >= 60:
        return "HIGH"
    elif risk_score >= 40:
        return "MEDIUM"
    elif risk_score >= 20:
        return "LOW"
    else:
        return "UNKNOWN"


def _update_audit_log(
    db: Session,
    operator_id: str,
    operator_name: str,
    query: str,
    query_type: str,
    sources_consulted: List[str],
    results_summary: Dict[str, Any],
    status: str,
) -> Optional[int]:
    """Atualiza ou cria log de auditoria com resultados"""
    
    try:
        # Busca o log mais recente deste operador para esta query
        audit_log = db.query(AuditLog).filter(
            AuditLog.operator_id == operator_id,
            AuditLog.query_identifier == query,
        ).order_by(AuditLog.timestamp.desc()).first()
        
        if not audit_log:
            # Cria novo log se não existir
            audit_log = AuditLog(
                operator_id=operator_id,
                operator_name=operator_name,
                action_type="SEARCH",
                query_identifier=query,
                query_type=query_type,
                status=status,
            )
            db.add(audit_log)
        
        # Atualiza com resultados
        audit_log.sources_consulted = sources_consulted
        audit_log.results_summary = results_summary
        audit_log.status = status
        
        db.commit()
        db.refresh(audit_log)
        
        return audit_log.id
        
    except Exception as e:
        logger.error(f"Erro ao atualizar log de auditoria: {str(e)}")
        db.rollback()
        return None
