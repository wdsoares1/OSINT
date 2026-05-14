"""
NOXIS Intelligence - OSINT Service
Serviço principal de processamento e análise de dados OSINT.
"""
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.core.logging_config import logger
from app.scrapers import (
    GoogleDorksScraper,
    PortalTransparenciaScraper,
    BNMPScraper,
    SocialMediaScraper,
)


class OSINTService:
    """
    Serviço de inteligência OSINT que coordena múltiplas fontes de dados.
    
    Responsabilidades:
    - Orquestrar scrapers em paralelo
    - Consolidar resultados de múltiplas fontes
    - Calcular scores de risco consolidados
    - Identificar correlações entre descobertas
    """

    def __init__(self, db_session: Optional[Session] = None):
        self.db_session = db_session
        self.logger = logger
        
        # Inicializa scrapers
        self.scrapers = {
            "google_dorks": GoogleDorksScraper(),
            "portal_transparencia": PortalTransparenciaScraper(),
            "bnmp": BNMPScraper(),
            "social_media": SocialMediaScraper(),
        }

    async def execute_comprehensive_search(
        self,
        query: str,
        query_type: Optional[str] = None,
        sources: Optional[List[str]] = None,
        include_details: bool = True,
        timeout_per_source: float = 60.0,
    ) -> Dict[str, Any]:
        """
        Executa busca completa em múltiplas fontes OSINT.
        
        Args:
            query: CPF, Nome ou outro identificador
            query_type: Tipo de query (CPF, NOME, CNPJ, AUTO)
            sources: Lista de fontes para consultar (None = todas)
            include_details: Se True, inclui detalhes completos
            timeout_per_source: Timeout individual por fonte em segundos
            
        Returns:
            Dicionário com resultados consolidados
        """
        
        # Auto-detecta tipo de query se necessário
        if not query_type or query_type == "AUTO":
            query_type = self._auto_detect_query_type(query)
        
        # Define fontes ativas
        active_sources = sources or list(self.scrapers.keys())
        active_scrapers = {
            k: v for k, v in self.scrapers.items() 
            if k in active_sources
        }
        
        self.logger.info(
            f"Iniciando busca OSINT completa para '{query}' "
            f"(tipo: {query_type}, fontes: {active_sources})"
        )
        
        results = {}
        errors = {}
        
        # Executa todas as fontes em paralelo
        tasks = []
        for source_name, scraper in active_scrapers.items():
            task = self._execute_single_scraper(
                scraper=scraper,
                source_name=source_name,
                query=query,
                query_type=query_type,
                include_details=include_details,
                timeout=timeout_per_source,
            )
            tasks.append(task)
        
        # Aguarda todas as tarefas
        task_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Processa resultados
        for i, result in enumerate(task_results):
            source_name = list(active_scrapers.keys())[i]
            
            if isinstance(result, Exception):
                errors[source_name] = str(result)
                results[source_name] = {
                    "status": "error",
                    "error": str(result),
                    "data": None,
                }
                self.logger.error(f"Erro na fonte {source_name}: {str(result)}")
            else:
                results[source_name] = result
                self.logger.info(f"Fonte {source_name} completada com sucesso")
        
        # Consolida resultados
        consolidated = self._consolidate_results(
            query=query,
            query_type=query_type,
            results=results,
            errors=errors,
        )
        
        return consolidated

    async def _execute_single_scraper(
        self,
        scraper: Any,
        source_name: str,
        query: str,
        query_type: str,
        include_details: bool,
        timeout: float,
    ) -> Dict[str, Any]:
        """Executa um único scraper com timeout"""
        
        kwargs = {"include_details": include_details}
        
        if query_type == "CPF":
            kwargs["search_type"] = "cpf"
        elif query_type == "NOME":
            kwargs["search_type"] = "nome"
        
        try:
            result = await asyncio.wait_for(
                scraper.scrape(query, **kwargs),
                timeout=timeout,
            )
            return result.get("data", result)
        except asyncio.TimeoutError:
            raise TimeoutError(f"Timeout após {timeout}s na fonte {source_name}")

    def _auto_detect_query_type(self, query: str) -> str:
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

    def _consolidate_results(
        self,
        query: str,
        query_type: str,
        results: Dict[str, Any],
        errors: Dict[str, str],
    ) -> Dict[str, Any]:
        """Consolida resultados de múltiplas fontes"""
        
        consolidated = {
            "query": query,
            "query_type": query_type,
            "timestamp": datetime.utcnow().isoformat(),
            "sources_consulted": list(results.keys()),
            "sources_with_errors": list(errors.keys()),
            "findings": [],
            "risk_indicators": [],
            "summary": {},
        }
        
        total_findings = 0
        has_critical = False
        
        # Analisa BNMP
        bnmp_data = results.get("bnmp", {}).get("bnmp_data", {})
        if bnmp_data:
            mandados = bnmp_data.get("mandados", [])
            if mandados:
                has_critical = True
                consolidated["risk_indicators"].append(
                    f"{len(mandados)} mandado(s) encontrado(s)"
                )
                for mandado in mandados:
                    consolidated["findings"].append({
                        "type": "MANDADO",
                        "source": "BNMP",
                        "data": mandado,
                        "relevance": "CRITICAL",
                    })
                    total_findings += 1
        
        # Analisa Portal da Transparência
        pt_data = results.get("portal_transparencia", {}).get("portal_transparencia", {})
        if pt_data:
            despesas = pt_data.get("despesas", [])
            servidores = pt_data.get("servidores", [])
            
            if despesas:
                consolidated["findings"].append({
                    "type": "DESPESAS",
                    "source": "PORTAL_TRANSPARENCIA",
                    "count": len(despesas),
                    "data": despesas[:10],  # Primeiros 10 registros
                    "relevance": "MEDIUM",
                })
                total_findings += len(despesas)
                
                if len(despesas) > 50:
                    consolidated["risk_indicators"].append(
                        "Volume elevado de despesas registradas"
                    )
            
            if servidores:
                consolidated["findings"].append({
                    "type": "SERVIDOR",
                    "source": "PORTAL_TRANSPARENCIA",
                    "count": len(servidores),
                    "data": servidores[:5],
                    "relevance": "HIGH",
                })
                total_findings += len(servidores)
                consolidated["risk_indicators"].append(
                    "Vínculo com órgão público identificado"
                )
        
        # Analisa Google Dorks
        gd_data = results.get("google_dorks", {}).get("results", [])
        if gd_data:
            consolidated["findings"].append({
                "type": "PRESENCA_DIGITAL",
                "source": "GOOGLE_DORKS",
                "count": len(gd_data),
                "data": gd_data[:20],
                "relevance": "LOW",
            })
            total_findings += len(gd_data)
            
            if len(gd_data) > 50:
                consolidated["risk_indicators"].append(
                    "Alta presença digital encontrada"
                )
        
        # Analisa Social Media
        sm_data = results.get("social_media", {}).get("mentions_by_platform", {})
        if sm_data:
            total_mentions = sum(len(v) for v in sm_data.values())
            if total_mentions > 0:
                consolidated["findings"].append({
                    "type": "REDES_SOCIAIS",
                    "source": "SOCIAL_MEDIA",
                    "count": total_mentions,
                    "data": sm_data,
                    "relevance": "LOW",
                })
                total_findings += total_mentions
        
        # Calcula score de risco consolidado
        risk_score = self._calculate_risk_score(
            has_critical=has_critical,
            risk_indicators=consolidated["risk_indicators"],
            total_findings=total_findings,
        )
        
        consolidated["summary"] = {
            "total_findings": total_findings,
            "has_critical_findings": has_critical,
            "risk_score": risk_score,
            "risk_level": self._get_risk_level(risk_score),
            "sources_with_results": [
                k for k, v in results.items() 
                if v.get("status") != "error" and v.get("data")
            ],
        }
        
        return consolidated

    def _calculate_risk_score(
        self,
        has_critical: bool,
        risk_indicators: List[str],
        total_findings: int,
    ) -> float:
        """Calcula score de risco baseado nos achados"""
        
        score = 0.0
        
        # Mandados de prisão (crítico)
        if has_critical:
            score += 50.0
        
        # Indicadores de risco
        score += min(len(risk_indicators) * 8.0, 24.0)
        
        # Volume de achados
        score += min(total_findings * 0.5, 20.0)
        
        return min(score, 100.0)

    def _get_risk_level(self, risk_score: float) -> str:
        """Obtém nível de risco baseado no score"""
        
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

    async def search_specific_source(
        self,
        source: str,
        query: str,
        query_type: str = "AUTO",
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Busca em uma fonte específica.
        
        Args:
            source: Nome da fonte (google_dorks, portal_transparencia, bnmp, social_media)
            query: Identificador para busca
            query_type: Tipo de query
            **kwargs: Parâmetros específicos do scraper
            
        Returns:
            Resultados da fonte específica
        """
        
        if source not in self.scrapers:
            raise ValueError(f"Fonte desconhecida: {source}")
        
        scraper = self.scrapers[source]
        
        if not query_type or query_type == "AUTO":
            query_type = self._auto_detect_query_type(query)
        
        kwargs["search_type"] = query_type.lower()
        
        result = await scraper.scrape(query, **kwargs)
        
        return result
