"""
NOXIS Intelligence - Scrapers Module
"""
from app.scrapers.base_scraper import BaseScraper, ScraperError
from app.scrapers.google_dorks_scraper import GoogleDorksScraper
from app.scrapers.portal_transparencia_scraper import PortalTransparenciaScraper
from app.scrapers.bnmp_scraper import BNMPScraper
from app.scrapers.social_media_scraper import SocialMediaScraper

__all__ = [
    "BaseScraper",
    "ScraperError",
    "GoogleDorksScraper",
    "PortalTransparenciaScraper",
    "BNMPScraper",
    "SocialMediaScraper",
]
