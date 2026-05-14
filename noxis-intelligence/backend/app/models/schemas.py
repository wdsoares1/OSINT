"""
NOXIS Intelligence - Database Models
Modelos SQLAlchemy para entidades e auditoria.
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class AuditLog(Base):
    """
    Modelo para logs de auditoria.
    Registra todas as consultas realizadas no sistema.
    """
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    operator_id = Column(String(100), nullable=False, index=True)  # ID do operador que realizou a consulta
    operator_name = Column(String(255), nullable=True)
    action_type = Column(String(50), nullable=False)  # SEARCH, VIEW, EXPORT, etc.
    query_identifier = Column(String(255), nullable=False)  # CPF, Nome, ou outro identificador buscado
    query_type = Column(String(50), nullable=True)  # CPF, NOME, CNPJ, etc.
    sources_consulted = Column(JSON, nullable=True)  # Lista de fontes consultadas
    results_summary = Column(JSON, nullable=True)  # Resumo dos resultados encontrados
    ip_address = Column(String(45), nullable=True)  # IPv4 ou IPv6
    user_agent = Column(Text, nullable=True)
    status = Column(String(50), default="success")  # success, error, partial
    error_message = Column(Text, nullable=True)
    duration_ms = Column(Float, nullable=True)  # Duração da consulta em milissegundos
    
    # Relacionamentos
    entities = relationship("Entity", back_populates="audit_log", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<AuditLog(id={self.id}, operator_id='{self.operator_id}', action='{self.action_type}')>"


class Entity(Base):
    """
    Modelo para entidades investigadas (pessoas, empresas, etc.).
    """
    __tablename__ = "entities"
    
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Dados básicos
    entity_type = Column(String(50), nullable=False)  # PERSON, COMPANY, ORGANIZATION
    name = Column(String(255), nullable=False, index=True)
    document = Column(String(50), nullable=True, index=True)  # CPF, CNPJ, etc.
    document_type = Column(String(20), nullable=True)  # CPF, CNPJ, RG, etc.
    
    # Dados adicionais (armazenados como JSON para flexibilidade)
    additional_data = Column(JSON, nullable=True)
    
    # Classificação de risco
    risk_level = Column(String(20), default="UNKNOWN")  # LOW, MEDIUM, HIGH, CRITICAL, UNKNOWN
    risk_score = Column(Float, default=0.0)  # Score numérico de 0 a 100
    
    # Status da investigação
    status = Column(String(50), default="ACTIVE")  # ACTIVE, ARCHIVED, CLOSED
    tags = Column(JSON, nullable=True)  # Tags personalizadas
    
    # Chave estrangeira para o log de auditoria que criou esta entidade
    audit_log_id = Column(Integer, ForeignKey("audit_logs.id"), nullable=True)
    
    # Relacionamentos
    audit_log = relationship("AuditLog", back_populates="entities")
    findings = relationship("Finding", back_populates="entity", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Entity(id={self.id}, name='{self.name}', type='{self.entity_type}')>"


class Finding(Base):
    """
    Modelo para descobertas/achados de uma investigação.
    Cada finding está vinculado a uma entidade e representa uma informação relevante.
    """
    __tablename__ = "findings"
    
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Tipo de descoberta
    finding_type = Column(String(50), nullable=False)  # MANDADO, DESPESA, REDE_SOCIAL, PROCESSO, etc.
    source = Column(String(100), nullable=False)  # BNMP, Portal Transparencia, Google, etc.
    
    # Conteúdo da descoberta
    title = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    content = Column(JSON, nullable=True)  # Dados completos da descoberta
    
    # Metadados
    url = Column(Text, nullable=True)  # URL de origem
    timestamp_found = Column(DateTime(timezone=True), nullable=True)  # Quando foi encontrado
    confidence_score = Column(Float, default=0.0)  # Score de confiança (0-100)
    
    # Severidade/Relevância
    relevance = Column(String(20), default="MEDIUM")  # LOW, MEDIUM, HIGH, CRITICAL
    verified = Column(Boolean, default=False)  # Se a informação foi verificada manualmente
    
    # Chave estrangeira
    entity_id = Column(Integer, ForeignKey("entities.id"), nullable=False, index=True)
    
    # Relacionamentos
    entity = relationship("Entity", back_populates="findings")
    
    def __repr__(self):
        return f"<Finding(id={self.id}, type='{self.finding_type}', source='{self.source}')>"


class InvestigationCase(Base):
    """
    Modelo para casos/investigações que agrupam múltiplas entidades e findings.
    """
    __tablename__ = "investigation_cases"
    
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    closed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Dados do caso
    case_number = Column(String(50), unique=True, nullable=False, index=True)  # Número do caso
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Classificação
    priority = Column(String(20), default="MEDIUM")  # LOW, MEDIUM, HIGH, CRITICAL
    category = Column(String(50), nullable=True)  # CORRUPCAO, FRAUDE, LAVAGEM_DINHEIRO, etc.
    status = Column(String(50), default="OPEN")  # OPEN, IN_PROGRESS, CLOSED, ARCHIVED
    
    # Operador responsável
    lead_operator_id = Column(String(100), nullable=False)
    lead_operator_name = Column(String(255), nullable=True)
    
    # Entidades e findings relacionados (via tabela de associação)
    related_entities = Column(JSON, nullable=True)  # IDs das entidades relacionadas
    summary = Column(JSON, nullable=True)  # Resumo automático gerado pelo sistema
    
    def __repr__(self):
        return f"<InvestigationCase(id={self.id}, number='{self.case_number}', title='{self.title}')>"
