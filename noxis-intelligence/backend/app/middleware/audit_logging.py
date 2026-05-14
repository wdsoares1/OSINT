"""
NOXIS Intelligence - Audit Logging Middleware
Middleware para registrar todas as consultas no banco de dados.
"""
import time
from datetime import datetime
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.orm import Session
from app.core.logging_config import logger
from app.models.schemas import AuditLog


class AuditLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware que intercepta todas as requisições e registra logs de auditoria.
    
    Funcionalidades:
    - Registra timestamp, operador, tipo de ação, identificador buscado
    - Captura IP address e User-Agent
    - Calcula duração da requisição
    - Armazena resumo dos resultados
    """
    
    def __init__(self, app, db_session_factory):
        super().__init__(app)
        self.db_session_factory = db_session_factory
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Ignora requisições para endpoints estáticos e health check
        skip_paths = ["/docs", "/redoc", "/openapi.json", "/health", "/static"]
        if any(request.url.path.startswith(path) for path in skip_paths):
            return await call_next(request)
        
        # Captura informações da requisição
        start_time = time.time()
        
        # Extrai ID do operador dos headers ou query params
        operator_id = request.headers.get("X-Operator-ID", "anonymous")
        operator_name = request.headers.get("X-Operator-Name", "Anonymous")
        
        # Extrai identificador da query (CPF, Nome, etc.)
        query_identifier = request.query_params.get("q", "")
        if not query_identifier and request.method == "POST":
            # Tenta extrair do body para requisições POST
            try:
                body = await request.json()
                query_identifier = body.get("query", body.get("identifier", ""))
            except Exception:
                pass
        
        # Determina tipo de ação baseado no método e path
        action_type = self._determine_action_type(request.method, request.url.path)
        
        # Determina tipo de query (CPF, NOME, CNPJ, etc.)
        query_type = self._determine_query_type(query_identifier)
        
        # Processa a requisição
        response = await call_next(request)
        
        # Calcula duração
        duration_ms = (time.time() - start_time) * 1000
        
        # Determina status baseado no código de resposta
        if response.status_code >= 500:
            status = "error"
        elif response.status_code >= 400:
            status = "partial"
        else:
            status = "success"
        
        # Registra no banco de dados (de forma assíncrona/fire-and-forget)
        try:
            self._log_audit(
                operator_id=operator_id,
                operator_name=operator_name,
                action_type=action_type,
                query_identifier=query_identifier,
                query_type=query_type,
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent", ""),
                status=status,
                duration_ms=duration_ms,
            )
        except Exception as e:
            logger.error(f"Erro ao registrar log de auditoria: {str(e)}")
        
        return response
    
    def _determine_action_type(self, method: str, path: str) -> str:
        """Determina o tipo de ação baseado no método HTTP e path"""
        
        if method == "GET":
            if "/search" in path:
                return "SEARCH"
            elif "/entity" in path:
                return "VIEW_ENTITY"
            elif "/case" in path:
                return "VIEW_CASE"
            elif "/export" in path:
                return "EXPORT"
            else:
                return "VIEW"
        elif method == "POST":
            if "/search" in path:
                return "SEARCH"
            elif "/entity" in path:
                return "CREATE_ENTITY"
            elif "/case" in path:
                return "CREATE_CASE"
            else:
                return "CREATE"
        elif method == "PUT":
            return "UPDATE"
        elif method == "DELETE":
            return "DELETE"
        else:
            return "OTHER"
    
    def _determine_query_type(self, identifier: str) -> str:
        """Determina o tipo de identificador (CPF, CNPJ, NOME, etc.)"""
        
        if not identifier:
            return "UNKNOWN"
        
        # Remove caracteres não numéricos para verificação
        clean_id = "".join(filter(str.isdigit, identifier))
        
        if len(clean_id) == 11:
            return "CPF"
        elif len(clean_id) == 14:
            return "CNPJ"
        elif len(clean_id) in [9, 10, 11]:  # RG varia por estado
            return "RG"
        elif "@" in identifier:
            return "EMAIL"
        else:
            return "NOME"
    
    def _log_audit(
        self,
        operator_id: str,
        operator_name: str,
        action_type: str,
        query_identifier: str,
        query_type: str,
        ip_address: str,
        user_agent: str,
        status: str,
        duration_ms: float,
    ):
        """Registra entrada no banco de dados de auditoria"""
        
        db = next(self.db_session_factory())
        
        try:
            audit_log = AuditLog(
                operator_id=operator_id,
                operator_name=operator_name,
                action_type=action_type,
                query_identifier=query_identifier,
                query_type=query_type,
                ip_address=ip_address,
                user_agent=user_agent,
                status=status,
                duration_ms=duration_ms,
                sources_consulted=[],  # Será preenchido pelo endpoint específico
                results_summary={},     # Será preenchido pelo endpoint específico
            )
            
            db.add(audit_log)
            db.commit()
            
            logger.info(
                f"AUDIT: {action_type} by {operator_id} - "
                f"Query: {query_identifier} ({query_type}) - "
                f"Status: {status} - Duration: {duration_ms:.2f}ms"
            )
            
        except Exception as e:
            db.rollback()
            logger.error(f"Erro ao salvar log de auditoria: {str(e)}")
            raise
        finally:
            db.close()
