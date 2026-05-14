"""
NOXIS Intelligence - Base Scraper Module
Classe base para scrapers modulares com rotação de User-Agent, 
tratamento de erros e normalização de dados.
"""
import random
import asyncio
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from datetime import datetime
from playwright.async_api import async_playwright, Browser, Page
from bs4 import BeautifulSoup
import aiohttp
from app.core.config import settings
from app.core.logging_config import logger


class ScraperError(Exception):
    """Exceção personalizada para erros de scraping"""
    pass


class BaseScraper(ABC):
    """
    Classe base abstrata para todos os scrapers do NOXIS Intelligence.
    
    Implementa:
    - Rotação de User-Agents
    - Tratamento de erros e retries
    - Normalização de dados para JSON
    - Suporte a Playwright e requests assíncronos
    """
    
    def __init__(self, name: str = "BaseScraper"):
        self.name = name
        self.user_agents = settings.USER_AGENTS
        self.timeout = settings.REQUEST_TIMEOUT
        self.max_retries = settings.MAX_RETRIES
        self.retry_delay = settings.RETRY_DELAY
        self.logger = logger
        
    def _get_random_user_agent(self) -> str:
        """Retorna um User-Agent aleatório da lista configurada"""
        return random.choice(self.user_agents)
    
    def _get_headers(self, custom_headers: Optional[Dict] = None) -> Dict[str, str]:
        """Gera headers com User-Agent rotativo"""
        headers = {
            "User-Agent": self._get_random_user_agent(),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Cache-Control": "max-age=0",
        }
        if custom_headers:
            headers.update(custom_headers)
        return headers
    
    async def _fetch_with_retry(
        self, 
        session: aiohttp.ClientSession, 
        url: str, 
        method: str = "GET",
        data: Optional[Dict] = None,
        headers: Optional[Dict] = None
    ) -> Optional[aiohttp.ClientResponse]:
        """Realiza requisição HTTP com retry automático"""
        
        for attempt in range(self.max_retries):
            try:
                request_headers = self._get_headers(headers)
                
                async with session.request(
                    method=method,
                    url=url,
                    headers=request_headers,
                    json=data if method == "POST" else None,
                    timeout=aiohttp.ClientTimeout(total=self.timeout),
                    allow_redirects=True
                ) as response:
                    if response.status == 200:
                        return response
                    elif response.status == 429:  # Rate limiting
                        wait_time = self.retry_delay * (2 ** attempt)
                        self.logger.warning(f"Rate limit atingido. Aguardando {wait_time}s")
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        self.logger.error(f"Erro HTTP {response.status} em {url}")
                        return None
                        
            except aiohttp.ClientError as e:
                self.logger.error(f"Tentativa {attempt + 1} falhou: {str(e)}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay * (2 ** attempt))
                continue
            except asyncio.TimeoutError:
                self.logger.error(f"Timeout na tentativa {attempt + 1}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay * (2 ** attempt))
                continue
        
        raise ScraperError(f"Falha após {self.max_retries} tentativas em {url}")
    
    async def fetch_html(self, url: str) -> Optional[str]:
        """Busca HTML de uma URL usando aiohttp"""
        async with aiohttp.ClientSession() as session:
            try:
                response = await self._fetch_with_retry(session, url)
                if response:
                    return await response.text()
            except ScraperError as e:
                self.logger.error(f"Erro ao buscar {url}: {str(e)}")
        return None
    
    async def fetch_with_playwright(self, url: str, wait_selector: Optional[str] = None) -> Optional[str]:
        """Busca conteúdo usando Playwright para páginas JavaScript-heavy"""
        
        browser: Optional[Browser] = None
        
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=settings.HEADLESS_BROWSER,
                    args=[
                        "--disable-gpu",
                        "--no-sandbox",
                        "--disable-setuid-sandbox",
                        "--disable-dev-shm-usage",
                    ]
                )
                
                context = await browser.new_context(
                    user_agent=self._get_random_user_agent(),
                    viewport={"width": 1920, "height": 1080},
                )
                
                page = await context.new_page()
                await page.goto(url, wait_until="networkidle", timeout=settings.BROWSER_TIMEOUT)
                
                if wait_selector:
                    await page.wait_for_selector(wait_selector, timeout=10000)
                
                content = await page.content()
                await context.close()
                return content
                
        except Exception as e:
            self.logger.error(f"Erro no Playwright para {url}: {str(e)}")
            return None
        finally:
            if browser:
                await browser.close()
    
    def parse_html(self, html: str) -> BeautifulSoup:
        """Parseia HTML usando BeautifulSoup"""
        return BeautifulSoup(html, "lxml")
    
    @abstractmethod
    async def scrape(self, query: str, **kwargs) -> Dict[str, Any]:
        """
        Método abstrato que deve ser implementado por cada scraper específico.
        
        Args:
            query: Termo de busca ou identificador (CPF, Nome, etc.)
            **kwargs: Parâmetros adicionais específicos de cada scraper
            
        Returns:
            Dicionário com dados normalizados
        """
        pass
    
    def normalize_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normaliza dados brutos para o padrão NOXIS.
        Pode ser sobrescrito por scrapers específicos.
        """
        normalized = {
            "source": self.name,
            "timestamp": datetime.utcnow().isoformat(),
            "data": raw_data,
            "status": "success" if raw_data else "error",
        }
        return normalized
