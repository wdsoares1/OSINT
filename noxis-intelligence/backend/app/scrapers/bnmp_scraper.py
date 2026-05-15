"""
NOXIS Intelligence - BNMP Scraper (Banco Nacional de Mandados de Prisão)
Consulta o sistema do CNJ para verificar existência de mandados de prisão.
"""
import re
from typing import Dict, List, Any, Optional
from datetime import datetime
from app.scrapers.base_scraper import BaseScraper


class BNMPScraper(BaseScraper):
    """
    Scraper para o Banco Nacional de Mandados de Prisão (BNMP) do CNJ.
    
    O BNMP é um sistema do Conselho Nacional de Justiça que centraliza
    informações sobre mandados de prisão e alvarás de soltura.
    
    Atenção: Esta implementação usa técnicas de scraping ético.
    Para uso em produção, considere usar a API oficial quando disponível.
    """
    
    def __init__(self):
        super().__init__(name="BNMPScraper")
        self.base_url = "https://bnmp.cnj.jus.br"
        self.search_url = "https://bnmp.cnj.jus.br/pesquisar"
        
    def _validate_cpf(self, cpf: str) -> bool:
        """Valida CPF usando algoritmo de dígitos verificadores"""
        
        cpf_clean = "".join(filter(str.isdigit, cpf))
        
        if len(cpf_clean) != 11:
            return False
        
        # Verifica se todos os dígitos são iguais (CPF inválido)
        if len(set(cpf_clean)) == 1:
            return False
        
        # Calcula primeiro dígito verificador
        sum_ = sum(int(digit) * weight for digit, weight in zip(cpf_clean[:9], range(10, 1, -1)))
        remainder = (sum_ * 10) % 11
        digit1 = 0 if remainder == 10 else remainder
        
        # Calcula segundo dígito verificador
        sum_ = sum(int(digit) * weight for digit, weight in zip(cpf_clean[:10], range(11, 1, -1)))
        remainder = (sum_ * 10) % 11
        digit2 = 0 if remainder == 10 else remainder
        
        return int(cpf_clean[9]) == digit1 and int(cpf_clean[10]) == digit2
    
    async def search_by_cpf(self, cpf: str) -> Dict[str, Any]:
        """Busca mandados por CPF"""
        
        if not self._validate_cpf(cpf):
            return {
                "error": "CPF inválido",
                "cpf": cpf,
                "mandados": [],
            }
        
        cpf_clean = "".join(filter(str.isdigit, cpf))
        
        # Formata CPF para o padrão do BNMP (000.000.000-00)
        cpf_formatted = f"{cpf_clean[:3]}.{cpf_clean[3:6]}.{cpf_clean[6:9]}-{cpf_clean[9:]}"
        
        results = {
            "cpf": cpf_formatted,
            "mandados": [],
            "alvaras": [],
            "status": "unknown",
        }
        
        try:
            # Usa Playwright para acessar o BNMP (página JavaScript-heavy)
            html = await self.fetch_with_playwright(
                self.search_url,
                wait_selector=None  # Aguarda carregamento completo
            )
            
            if not html:
                return results
            
            soup = self.parse_html(html)
            
            # Tenta encontrar resultados na página
            # Nota: Seletores específicos podem precisar de ajuste conforme mudanças no site
            mandado_elements = soup.select(".mandado-item, .resultado-mandado, [class*='mandado']")
            
            for element in mandado_elements[:10]:  # Limita a 10 resultados
                mandado_data = self._parse_mandado_element(element)
                if mandado_data:
                    results["mandados"].append(mandado_data)
            
            # Verifica status
            if results["mandados"]:
                results["status"] = "mandados_encontrados"
            else:
                results["status"] = "sem_mandados"
                
        except Exception as e:
            self.logger.error(f"Erro ao buscar BNMP para CPF {cpf}: {str(e)}")
            results["error"] = str(e)
        
        return results
    
    async def search_by_name(self, name: str, birth_date: Optional[str] = None) -> Dict[str, Any]:
        """Busca mandados por nome (e opcionalmente data de nascimento)"""
        
        results = {
            "nome": name,
            "data_nascimento": birth_date,
            "mandados": [],
            "status": "unknown",
        }
        
        try:
            # Constrói URL de busca com parâmetros
            search_params = {
                "nome": urllib.parse.quote(name.strip()),
            }
            
            if birth_date:
                search_params["data_nascimento"] = birth_date
            
            query_string = "&".join(f"{k}={v}" for k, v in search_params.items())
            search_url = f"{self.search_url}?{query_string}"
            
            html = await self.fetch_with_playwright(search_url, wait_selector=None)
            
            if not html:
                return results
            
            soup = self.parse_html(html)
            
            mandado_elements = soup.select(".mandado-item, .resultado-mandado, [class*='mandado']")
            
            for element in mandado_elements[:10]:
                mandado_data = self._parse_mandado_element(element)
                if mandado_data:
                    results["mandados"].append(mandado_data)
            
            if results["mandados"]:
                results["status"] = "mandados_encontrados"
            else:
                results["status"] = "sem_mandados"
                
        except Exception as e:
            self.logger.error(f"Erro ao buscar BNMP por nome {name}: {str(e)}")
            results["error"] = str(e)
        
        return results
    
    def _parse_mandado_element(self, element) -> Optional[Dict[str, Any]]:
        """Parseia um elemento HTML de mandado para dicionário"""
        
        try:
            # Extrai campos comuns de mandados
            numero_mandado = element.select_one(".numero-mandado, [class*='numero']")
            tipo_mandado = element.select_one(".tipo-mandado, [class*='tipo']")
            situacao = element.select_one(".situacao, [class*='situacao']")
            data_expedicao = element.select_one(".data-expedicao, [class*='data']")
            orgao_emissor = element.select_one(".orgao-emissor, [class*='orgao']")
            
            mandado = {
                "numero": numero_mandado.get_text(strip=True) if numero_mandado else "",
                "tipo": tipo_mandado.get_text(strip=True) if tipo_mandado else "Desconhecido",
                "situacao": situacao.get_text(strip=True) if situacao else "Desconhecida",
                "data_expedicao": data_expedicao.get_text(strip=True) if data_expedicao else "",
                "orgao_emissor": orgao_emissor.get_text(strip=True) if orgao_emissor else "",
            }
            
            # Normaliza situação
            situacao_text = mandado["situacao"].lower()
            if "ativo" in situacao_text or "vigente" in situacao_text:
                mandado["ativo"] = True
            elif "cumprido" in situacao_text or "cancelado" in situacao_text:
                mandado["ativo"] = False
            else:
                mandado["ativo"] = None
            
            return mandado
            
        except Exception as e:
            self.logger.error(f"Erro ao parsear mandado: {str(e)}")
            return None
    
    async def scrape(self, query: str, **kwargs) -> Dict[str, Any]:
        """
        Realiza busca no BNMP.
        
        Args:
            query: CPF ou nome para busca
            **kwargs: Parâmetros adicionais
                - search_type: 'cpf', 'nome' ou 'auto' (default: 'auto')
                - birth_date: Data de nascimento (para busca por nome)
                - include_details: Se True, inclui detalhes completos (default: True)
                
        Returns:
            Dicionário com informações de mandados do BNMP
        """
        
        search_type = kwargs.get("search_type", "auto")
        birth_date = kwargs.get("birth_date")
        include_details = kwargs.get("include_details", True)
        
        self.logger.info(f"Iniciando busca no BNMP para '{query}'")
        
        # Detecta automaticamente o tipo de busca
        if search_type == "auto":
            if query.isdigit() and len(query) == 11:
                search_type = "cpf"
            else:
                search_type = "nome"
        
        results = {
            "query": query,
            "search_type": search_type,
            "bnmp_data": {},
        }
        
        if search_type == "cpf":
            results["bnmp_data"] = await self.search_by_cpf(query)
        elif search_type == "nome":
            results["bnmp_data"] = await self.search_by_name(query, birth_date)
        
        normalized_data = {
            "query": query,
            "bnmp": results["bnmp_data"],
            "has_warrants": len(results["bnmp_data"].get("mandados", [])) > 0,
            "active_warrants_count": sum(
                1 for m in results["bnmp_data"].get("mandados", [])
                if m.get("ativo") is True
            ),
        }
        
        return self.normalize_data(normalized_data)
