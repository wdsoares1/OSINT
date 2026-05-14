"""
NOXIS Intelligence - Logging Configuration
"""
import logging
from app.core.config import settings


def setup_logging():
    """Configura o sistema de logging da aplicação"""
    
    log_format = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    
    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL),
        format=log_format,
        handlers=[
            logging.StreamHandler(),
        ]
    )
    
    logger = logging.getLogger("NOXIS")
    return logger


logger = setup_logging()
