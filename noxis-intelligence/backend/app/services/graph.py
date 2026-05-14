"""
NOXIS Intelligence - Graph Service
Serviço para geração e análise de grafos de relacionamentos.
"""
import json
from typing import Dict, List, Any, Optional, Set, Tuple
from datetime import datetime
from collections import defaultdict

from app.core.logging_config import logger


class GraphService:
    """
    Serviço para construção e análise de grafos de relacionamentos entre entidades.
    
    Funcionalidades:
    - Construir grafo a partir de resultados OSINT
    - Identificar conexões entre entidades
    - Calcular centralidade e relevância de nós
    - Exportar grafo em formatos compatíveis com visualizadores
    """

    def __init__(self):
        self.logger = logger
        self.nodes: Dict[str, Dict[str, Any]] = {}
        self.edges: List[Dict[str, Any]] = []

    def build_graph_from_findings(
        self,
        findings: List[Dict[str, Any]],
        primary_entity: str,
    ) -> Dict[str, Any]:
        """
        Constrói grafo a partir de descobertas OSINT.
        
        Args:
            findings: Lista de findings do OSINT
            primary_entity: Entidade principal da investigação
            
        Returns:
            Estrutura de grafo (nodes + edges)
        """
        
        self.nodes = {}
        self.edges = []
        
        # Adiciona entidade principal
        self._add_node(
            node_id=primary_entity,
            label=primary_entity,
            type="PRIMARY",
            is_primary=True,
        )
        
        # Processa cada finding para extrair entidades e relações
        for finding in findings:
            self._process_finding(finding, primary_entity)
        
        return {
            "nodes": list(self.nodes.values()),
            "edges": self.edges,
            "metadata": {
                "total_nodes": len(self.nodes),
                "total_edges": len(self.edges),
                "primary_entity": primary_entity,
                "generated_at": datetime.utcnow().isoformat(),
            },
        }

    def _add_node(
        self,
        node_id: str,
        label: str,
        type: str,
        **kwargs,
    ):
        """Adiciona um nó ao grafo"""
        
        if node_id not in self.nodes:
            self.nodes[node_id] = {
                "id": node_id,
                "label": label,
                "type": type,
                "is_primary": kwargs.get("is_primary", False),
                "metadata": kwargs.get("metadata", {}),
            }
        else:
            # Atualiza metadata se já existir
            self.nodes[node_id]["metadata"].update(kwargs.get("metadata", {}))

    def _add_edge(
        self,
        source: str,
        target: str,
        relationship: str,
        **kwargs,
    ):
        """Adiciona uma aresta ao grafo"""
        
        edge = {
            "source": source,
            "target": target,
            "relationship": relationship,
            "metadata": kwargs.get("metadata", {}),
        }
        
        # Evita duplicatas
        if not any(
            e["source"] == source and e["target"] == target and e["relationship"] == relationship
            for e in self.edges
        ):
            self.edges.append(edge)

    def _process_finding(self, finding: Dict[str, Any], primary_entity: str):
        """Processa um finding para extrair entidades e relações"""
        
        finding_type = finding.get("type", "")
        source = finding.get("source", "")
        data = finding.get("data", {})
        
        if finding_type == "MANDADO":
            # Extrai órgão emissor como entidade relacionada
            orgao = data.get("orgao_emissor", "")
            if orgao:
                self._add_node(
                    node_id=f"orgao:{orgao}",
                    label=orgao,
                    type="ORGANIZATION",
                    metadata={"source": source},
                )
                self._add_edge(
                    source=primary_entity,
                    target=f"orgao:{orgao}",
                    relationship="POSSUI_MANDADO",
                    metadata={
                        "tipo_mandado": data.get("tipo", ""),
                        "situacao": data.get("situacao", ""),
                    },
                )
        
        elif finding_type == "SERVIDOR":
            # Extrai órgão público como entidade relacionada
            if isinstance(data, list) and len(data) > 0:
                servidor_data = data[0]
                orgao = servidor_data.get("orgao", "Órgão não identificado")
                
                self._add_node(
                    node_id=f"orgao:{orgao}",
                    label=orgao,
                    type="GOVERNMENT_AGENCY",
                    metadata={"source": source},
                )
                self._add_edge(
                    source=primary_entity,
                    target=f"orgao:{orgao}",
                    relationship="VINCULO_SERVIDOR",
                    metadata={
                        "cargo": servidor_data.get("cargo", ""),
                        "lotacao": servidor_data.get("lotacao", ""),
                    },
                )
        
        elif finding_type == "DESPESAS":
            # Agrupa despesas por órgão/empresa
            if isinstance(data, list):
                orgaos_vistos: Set[str] = set()
                
                for despesa in data[:5]:  # Limita para não sobrecarregar
                    orgao = despesa.get("orgao", "Desconhecido")
                    
                    if orgao and orgao not in orgaos_vistos:
                        orgaos_vistos.add(orgao)
                        self._add_node(
                            node_id=f"orgao:{orgao}",
                            label=orgao,
                            type="GOVERNMENT_AGENCY",
                            metadata={"source": source},
                        )
                        self._add_edge(
                            source=primary_entity,
                            target=f"orgao:{orgao}",
                            relationship="RECEBEU_DESPESA",
                            metadata={"count": finding.get("count", 0)},
                        )
        
        elif finding_type == "PRESENCA_DIGITAL":
            # Extrai domínios/sites relacionados
            if isinstance(data, list):
                dominios_vistos: Set[str] = set()
                
                for result in data[:10]:
                    url = result.get("url", "")
                    if url:
                        try:
                            dominio = url.split("//")[1].split("/")[0]
                            
                            if dominio not in dominios_vistos:
                                dominios_vistos.add(dominio)
                                
                                self._add_node(
                                    node_id=f"domain:{dominio}",
                                    label=dominio,
                                    type="WEBSITE",
                                    metadata={"source": source},
                                )
                                self._add_edge(
                                    source=primary_entity,
                                    target=f"domain:{dominio}",
                                    relationship="MENCIONADO_EM",
                                    metadata={
                                        "titulo": result.get("title", ""),
                                        "snippet": result.get("snippet", "")[:100],
                                    },
                                )
                        except (IndexError, ValueError):
                            continue
        
        elif finding_type == "REDES_SOCIAIS":
            # Extrai perfis sociais
            if isinstance(data, dict):
                for platform, mentions in data.items():
                    if isinstance(mentions, list):
                        for mention in mentions[:3]:
                            author = mention.get("author", "")
                            if author:
                                node_id = f"social:{platform}:{author}"
                                self._add_node(
                                    node_id=node_id,
                                    label=f"{author} ({platform})",
                                    type="SOCIAL_PROFILE",
                                    metadata={
                                        "platform": platform,
                                        "source": source,
                                    },
                                )
                                self._add_edge(
                                    source=primary_entity,
                                    target=node_id,
                                    relationship="MENCAO_REDE_SOCIAL",
                                    metadata={
                                        "content": mention.get("content", "")[:100],
                                    },
                                )

    def calculate_centrality(self) -> Dict[str, float]:
        """
        Calcula centralidade de grau para cada nó.
        
        Returns:
            Dicionário com score de centralidade por nó
        """
        
        centrality = defaultdict(float)
        
        for edge in self.edges:
            centrality[edge["source"]] += 1
            centrality[edge["target"]] += 1
        
        # Normaliza
        max_connections = max(centrality.values()) if centrality else 1
        
        return {
            node_id: connections / max_connections
            for node_id, connections in centrality.items()
        }

    def identify_clusters(self) -> List[List[str]]:
        """
        Identifica clusters/conexos no grafo usando BFS.
        
        Returns:
            Lista de clusters (cada cluster é uma lista de node_ids)
        """
        
        visited: Set[str] = set()
        clusters: List[List[str]] = []
        
        # Build adjacency list
        adj: Dict[str, List[str]] = defaultdict(list)
        for edge in self.edges:
            adj[edge["source"]].append(edge["target"])
            adj[edge["target"]].append(edge["source"])
        
        for node_id in self.nodes.keys():
            if node_id not in visited:
                # BFS para encontrar todo o cluster
                cluster = []
                queue = [node_id]
                
                while queue:
                    current = queue.pop(0)
                    if current not in visited:
                        visited.add(current)
                        cluster.append(current)
                        queue.extend(adj[current])
                
                if cluster:
                    clusters.append(cluster)
        
        return clusters

    def export_to_json(self) -> str:
        """Exporta grafo como JSON"""
        
        return json.dumps({
            "nodes": list(self.nodes.values()),
            "edges": self.edges,
        }, indent=2, ensure_ascii=False)

    def export_to_gexf(self) -> str:
        """
        Exporta grafo no formato GEXF (compatível com Gephi).
        
        Returns:
            String XML no formato GEXF
        """
        
        gexf_header = '''<?xml version="1.0" encoding="UTF-8"?>
<gexf xmlns="http://www.gexf.net/1.2draft" version="1.2">
    <meta lastmodifieddate="{}">
        <creator>NOXIS Intelligence</creator>
        <description>Grafo de relacionamentos OSINT</description>
    </meta>
    <graph defaultedgetype="undirected">
'''.format(datetime.utcnow().isoformat())
        
        # Nodes
        nodes_xml = '        <nodes>\n'
        for node in self.nodes.values():
            node_type = node.get("type", "UNKNOWN")
            color = self._get_node_color(node_type)
            
            nodes_xml += '''            <node id="{}" label="{}" type="{}">
                <viz>
                    <color r="{}" g="{}" b="{}" />
                </viz>
            </node>\n'''.format(
                self._escape_xml(node["id"]),
                self._escape_xml(node["label"]),
                node_type,
                color[0], color[1], color[2],
            )
        nodes_xml += '        </nodes>\n'
        
        # Edges
        edges_xml = '        <edges>\n'
        for i, edge in enumerate(self.edges):
            edges_xml += '''            <edge id="{}" source="{}" target="{}" label="{}" />\n'''.format(
                i,
                self._escape_xml(edge["source"]),
                self._escape_xml(edge["target"]),
                self._escape_xml(edge["relationship"]),
            )
        edges_xml += '        </edges>\n'
        
        gexf_footer = '''    </graph>
</gexf>'''
        
        return gexf_header + nodes_xml + edges_xml + gexf_footer

    def _get_node_color(self, node_type: str) -> Tuple[int, int, int]:
        """Retorna cor RGB baseada no tipo de nó"""
        
        colors = {
            "PRIMARY": (255, 0, 0),  # Vermelho
            "PERSON": (0, 128, 255),  # Azul
            "ORGANIZATION": (0, 200, 0),  # Verde
            "GOVERNMENT_AGENCY": (128, 0, 128),  # Roxo
            "WEBSITE": (255, 165, 0),  # Laranja
            "SOCIAL_PROFILE": (255, 192, 203),  # Rosa
            "UNKNOWN": (128, 128, 128),  # Cinza
        }
        
        return colors.get(node_type, colors["UNKNOWN"])

    def _escape_xml(self, text: str) -> str:
        """Escapa caracteres especiais para XML"""
        
        if not text:
            return ""
        
        replacements = {
            "&": "&amp;",
            "<": "&lt;",
            ">": "&gt;",
            '"': "&quot;",
            "'": "&apos;",
        }
        
        for char, replacement in replacements.items():
            text = text.replace(char, replacement)
        
        return text

    def reset(self):
        """Reseta o grafo para nova construção"""
        
        self.nodes = {}
        self.edges = []
