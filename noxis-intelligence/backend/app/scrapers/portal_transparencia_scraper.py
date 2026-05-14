"""
NOXIS Intelligence - Portal da Transparência Scraper
Consulta dados abertos do Portal da Transparência do Governo Federal.
"""
import asyncio
import urllib.parse
from typing import Dict, List, Any, Optional
import aiohttp
from app.scrapers.base_scraper import BaseScraper


class PortalTransparenciaScraper(BaseScraper):
    """
    Scraper para o Portal da Transparência.
    
    Endpoints disponíveis:
    - /portais/transparencia/v1/diario/despesas/{cpf}
    - /portais/transparencia/v1/pessoal/matriculas/{nome}
    - /orgaos/executivo/poder/{poder}/tipos-orgao/{tipo}
    """
    
    def __init__(self):
        super().__init__(name="PortalTransparenciaScraper")
        self.base_url = "https://api.portaldatransparencia.gov.br/api-de-dados"
        
    async def _fetch_endpoint(
        self, 
        endpoint: str, 
        params: Optional[Dict] = None
    ) -> Optional[Any]:
        """Busca dados de um endpoint específico da API"""
        
        url = f"{self.base_url}/{endpoint}"
        
        headers = {
            "Accept": "application/json",
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                response = await self._fetch_with_retry(
                    session=session,
                    url=url,
                    method="GET",
                    headers=headers
                )
                
                if response:
                    return await response.json()
                    
        except Exception as e:
            self.logger.error(f"Erro ao buscar endpoint {endpoint}: {str(e)}")
        
        return None
    
    async def search_by_cpf(self, cpf: str) -> Dict[str, Any]:
        """Busca despesas diárias associadas a um CPF"""
        
        # Remove caracteres não numéricos
        cpf_clean = "".join(filter(str.isdigit, cpf))
        
        if len(cpf_clean) != 11:
            return {"error": "CPF inválido", "cpf": cpf}
        
        endpoint = f"portais/transparencia/v1/diario/despesas/cpf/{cpf_clean}"
        
        results = await self._fetch_endpoint(endpoint)
        
        return {
            "search_type": "cpf",
            "identifier": cpf,
            "data": results if results else [],
        }
    
    async def search_by_name(self, name: str) -> Dict[str, Any]:
        """Busca servidores pelo nome"""
        
        # Codifica o nome para URL
        name_encoded = urllib.parse.quote(name.strip())
        
        endpoint = f"portais/transparencia/v1/pessoal/matriculas/nome/{name_encoded}"
        
        results = await self._fetch_endpoint(endpoint)
        
        return {
            "search_type": "nome",
            "identifier": name,
            "data": results if results else [],
        }
    
    async def search_by_entity(self, entity_name: str) -> Dict[str, Any]:
        """Busca órgãos/entidades pelo nome"""
        
        entity_encoded = urllib.parse.quote(entity_name.strip())
        
        endpoint = f"portais/transparencia/v1/orgaos/{entity_encoded}"
        
        results = await self._fetch_endpoint(endpoint)
        
        return {
            "search_type": "orgao",
            "identifier": entity_name,
            "data": results if results else [],
        }
    
    async def scrape(self, query: str, **kwargs) -> Dict[str, Any]:
        """
        Realiza busca no Portal da Transparência.
        
        Args:
            query: CPF ou nome para busca
            **kwargs: Parâmetros adicionais
                - search_type: 'cpf', 'nome' ou 'auto' (default: 'auto')
                - include_despesas: Se True, inclui despesas (default: True)
                - include_servidores: Se True, inclui servidores (default: True)
                
        Returns:
            Dicionário com dados do Portal da Transparência
        """
        
        search_type = kwargs.get("search_type", "auto")
        include_despesas = kwargs.get("include_despesas", True)
        include_servidores = kwargs.get("include_servidores", True)
        
        self.logger.info(f"Iniciando busca no Portal da Transparência para '{query}'")
        
        results = {
            "query": query,
            "search_type": search_type,
            "despesas": [],
            "servidores": [],
            "orgaos": [],
        }
        
        # Detecta automaticamente o tipo de busca se necessário
        if search_type == "auto":
            if query.isdigit() and len(query) == 11:
                search_type = "cpf"
            else:
                search_type = "nome"
        
        # Busca por CPF
        if search_type == "cpf" and include_despesas:
            cpf_result = await self.search_by_cpf(query)
            results["despesas"] = cpf_result.get("data", [])
            results["search_type"] = "cpf"
        
        # Busca por nome
        elif search_type == "nome":
            if include_servidores:
                servidor_result = await self.search_by_name(query)
                results["servidores"] = servidor_result.get("data", [])
            
            if include_despesas:
                # Tenta buscar como órgão também
                orgao_result = await self.search_by_entity(query)
                results["orgaos"] = orgao_result.get("data", [])
            
            results["search_type"] = "nome"
        
        normalized_data = {
            "query": query,
            "portal_transparencia": results,
            "total_registros": (
                len(results["despesas"]) + 
                len(results["servidores"]) + 
                len(results["orgaos"])
            ),
        }
        
        return self.normalize_data(normalized_data)
