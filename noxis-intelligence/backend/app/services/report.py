"""
NOXIS Intelligence - Report Service
Serviço para geração de relatórios e exportação de investigações.
"""
import json
import base64
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path

from app.core.logging_config import logger


class ReportService:
    """
    Serviço para geração de relatórios de investigação OSINT.
    
    Funcionalidades:
    - Gerar relatório em PDF (via HTML)
    - Exportar dados em JSON/CSV
    - Criar resumo executivo automático
    - Gerar linha do tempo de descobertas
    """

    def __init__(self):
        self.logger = logger

    def generate_executive_summary(
        self,
        query: str,
        query_type: str,
        consolidated_results: Dict[str, Any],
    ) -> str:
        """
        Gera resumo executivo em texto natural.
        
        Args:
            query: Identificador buscado
            query_type: Tipo de query
            consolidated_results: Resultados consolidados do OSINT
            
        Returns:
            Texto do resumo executivo
        """
        
        summary = consolidated_results.get("summary", {})
        findings = consolidated_results.get("findings", [])
        risk_indicators = consolidated_results.get("risk_indicators", [])
        
        risk_level = summary.get("risk_level", "UNKNOWN")
        risk_score = summary.get("risk_score", 0)
        total_findings = summary.get("total_findings", 0)
        
        # Constrói resumo
        lines = []
        lines.append(f"RELATÓRIO EXECUTIVO - NOXIS Intelligence")
        lines.append(f"=" * 50)
        lines.append(f"Data de geração: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        lines.append(f"Identificador: {query}")
        lines.append(f"Tipo: {query_type}")
        lines.append("")
        
        # Seção de classificação de risco
        lines.append("CLASSIFICAÇÃO DE RISCO")
        lines.append("-" * 30)
        lines.append(f"Nível: {risk_level}")
        lines.append(f"Score: {risk_score:.1f}/100")
        lines.append(f"Total de achados: {total_findings}")
        lines.append("")
        
        # Indicadores de risco
        if risk_indicators:
            lines.append("INDICADORES DE RISCO IDENTIFICADOS")
            lines.append("-" * 30)
            for i, indicator in enumerate(risk_indicators, 1):
                lines.append(f"{i}. {indicator}")
            lines.append("")
        
        # Achados críticos
        critical_findings = [f for f in findings if f.get("relevance") == "CRITICAL"]
        if critical_findings:
            lines.append("ACHADOS CRÍTICOS")
            lines.append("-" * 30)
            for finding in critical_findings:
                finding_type = finding.get("type", "")
                source = finding.get("source", "")
                data = finding.get("data", {})
                
                if finding_type == "MANDADO":
                    lines.append(f"• Mandado encontrado via {source}")
                    lines.append(f"  - Tipo: {data.get('tipo', 'N/A')}")
                    lines.append(f"  - Situação: {data.get('situacao', 'N/A')}")
                    lines.append(f"  - Órgão: {data.get('orgao_emissor', 'N/A')}")
            lines.append("")
        
        # Resumo por fonte
        lines.append("RESUMO POR FONTE CONSULTADA")
        lines.append("-" * 30)
        
        sources_consulted = consolidated_results.get("sources_consulted", [])
        for source in sources_consulted:
            source_findings = [f for f in findings if f.get("source") == source.upper().replace("_", "")]
            count = len(source_findings)
            
            source_name = source.replace("_", " ").title()
            status = "OK" if source not in consolidated_results.get("sources_with_errors", []) else "ERRO"
            
            lines.append(f"• {source_name}: {count} achado(s) [{status}]")
        
        lines.append("")
        lines.append("=" * 50)
        lines.append("FIM DO RELATÓRIO")
        
        return "\n".join(lines)

    def generate_html_report(
        self,
        query: str,
        query_type: str,
        consolidated_results: Dict[str, Any],
        graph_data: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Gera relatório em formato HTML para exportação ou visualização.
        
        Args:
            query: Identificador buscado
            query_type: Tipo de query
            consolidated_results: Resultados consolidados
            graph_data: Dados do grafo de relacionamentos (opcional)
            
        Returns:
            HTML completo do relatório
        """
        
        summary = consolidated_results.get("summary", {})
        findings = consolidated_results.get("findings", [])
        risk_indicators = consolidated_results.get("risk_indicators", [])
        
        risk_level = summary.get("risk_level", "UNKNOWN")
        risk_score = summary.get("risk_score", 0)
        
        # Cores baseadas no nível de risco
        risk_colors = {
            "CRITICAL": "#dc2626",
            "HIGH": "#ea580c",
            "MEDIUM": "#ca8a04",
            "LOW": "#16a34a",
            "UNKNOWN": "#6b7280",
        }
        risk_color = risk_colors.get(risk_level, "#6b7280")
        
        html = f'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Relatório NOXIS - {query}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #0a0e13; color: #e5e7eb; line-height: 1.6; }}
        .container {{ max-width: 1200px; margin: 0 auto; padding: 2rem; }}
        .header {{ background: linear-gradient(135deg, #1c2025 0%, #2563eb 100%); padding: 2rem; border-radius: 8px; margin-bottom: 2rem; }}
        .header h1 {{ color: #fff; font-size: 1.8rem; margin-bottom: 0.5rem; }}
        .header p {{ color: #9ca3af; }}
        .risk-badge {{ display: inline-block; padding: 0.5rem 1rem; border-radius: 4px; background: {risk_color}; color: #fff; font-weight: bold; }}
        .section {{ background: #1c2025; padding: 1.5rem; border-radius: 8px; margin-bottom: 1.5rem; }}
        .section h2 {{ color: #2563eb; margin-bottom: 1rem; font-size: 1.3rem; border-bottom: 1px solid #374151; padding-bottom: 0.5rem; }}
        .stat-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-bottom: 1rem; }}
        .stat-card {{ background: #2563eb; padding: 1rem; border-radius: 6px; text-align: center; }}
        .stat-value {{ font-size: 2rem; font-weight: bold; color: #fff; }}
        .stat-label {{ color: #9ca3af; font-size: 0.9rem; }}
        .finding-card {{ background: #0f172a; padding: 1rem; border-radius: 6px; margin-bottom: 0.75rem; border-left: 4px solid #2563eb; }}
        .finding-card.critical {{ border-left-color: #dc2626; }}
        .finding-card.high {{ border-left-color: #ea580c; }}
        .finding-card.medium {{ border-left-color: #ca8a04; }}
        .indicator {{ background: #374151; padding: 0.5rem 1rem; border-radius: 4px; margin: 0.25rem 0; }}
        .timestamp {{ color: #6b7280; font-size: 0.85rem; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 1rem; }}
        th, td {{ padding: 0.75rem; text-align: left; border-bottom: 1px solid #374151; }}
        th {{ background: #2563eb; color: #fff; }}
        tr:hover {{ background: #1f2937; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔍 NOXIS Intelligence - Relatório de Investigação</h1>
            <p>Identificador: <strong>{query}</strong> | Tipo: {query_type}</p>
            <p class="timestamp">Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</p>
        </div>
        
        <div class="section">
            <h2>📊 Classificação de Risco</h2>
            <div class="stat-grid">
                <div class="stat-card">
                    <div class="stat-value" style="color: {risk_color}">{risk_level}</div>
                    <div class="stat-label">Nível de Risco</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{risk_score:.1f}</div>
                    <div class="stat-label">Score (0-100)</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{summary.get('total_findings', 0)}</div>
                    <div class="stat-label">Total de Achados</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{"SIM" if summary.get('has_critical_findings') else "NÃO"}</div>
                    <div class="stat-label">Achados Críticos</div>
                </div>
            </div>
        </div>
        
        {self._generate_risk_indicators_html(risk_indicators)}
        {self._generate_findings_html(findings)}
        {self._generate_sources_html(consolidated_results)}
        {self._generate_graph_html(graph_data) if graph_data else ''}
        
        <div class="section" style="text-align: center; color: #6b7280;">
            <p>NOXIS Intelligence Platform v1.0.0</p>
            <p class="timestamp">Relatório gerado automaticamente - Uso restrito a órgãos de controle</p>
        </div>
    </div>
</body>
</html>'''
        
        return html

    def _generate_risk_indicators_html(self, indicators: List[str]) -> str:
        """Gera HTML para indicadores de risco"""
        
        if not indicators:
            return ""
        
        items = "".join([f'<div class="indicator">⚠️ {ind}</div>' for ind in indicators])
        
        return f'''
        <div class="section">
            <h2>⚠️ Indicadores de Risco</h2>
            {items}
        </div>
        '''

    def _generate_findings_html(self, findings: List[Dict[str, Any]]) -> str:
        """Gera HTML para lista de achados"""
        
        if not findings:
            return '<div class="section"><h2>📋 Achados</h2><p>Nenhum achado relevante encontrado.</p></div>'
        
        cards = []
        for finding in findings:
            relevance = finding.get("relevance", "LOW").lower()
            finding_type = finding.get("type", "UNKNOWN")
            source = finding.get("source", "Unknown")
            count = finding.get("count")
            
            card_class = "finding-card"
            if relevance in ["critical", "high", "medium"]:
                card_class += f" {relevance}"
            
            details = ""
            if count:
                details = f"<p><strong>Quantidade:</strong> {count}</p>"
            
            cards.append(f'''
            <div class="{card_class}">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <strong>{finding_type}</strong>
                    <span style="color: #6b7280; font-size: 0.85rem;">{source}</span>
                </div>
                {details}
                <p style="color: #9ca3af; font-size: 0.9rem; margin-top: 0.5rem;">Relevância: {relevance.upper()}</p>
            </div>
            ''')
        
        return f'''
        <div class="section">
            <h2>📋 Achados Detalhados</h2>
            {''.join(cards)}
        </div>
        '''

    def _generate_sources_html(self, results: Dict[str, Any]) -> str:
        """Gera HTML para fontes consultadas"""
        
        sources = results.get("sources_consulted", [])
        errors = results.get("sources_with_errors", [])
        
        if not sources:
            return ""
        
        rows = ""
        for source in sources:
            status = "❌ ERRO" if source in errors else "✅ SUCESSO"
            source_name = source.replace("_", " ").title()
            rows += f"<tr><td>{source_name}</td><td>{status}</td></tr>"
        
        return f'''
        <div class="section">
            <h2>🔗 Fontes Consultadas</h2>
            <table>
                <thead>
                    <tr><th>Fonte</th><th>Status</th></tr>
                </thead>
                <tbody>
                    {rows}
                </tbody>
            </table>
        </div>
        '''

    def _generate_graph_html(self, graph_data: Dict[str, Any]) -> str:
        """Gera HTML para visualização do grafo"""
        
        nodes = graph_data.get("nodes", [])
        edges = graph_data.get("edges", [])
        
        return f'''
        <div class="section">
            <h2>🕸️ Grafo de Relacionamentos</h2>
            <div class="stat-grid">
                <div class="stat-card">
                    <div class="stat-value">{len(nodes)}</div>
                    <div class="stat-label">Nós</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{len(edges)}</div>
                    <div class="stat-label">Conexões</div>
                </div>
            </div>
            <p style="color: #9ca3af; margin-top: 1rem;">
                Grafo exportável em formatos JSON e GEXF para análise em ferramentas especializadas.
            </p>
        </div>
        '''

    def export_to_json(
        self,
        consolidated_results: Dict[str, Any],
        pretty: bool = True,
    ) -> str:
        """Exporta resultados como JSON"""
        
        indent = 2 if pretty else None
        return json.dumps(consolidated_results, indent=indent, ensure_ascii=False, default=str)

    def export_findings_to_csv(self, findings: List[Dict[str, Any]]) -> str:
        """Exporta achados como CSV"""
        
        if not findings:
            return "type,source,relevance,count\n"
        
        lines = ["type,source,relevance,count"]
        
        for finding in findings:
            line = '{},{},{},{}'.format(
                finding.get("type", ""),
                finding.get("source", ""),
                finding.get("relevance", ""),
                finding.get("count", ""),
            )
            lines.append(line)
        
        return "\n".join(lines)

    def save_report(
        self,
        html_content: str,
        output_path: str,
    ) -> Path:
        """Salva relatório HTML em arquivo"""
        
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, "w", encoding="utf-8") as f:
            f.write(html_content)
        
        self.logger.info(f"Relatório salvo em: {path}")
        return path
