from pathlib import Path
from typing import List, Dict

import pandas as pd

class VerificadorPendencias:
    CAMPOS_OBRIGATORIOS = {
        "nome inqs": "Nome do Inquilino",
        "cpf_iqs": "CPF do Inquilino",
        "nome pps": "Nome do Locador",
        "cpf_pps": "CPF do Locador",
        "rg_pps": "RG do Locador",
        "endereco_pps": "Endereço do Locador",
        "valor_historico": "Valor Histórico do Débito",
        "valor_atualizado": "Valor Atualizado do Débito",
    }

    def __init__(self, prints_dir: str = None):
        self.prints_dir = Path(prints_dir) if prints_dir else None

    def verificar_contrato(self, row: pd.Series, numero_contrato: str) -> List[Dict]:
        pendencias = []
        for campo, descricao in self.CAMPOS_OBRIGATORIOS.items():
            valor = row.get(campo, "")
            if pd.isna(valor) or str(valor).strip() == "":
                pendencias.append(
                    {
                        "contrato": numero_contrato,
                        "campo": campo,
                        "descricao": descricao,
                        "observacao": f"{descricao} não preenchido",
                    }
                )
        if self.prints_dir and self.prints_dir.exists():
            imagem_encontrada = False
            for ext in [".png", ".jpg", ".jpeg", ".PNG", ".JPG", ".JPEG"]:
                if (self.prints_dir / f"{numero_contrato}{ext}").exists():
                    imagem_encontrada = True
                    break

            if not imagem_encontrada:
                pendencias.append(
                    {
                        "contrato": numero_contrato,
                        "campo": "imagem_clausula",
                        "descricao": "Imagem da Cláusula",
                        "observacao": f"Arquivo prints/{numero_contrato}.png/jpg não encontrado",
                    }
                )
        return pendencias
