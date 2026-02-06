#!/usr/bin/env python3
"""
Modelos de Dados - Core
Gerador de Iniciais Arbitrais

Dataclasses que representam as entidades do domínio.
"""

from dataclasses import dataclass, field
from typing import List


@dataclass
class Inquilino:
    """Representa um inquilino/locatário"""
    nome: str = ""
    cpf: str = ""
    telefone: str = ""
    email: str = ""
    nacionalidade: str = "brasileiro(a)"


@dataclass
class Proprietario:
    """Representa um proprietário/locador"""
    nome: str = ""
    cpf: str = ""  # Coluna cpf_pps
    rg: str = ""   # Coluna rg_pps
    telefone: str = ""
    email: str = ""
    endereco: str = ""  # Coluna endereco_pps


@dataclass
class Imovel:
    """Representa um imóvel"""
    endereco: str = ""
    complemento: str = ""
    bairro: str = ""
    cidade: str = ""
    cep: str = ""

    @property
    def endereco_completo(self) -> str:
        """Retorna endereço completo formatado"""
        partes = []
        if self.endereco:
            partes.append(self.endereco)
        if self.complemento:
            partes.append(self.complemento)
        if self.bairro:
            partes.append(self.bairro)
        if self.cidade:
            partes.append(self.cidade)
        if self.cep:
            partes.append(f"CEP {self.cep}")
        return ", ".join(partes) if partes else ""


@dataclass
class Contrato:
    """Representa um contrato de locação"""
    numero: str = ""
    inquilinos: List[Inquilino] = field(default_factory=list)
    proprietarios: List[Proprietario] = field(default_factory=list)
    imovel: Imovel = field(default_factory=Imovel)
    cidade: str = "São Paulo"
    valor_aluguel: float = 0.0
    valor_condominio: float = 0.0
    valor_iptu: float = 0.0
    valor_seguro: float = 0.0
    valor_historico: float = 0.0   # Valor do débito sem juros (coluna valor_historico)
    valor_atualizado: float = 0.0  # Valor do débito com juros (coluna valor_atualizado)

    @property
    def valor_mensal(self) -> float:
        """Retorna valor mensal total (aluguel + encargos)"""
        return self.valor_aluguel + self.valor_condominio + self.valor_iptu + self.valor_seguro

    @property
    def valor_causa(self) -> float:
        """Retorna valor da causa (valor mensal * 12)"""
        return self.valor_mensal * 12
