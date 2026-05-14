"""
NOXIS Intelligence - Google Dorks Scraper
Realiza buscas automatizadas usando Google Dorks para OSINT.
"""
import urllib.parse
from typing import Dict, List, Any, Optional
from app.scrapers.base_scraper import BaseScraper, ScraperError


class GoogleDorksScraper(BaseScraper):
    """
    Scraper para buscas via Google Dorks.
    
    Dorks utilizadas:
    - intext:"{query}" - Busca no conteúdo da página
    - inurl:"{query}" - Busca na URL
    - filetype:pdf "{query}" - Documentos PDF
    - site:gov.br "{query}" - Sites governamentais
    - site:jus.br "{query}" - Sites do judiciário
    """
    
    def __init__(self):
        super().__init__(name="GoogleDorksScraper")
        self.search_url = "https://www.google.com/search"
        
    def _build_dork_queries(self, query: str) -> List[str]:
        """Constrói uma lista de Google Dorks baseados na query"""
        
        # Detecta se é CPF (apenas números, 11 dígitos)
        is_cpf = query.isdigit() and len(query) == 11
        
        dorks = []
        
        if is_cpf:
            # Dorks específicas para CPF
            dorks.extend([
                f'"{query}"',
                f'intext:"{query}"',
                f'site:gov.br "{query}"',
                f'site:jus.br "{query}"',
                f'site:cnj.jus.br "{query}"',
                f'filetype:pdf "{query}"',
                f'filetype:xls "{query}"',
                f'filetype:xlsx "{query}"',
            ])
        else:
            # Dorks para nome ou outros termos
            dorks.extend([
                f'"{query}"',
                f'intext:"{query}"',
                f'site:gov.br "{query}"',
                f'site:jus.br "{query}"',
                f'site:reclameaqui.com.br "{query}"',
                f'site:linkedin.com "{query}"',
                f'site:facebook.com "{query}"',
                f'site:instagram.com "{query}"',
                f'site:twitter.com "{query}"',
                f'filetype:pdf "{query}"',
            ])
        
        return dorks
    
    async def _search_dork(self, dork: str) -> List[Dict[str, str]]:
        """Executa uma busca com um dork específico"""
        
        params = {
            "q": dork,
            "num": 10,
            "hl": "pt-BR",
            "gl": "br",
        }
        
        url = f"{self.search_url}?{urllib.parse.urlencode(params)}"
        
        results = []
        
        try:
            html = await self.fetch_with_playwright(url, wait_selector="div#search")
            
            if not html:
                return results
            
            soup = self.parse_html(html)
            
            # Extrai resultados da SERP do Google
            search_results = soup.select("div.g")
            
            for result in search_results[:10]:  # Limita a 10 resultados por dork
                title_elem = result.select_one("h3")
                link_elem = result.select_one("a")
                snippet_elem = result.select_one("div.VwiC3b")
                
                if title_elem and link_elem:
                    results.append({
                        "title": title_elem.get_text(strip=True),
                        "url": link_elem.get("href", ""),
                        "snippet": snippet_elem.get_text(strip=True) if snippet_elem else "",
                        "dork": dork,
                    })
                    
        except Exception as e:
            self.logger.error(f"Erro ao buscar dork '{dork}': {str(e)}")
        
        return results
    
    async def scrape(self, query: str, **kwargs) -> Dict[str, Any]:
        """
        Realiza buscas com múltiplos Google Dorks em paralelo.
        
        Args:
            query: CPF, nome ou outro identificador
            **kwargs: Parâmetros adicionais
                - max_dorks: Número máximo de dorks para usar (default: 5)
                - parallel: Se True, executa dorks em paralelo (default: True)
                
        Returns:
            Dicionário com todos os resultados encontrados
        """
        
        max_dorks = kwargs.get("max_dorks", 5)
        parallel = kwargs.get("parallel", True)
        
        dorks = self._build_dork_queries(query)[:max_dorks]
        
        self.logger.info(f"Iniciando Google Dorks search para '{query}' com {len(dorks)} dorks")
        
        all_results = []
        
        if parallel:
            # Executa todas as dorks em paralelo
            tasks = [self._search_dork(dork) for dork in dorks]
            results_list = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in results_list:
                if isinstance(result, list):
                    all_results.extend(result)
                elif isinstance(result, Exception):
                    self.logger.error(f"Erro em task paralela: {str(result)}")
        else:
            # Executa sequencialmente
            for dork in dorks:
                results = await self._search_dork(dork)
                all_results.extend(results)
        
        # Remove duplicatas por URL
        seen_urls = set()
        unique_results = []
        for result in all_results:
            if result["url"] not in seen_urls:
                seen_urls.add(result["url"])
                unique_results.append(result)
        
        normalized_data = {
            "query": query,
            "dorks_used": dorks,
            "total_results": len(unique_results),
            "results": unique_results,
        }
        
        return self.normalize_data(normalized_data)
