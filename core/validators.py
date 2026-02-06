#!/usr/bin/env python3
"""
Validadores - Core
Gerador de Iniciais Arbitrais

Classes responsáveis por validar dados e verificar pendências.
"""

from pathlib import Path
from typing import List, Dict

import pandas as pd


class VerificadorPendencias:
    """Verifica campos obrigatórios faltantes em contratos"""

    # Campos obrigatórios e suas descrições
    CAMPOS_OBRIGATORIOS = {
        'nome inqs': 'Nome do Inquilino',
        'cpf_iqs': 'CPF do Inquilino',
        'nome pps': 'Nome do Locador',
        'cpf_pps': 'CPF do Locador',
        'rg_pps': 'RG do Locador',
        'endereco_pps': 'Endereço do Locador',
        'valor_historico': 'Valor Histórico do Débito',
        'valor_atualizado': 'Valor Atualizado do Débito',
    }

    def __init__(self, prints_dir: str = None):
        """
        Inicializa o verificador

        Args:
            prints_dir: Pasta com imagens das cláusulas (opcional)
        """
        self.prints_dir = Path(prints_dir) if prints_dir else None

    def verificar_contrato(self, row: pd.Series, numero_contrato: str) -> List[Dict]:
        """
        Verifica um contrato e retorna lista de pendências.

        Args:
            row: Linha da planilha com dados do contrato
            numero_contrato: Número do contrato

        Returns:
            Lista de dicionários com pendências encontradas.
            Cada pendência tem: contrato, campo, descricao, observacao
        """
        pendencias = []

        # Verifica campos obrigatórios
        for campo, descricao in self.CAMPOS_OBRIGATORIOS.items():
            valor = row.get(campo, '')
            if pd.isna(valor) or str(valor).strip() == '':
                pendencias.append({
                    'contrato': numero_contrato,
                    'campo': campo,
                    'descricao': descricao,
                    'observacao': f'{descricao} não preenchido'
                })

        # Verifica se existe imagem da cláusula
        if self.prints_dir and self.prints_dir.exists():
            imagem_encontrada = False
            for ext in ['.png', '.jpg', '.jpeg', '.PNG', '.JPG', '.JPEG']:
                if (self.prints_dir / f"{numero_contrato}{ext}").exists():
                    imagem_encontrada = True
                    break

            if not imagem_encontrada:
                pendencias.append({
                    'contrato': numero_contrato,
                    'campo': 'imagem_clausula',
                    'descricao': 'Imagem da Cláusula',
                    'observacao': f'Arquivo prints/{numero_contrato}.png/jpg não encontrado'
                })

        return pendencias
