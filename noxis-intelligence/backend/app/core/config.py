"""
NOXIS Intelligence - Core Configuration
"""
from pydantic_settings import BaseSettings
from typing import List, Optional
import os


class Settings(BaseSettings):
    """Configurações da aplicação NOXIS Intelligence"""
    
    # Application
    APP_NAME: str = "NOXIS Intelligence"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://noxis:noxis_pass@localhost:5432/noxis_db")
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "noxis-secret-key-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    
    # Scraping
    USER_AGENTS: List[str] = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/120.0.0.0 Safari/537.36",
    ]
    REQUEST_TIMEOUT: int = 30
    MAX_RETRIES: int = 3
    RETRY_DELAY: float = 1.0
    
    # Playwright
    HEADLESS_BROWSER: bool = True
    BROWSER_TIMEOUT: int = 60000
    
    # APIs Externas
    PORTAL_TRANSPARENCIA_API: str = "https://api.portaldatransparencia.gov.br/api-de-dados"
    CNJ_BNMP_WS: str = "https://bnmp.cnj.jus.br/"
    
    # Logging
    LOG_LEVEL: str = "INFO"
    AUDIT_LOG_ENABLED: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
