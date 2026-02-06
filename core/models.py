from dataclasses import dataclass, field
from typing import List

@dataclass
class Inquilino:
    nome: str = ""
    cpf: str = ""
    telefone: str = ""
    email: str = ""
    nacionalidade: str = "brasileiro(a)"

@dataclass
class Proprietario:
    nome: str = ""
    cpf: str = ""
    rg: str = ""
    telefone: str = ""
    email: str = ""
    endereco: str = ""

@dataclass
class Imovel:
    endereco: str = ""
    complemento: str = ""
    bairro: str = ""
    cidade: str = ""
    cep: str = ""

    @property
    def endereco_completo(self) -> str:
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
    numero: str = ""
    inquilinos: List[Inquilino] = field(default_factory=list)
    proprietarios: List[Proprietario] = field(default_factory=list)
    imovel: Imovel = field(default_factory=Imovel)
    cidade: str = "São Paulo"
    valor_aluguel: float = 0.0
    valor_condominio: float = 0.0
    valor_iptu: float = 0.0
    valor_seguro: float = 0.0
    valor_historico: float = 0.0
    valor_atualizado: float = 0.0

    @property
    def valor_mensal(self) -> float:
        return (
            self.valor_aluguel
            + self.valor_condominio
            + self.valor_iptu
            + self.valor_seguro
        )

    @property
    def valor_causa(self) -> float:
        return self.valor_mensal * 12
