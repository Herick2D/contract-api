import logging
from pathlib import Path
from typing import List, Optional

import pandas as pd

from .models import Contrato, Inquilino, Proprietario, Imovel
from .utils import formatar_cpf, formatar_telefone, limpar_texto, separar_valores

logger = logging.getLogger(__name__)


class ExcelReader:

    def __init__(self, filepath: str):

        self.filepath = Path(filepath)
        self.df_endereco: pd.DataFrame = None
        self.df_contatos: pd.DataFrame = None
        self._carregar()

    def _carregar(self):
        logger.info(f"Carregando planilha: {self.filepath}")

        xlsx = pd.ExcelFile(self.filepath)

        try:
            for sheet in xlsx.sheet_names:
                df = pd.read_excel(xlsx, sheet_name=sheet, dtype=str)
                df.columns = [str(c).strip().lower() for c in df.columns]

                if 'endere' in sheet.lower():
                    self.df_endereco = df
                    logger.info(f"  Aba '{sheet}': {len(df)} linhas")
                elif 'contato' in sheet.lower() or 'base' in sheet.lower():
                    self.df_contatos = df
                    logger.info(f"  Aba '{sheet}': {len(df)} linhas")
        finally:
            xlsx.close()

        if self.df_endereco is not None and 'contract' in self.df_endereco.columns:
            self.df_endereco['contract'] = self.df_endereco['contract'].astype(str)
            self.df_endereco.set_index('contract', inplace=True, drop=False)

        if self.df_contatos is not None and 'contrato' in self.df_contatos.columns:
            self.df_contatos['contrato'] = self.df_contatos['contrato'].astype(str)
            self.df_contatos.set_index('contrato', inplace=True, drop=False)

    def listar_contratos(self) -> List[str]:

        if self.df_contatos is None:
            return []
        return self.df_contatos['contrato'].unique().tolist()

    def obter_contrato(self, numero: str) -> Optional[Contrato]:

        numero = str(numero)

        if self.df_contatos is None or numero not in self.df_contatos.index:
            logger.warning(f"Contrato {numero} não encontrado em Base Contatos")
            return None

        row_contatos = self.df_contatos.loc[numero]
        if isinstance(row_contatos, pd.DataFrame):
            row_contatos = row_contatos.iloc[0]

        row_endereco = None
        if self.df_endereco is not None and numero in self.df_endereco.index:
            row_endereco = self.df_endereco.loc[numero]
            if isinstance(row_endereco, pd.DataFrame):
                row_endereco = row_endereco.iloc[0]

        contrato = Contrato(numero=numero)

        nomes_inqs = separar_valores(limpar_texto(row_contatos.get('nome inqs', '')))
        emails_inqs = separar_valores(limpar_texto(row_contatos.get('email inqs', '')))
        tels_inqs = separar_valores(limpar_texto(row_contatos.get('tel inqs', '')))
        cpfs_inqs = separar_valores(limpar_texto(row_contatos.get('cpf_iqs', '')))

        nacionalidade_padrao = "brasileiro(a)"

        for i, nome in enumerate(nomes_inqs):
            inq = Inquilino(
                nome=nome,
                cpf=formatar_cpf(cpfs_inqs[i] if i < len(cpfs_inqs) else ""),
                telefone=formatar_telefone(tels_inqs[i] if i < len(tels_inqs) else (tels_inqs[0] if tels_inqs else "")),
                email=emails_inqs[i] if i < len(emails_inqs) else (emails_inqs[0] if emails_inqs else ""),
                nacionalidade=nacionalidade_padrao
            )
            contrato.inquilinos.append(inq)

        nomes_pps = separar_valores(limpar_texto(row_contatos.get('nome pps', '')))
        emails_pps = separar_valores(limpar_texto(row_contatos.get('email pps', '')))
        tels_pps = separar_valores(limpar_texto(row_contatos.get('tel pp', '')))
        cpfs_pps = separar_valores(limpar_texto(row_contatos.get('cpf_pps', '')))
        rgs_pps = separar_valores(limpar_texto(row_contatos.get('rg_pps', '')))
        enderecos_pps = separar_valores(limpar_texto(row_contatos.get('endereco_pps', '')))

        for i, nome in enumerate(nomes_pps):
            prop = Proprietario(
                nome=nome,
                cpf=formatar_cpf(cpfs_pps[i] if i < len(cpfs_pps) else (cpfs_pps[0] if cpfs_pps else "")),
                rg=rgs_pps[i] if i < len(rgs_pps) else (rgs_pps[0] if rgs_pps else ""),
                email=emails_pps[i] if i < len(emails_pps) else (emails_pps[0] if emails_pps else ""),
                telefone=formatar_telefone(tels_pps[i] if i < len(tels_pps) else (tels_pps[0] if tels_pps else "")),
                endereco=enderecos_pps[i] if i < len(enderecos_pps) else (enderecos_pps[0] if enderecos_pps else "")
            )
            contrato.proprietarios.append(prop)

        if row_endereco is not None:
            contrato.imovel = Imovel(
                endereco=limpar_texto(row_endereco.get('house_address', '')),
                complemento=limpar_texto(row_endereco.get('house_complement', '')),
                bairro=limpar_texto(row_endereco.get('house_neighborhood', '')),
                cidade=limpar_texto(row_endereco.get('house_city', '')),
                cep=limpar_texto(row_endereco.get('house_zipcode', ''))
            )

        contrato.cidade = limpar_texto(row_contatos.get('cidade', '')) or "São Paulo"

        def safe_float(val):
            try:
                if pd.isna(val) or val is None or val == '':
                    return 0.0
                return float(val)
            except:
                return 0.0

        contrato.valor_aluguel = safe_float(row_contatos.get('valor_aluguel', 0))
        contrato.valor_condominio = safe_float(row_contatos.get('valor_condominio', 0))
        contrato.valor_iptu = safe_float(row_contatos.get('valor_iptu', 0))
        contrato.valor_seguro = safe_float(row_contatos.get('valor_seguro_incendio', 0))
        contrato.valor_historico = safe_float(row_contatos.get('valor_historico', 0))
        contrato.valor_atualizado = safe_float(row_contatos.get('valor_atualizado', 0))

        return contrato
