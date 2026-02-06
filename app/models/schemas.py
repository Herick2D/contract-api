"""
Schemas Pydantic - Modelos de Request/Response
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


# ==================== ENUMS ====================

class TemplateStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class ProcessingStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


# ==================== TEMPLATE SCHEMAS ====================

class TemplateBase(BaseModel):
    """Base do template"""
    name: str = Field(..., description="Nome identificador do template")
    description: Optional[str] = Field(None, description="Descrição do template")


class TemplateCreate(TemplateBase):
    """Schema para criação de template"""
    pass


class TemplateResponse(TemplateBase):
    """Schema de resposta do template"""
    id: str = Field(..., description="ID único do template")
    filename: str = Field(..., description="Nome do arquivo original")
    file_path: str = Field(..., description="Caminho do arquivo no servidor")
    status: TemplateStatus = Field(default=TemplateStatus.ACTIVE)
    placeholders: List[str] = Field(default_factory=list, description="Placeholders encontrados no documento")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    class Config:
        from_attributes = True


class TemplateListResponse(BaseModel):
    """Lista de templates"""
    total: int
    templates: List[TemplateResponse]


class TemplateUpdateRequest(BaseModel):
    """Schema para atualização de template"""
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TemplateStatus] = None


# ==================== CONTRACT PROCESSING SCHEMAS ====================

class ContractInfo(BaseModel):
    """Informações de um contrato"""
    numero: str
    inquilinos: int = 0
    proprietarios: int = 0
    valor_causa: float = 0.0
    cidade: str = ""


class ContractResult(BaseModel):
    """Resultado do processamento de um contrato"""
    contrato: str
    sucesso: bool
    arquivo: Optional[str] = None
    mensagem: str = ""
    dados: Dict[str, Any] = Field(default_factory=dict)


class ProcessingRequest(BaseModel):
    """Request para processamento de contratos"""
    template_id: str = Field(..., description="ID do template a ser usado")
    contratos: Optional[List[str]] = Field(None, description="Lista de contratos específicos (None = todos)")


class ProcessingResponse(BaseModel):
    """Resposta do processamento"""
    job_id: str = Field(..., description="ID do job de processamento")
    status: ProcessingStatus
    total_contratos: int = 0
    processados: int = 0
    sucessos: int = 0
    falhas: int = 0
    resultados: List[ContractResult] = Field(default_factory=list)
    download_url: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    mensagem: str = ""


class ContractListResponse(BaseModel):
    """Lista de contratos de um Excel"""
    sucesso: bool
    total: int
    contratos: List[str]
    mensagem: str = ""


# ==================== CONFIGURATION SCHEMAS ====================

class ConfigurationBase(BaseModel):
    """Configuração do escritório"""
    advogado_nome: str = "João Thomaz Prazeres Gondim"
    advogado_oab: str = "270.757"
    escritorio_telefone: str = "(21) 2262-7979"
    escritorio_whatsapp: str = "(21) 96975-0156"
    escritorio_email: str = "quintoandar@gondimadv.com.br"
    escritorio_email_intimacoes: str = "camaras.arbitrais@gondimadv.com.br"
    escritorio_endereco: str = "Avenida Paulo de Frontin, 1, Centro Empresarial, Cidade Nova, Rio de Janeiro - RJ, 20260-010"
    nacionalidade_padrao: str = "brasileiro(a)"


class ConfigurationUpdate(BaseModel):
    """Atualização parcial de configuração"""
    advogado_nome: Optional[str] = None
    advogado_oab: Optional[str] = None
    escritorio_telefone: Optional[str] = None
    escritorio_whatsapp: Optional[str] = None
    escritorio_email: Optional[str] = None
    escritorio_email_intimacoes: Optional[str] = None
    escritorio_endereco: Optional[str] = None
    nacionalidade_padrao: Optional[str] = None


class ConfigurationResponse(ConfigurationBase):
    """Resposta da configuração"""
    updated_at: datetime = Field(default_factory=datetime.now)


# ==================== PENDENCIAS SCHEMAS ====================

class Pendencia(BaseModel):
    """Uma pendência encontrada"""
    contrato: str
    campo: str
    descricao: str
    observacao: str = ""


class PendenciasResponse(BaseModel):
    """Resposta de verificação de pendências"""
    sucesso: bool
    total_contratos: int = 0
    contratos_completos: int = 0
    contratos_pendentes: int = 0
    pendencias: List[Pendencia] = Field(default_factory=list)
    mensagem: str = ""


# ==================== GENERAL SCHEMAS ====================

class HealthResponse(BaseModel):
    """Resposta do health check"""
    status: str = "healthy"
    version: str
    timestamp: datetime = Field(default_factory=datetime.now)


class ErrorResponse(BaseModel):
    """Resposta de erro"""
    error: str
    detail: str
    timestamp: datetime = Field(default_factory=datetime.now)
