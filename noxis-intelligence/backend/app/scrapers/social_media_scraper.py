"""
NOXIS Intelligence - Social Media Scraper
Monitora menções em redes sociais abertas (Surface Web).
"""
import asyncio
import urllib.parse
from typing import Dict, List, Any, Optional
from app.scrapers.base_scraper import BaseScraper


class SocialMediaScraper(BaseScraper):
    """
    Scraper para monitoramento de menções em redes sociais.
    
    Plataformas suportadas (via buscas públicas):
    - Twitter/X
    - Facebook (páginas públicas)
    - Instagram (perfis públicos)
    - LinkedIn (perfis públicos)
    - Reddit
    - YouTube
    """
    
    def __init__(self):
        super().__init__(name="SocialMediaScraper")
        self.platforms = {
            "twitter": "https://twitter.com/search?q={query}&f=live",
            "facebook": "https://www.facebook.com/public/{query}",
            "instagram": "https://www.instagram.com/web/search/topsearch/?query={query}",
            "linkedin": "https://www.linkedin.com/search/results/all/?keywords={query}",
            "reddit": "https://www.reddit.com/search?q={query}",
            "youtube": "https://www.youtube.com/results?search_query={query}",
        }
        
    async def _search_platform(
        self, 
        platform: str, 
        query: str
    ) -> List[Dict[str, str]]:
        """Busca menções em uma plataforma específica"""
        
        if platform not in self.platforms:
            return []
        
        url_template = self.platforms[platform]
        query_encoded = urllib.parse.quote(query.strip())
        url = url_template.format(query=query_encoded)
        
        results = []
        
        try:
            html = await self.fetch_with_playwright(url, wait_selector=None)
            
            if not html:
                return results
            
            soup = self.parse_html(html)
            
            # Seletores específicos por plataforma
            selectors = {
                "twitter": ["article", "[data-testid='tweet']"],
                "facebook": ["[role='article']", ".userContent"],
                "instagram": ["article", "_aacli"],
                "linkedin": [".reusable-search__result-container", ".search-result"],
                "reddit": ["shreddit-post", ".Post", ".thing"],
                "youtube": ["ytd-video-renderer", ".ytd-video-renderer"],
            }
            
            platform_selectors = selectors.get(platform, [])
            
            for selector in platform_selectors:
                elements = soup.select(selector)
                
                for element in elements[:5]:  # Limita a 5 resultados por plataforma
                    result_data = self._extract_social_post(element, platform)
                    if result_data:
                        results.append(result_data)
                
                if results:
                    break  # Se encontrou resultados com um seletor, não tenta outros
                    
        except Exception as e:
            self.logger.error(f"Erro ao buscar {platform} para '{query}': {str(e)}")
        
        return results
    
    def _extract_social_post(self, element, platform: str) -> Optional[Dict[str, str]]:
        """Extrai dados de um post/publicação social"""
        
        try:
            post_data = {
                "platform": platform,
                "content": "",
                "author": "",
                "url": "",
                "timestamp": "",
            }
            
            # Extração específica por plataforma
            if platform == "twitter":
                content_elem = element.select_one("[lang]")
                author_elem = element.select_one("[data-testid='User-Name']")
                time_elem = element.select_one("time")
                
                post_data["content"] = content_elem.get_text(strip=True)[:280] if content_elem else ""
                post_data["author"] = author_elem.get_text(strip=True) if author_elem else ""
                post_data["timestamp"] = time_elem.get("datetime", "") if time_elem else ""
                
            elif platform == "facebook":
                content_elem = element.select_one(".userContent, p")
                author_elem = element.select_one("strong, h3")
                
                post_data["content"] = content_elem.get_text(strip=True)[:500] if content_elem else ""
                post_data["author"] = author_elem.get_text(strip=True) if author_elem else ""
                
            elif platform == "instagram":
                content_elem = element.select_one("span")
                author_elem = element.select_one("a[href*='/p/'] ~ a")
                
                post_data["content"] = content_elem.get_text(strip=True)[:280] if content_elem else ""
                post_data["author"] = author_elem.get_text(strip=True) if author_elem else ""
                
            elif platform == "linkedin":
                content_elem = element.select_one(".feed-shared-update-v2__description")
                author_elem = element.select_one(".feed-shared-actor__name")
                
                post_data["content"] = content_elem.get_text(strip=True)[:500] if content_elem else ""
                post_data["author"] = author_elem.get_text(strip=True) if author_elem else ""
                
            elif platform == "reddit":
                title_elem = element.select_one("h3, .title")
                author_elem = element.select_one("a.author, .byline")
                
                post_data["content"] = title_elem.get_text(strip=True)[:300] if title_elem else ""
                post_data["author"] = author_elem.get_text(strip=True) if author_elem else ""
                
            elif platform == "youtube":
                title_elem = element.select_one("#video-title, h3")
                channel_elem = element.select_one("#channel-name, .ytd-channel-name")
                
                post_data["content"] = title_elem.get_text(strip=True)[:200] if title_elem else ""
                post_data["author"] = channel_elem.get_text(strip=True) if channel_elem else ""
            
            # Tenta extrair URL
            link_elem = element.select_one("a[href]")
            if link_elem and link_elem.get("href"):
                href = link_elem.get("href")
                if href.startswith("/"):
                    href = f"https://{platform}.com{href}"
                post_data["url"] = href
            
            # Valida se tem conteúdo mínimo
            if post_data["content"] or post_data["author"]:
                return post_data
                
        except Exception as e:
            self.logger.error(f"Erro ao extrair post do {platform}: {str(e)}")
        
        return None
    
    async def scrape(self, query: str, **kwargs) -> Dict[str, Any]:
        """
        Realiza busca em múltiplas redes sociais.
        
        Args:
            query: Nome ou termo para busca
            **kwargs: Parâmetros adicionais
                - platforms: Lista de plataformas para buscar (default: todas)
                - max_results_per_platform: Máximo de resultados por plataforma (default: 5)
                - parallel: Se True, executa buscas em paralelo (default: True)
                
        Returns:
            Dicionário com menções encontradas nas redes sociais
        """
        
        platforms = kwargs.get("platforms", list(self.platforms.keys()))
        max_results_per_platform = kwargs.get("max_results_per_platform", 5)
        parallel = kwargs.get("parallel", True)
        
        self.logger.info(f"Iniciando busca em redes sociais para '{query}'")
        
        all_results = []
        
        if parallel:
            # Executa buscas em todas as plataformas em paralelo
            tasks = [self._search_platform(platform, query) for platform in platforms]
            results_list = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in results_list:
                if isinstance(result, list):
                    all_results.extend(result[:max_results_per_platform])
                elif isinstance(result, Exception):
                    self.logger.error(f"Erro em task paralela: {str(result)}")
        else:
            # Executa sequencialmente
            for platform in platforms:
                results = await self._search_platform(platform, query)
                all_results.extend(results[:max_results_per_platform])
        
        # Agrupa resultados por plataforma
        results_by_platform = {}
        for result in all_results:
            platform = result.get("platform", "unknown")
            if platform not in results_by_platform:
                results_by_platform[platform] = []
            results_by_platform[platform].append(result)
        
        normalized_data = {
            "query": query,
            "platforms_searched": platforms,
            "total_mentions": len(all_results),
            "mentions_by_platform": results_by_platform,
        }
        
        return self.normalize_data(normalized_data)
