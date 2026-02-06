import logging
from pathlib import Path
from typing import List, Dict
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd

from .excel_reader import ExcelReader
from .document_generator import DocumentGenerator
from .validators import VerificadorPendencias

logger = logging.getLogger(__name__)


class ProcessadorIniciais:
    def __init__(
        self,
        excel_path: str,
        template_path: str,
        output_dir: str = "output",
        prints_dir: str = None,
    ):

        self.reader = ExcelReader(excel_path)
        self.generator = DocumentGenerator(template_path, prints_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.prints_dir = Path(prints_dir) if prints_dir else None
        self.resultados = []

    def processar_contrato(self, numero: str) -> Dict:
        resultado = {
            "contrato": numero,
            "sucesso": False,
            "arquivo": None,
            "mensagem": "",
            "dados": {},
        }

        contrato = self.reader.obter_contrato(numero)

        if not contrato:
            resultado["mensagem"] = "Contrato não encontrado"
            return resultado

        resultado["dados"] = {
            "inquilinos": len(contrato.inquilinos),
            "proprietarios": len(contrato.proprietarios),
            "valor_causa": contrato.valor_causa,
            "cidade": contrato.cidade,
        }

        output_path = self.output_dir / f"INICIAL_ARBITRAL_{numero}.docx"
        sucesso, msg = self.generator.gerar(contrato, str(output_path))
        resultado["sucesso"] = sucesso
        resultado["mensagem"] = msg
        if sucesso:
            resultado["arquivo"] = str(output_path)

        return resultado

    def processar_todos(self, max_workers: int = 4) -> List[Dict]:
        contratos = self.reader.listar_contratos()
        total = len(contratos)
        logger.info(f"Processando {total} contratos...")
        self.resultados = []
        processados = 0
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(self.processar_contrato, num): num for num in contratos
            }

            for future in as_completed(futures):
                resultado = future.result()
                self.resultados.append(resultado)
                processados += 1
                if processados % 100 == 0 or processados == total:
                    logger.info(
                        f"  Progresso: {processados}/{total} ({100*processados//total}%)"
                    )

        sucessos = sum(1 for r in self.resultados if r["sucesso"])
        falhas = total - sucessos
        logger.info(f"Concluído: {sucessos} sucessos, {falhas} falhas")
        return self.resultados

    def processar_lista(self, numeros: List[str]) -> List[Dict]:
        self.resultados = []
        for num in numeros:
            resultado = self.processar_contrato(num)
            self.resultados.append(resultado)
            status = "✓" if resultado["sucesso"] else "✗"
            logger.info(f"  [{status}] Contrato {num}: {resultado['mensagem']}")
        return self.resultados


class ProcessadorLote:
    def __init__(
        self,
        excel_dir: str,
        template_path: str,
        output_dir: str = "output",
        prints_dir: str = None,
        pendencias_dir: str = "pendencias",
    ):

        self.excel_dir = Path(excel_dir)
        self.template_path = Path(template_path)
        self.output_dir = Path(output_dir)
        self.prints_dir = Path(prints_dir) if prints_dir else None
        self.pendencias_dir = Path(pendencias_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.pendencias_dir.mkdir(parents=True, exist_ok=True)
        self.verificador = VerificadorPendencias(prints_dir)
        self.todas_pendencias = []
        self.estatisticas = {
            "arquivos_processados": 0,
            "contratos_total": 0,
            "contratos_completos": 0,
            "contratos_pendentes": 0,
            "documentos_gerados": 0,
        }

    def listar_arquivos_excel(self) -> List[Path]:
        arquivos = set()
        for ext in ["*.xlsx", "*.xls"]:
            arquivos.update(self.excel_dir.glob(ext))
        arquivos = [a for a in arquivos if not a.name.startswith("~$")]

        return sorted(arquivos)

    def processar_arquivo(self, excel_path: Path) -> Dict:
        logger.info(f"\nProcessando: {excel_path.name}")
        resultado = {
            "arquivo": excel_path.name,
            "contratos_total": 0,
            "contratos_completos": 0,
            "contratos_pendentes": 0,
            "documentos_gerados": 0,
            "pendencias": [],
        }

        try:
            xlsx = pd.ExcelFile(excel_path)
            df_contatos = None
            for sheet in xlsx.sheet_names:
                if "contato" in sheet.lower() or "base" in sheet.lower():
                    df_contatos = pd.read_excel(xlsx, sheet_name=sheet, dtype=str)
                    df_contatos.columns = [
                        str(c).strip().lower() for c in df_contatos.columns
                    ]
                    break

            if df_contatos is None or "contrato" not in df_contatos.columns:
                logger.warning("Planilha sem aba de contatos válida")
                return resultado

            resultado["contratos_total"] = len(df_contatos)
            processador = ProcessadorIniciais(
                str(excel_path),
                str(self.template_path),
                str(self.output_dir),
                str(self.prints_dir) if self.prints_dir else None,
            )

            for _, row in df_contatos.iterrows():
                numero = str(row.get("contrato", ""))
                if not numero or numero == "nan":
                    continue

                pendencias = self.verificador.verificar_contrato(row, numero)

                if pendencias:
                    resultado["contratos_pendentes"] += 1
                    for p in pendencias:
                        p["arquivo"] = excel_path.name
                        resultado["pendencias"].append(p)
                        self.todas_pendencias.append(p)

                else:
                    resultado["contratos_completos"] += 1

                res = processador.processar_contrato(numero)

                if res["sucesso"]:
                    resultado["documentos_gerados"] += 1

            logger.info(
                f"  ✓ {resultado['documentos_gerados']} documentos gerados, {resultado['contratos_pendentes']} com pendências"
            )

        except Exception as e:
            logger.error(f"  ✗ Erro: {e}")

        return resultado

    def processar_todos(self) -> Dict:
        arquivos = self.listar_arquivos_excel()

        if not arquivos:
            logger.warning(f"Nenhum arquivo Excel encontrado em: {self.excel_dir}")
            return self.estatisticas

        logger.info(f" Encontrados {len(arquivos)} arquivos Excel")

        for arquivo in arquivos:
            resultado = self.processar_arquivo(arquivo)
            self.estatisticas["arquivos_processados"] += 1
            self.estatisticas["contratos_total"] += resultado["contratos_total"]
            self.estatisticas["contratos_completos"] += resultado["contratos_completos"]
            self.estatisticas["contratos_pendentes"] += resultado["contratos_pendentes"]
            self.estatisticas["documentos_gerados"] += resultado["documentos_gerados"]

        if self.todas_pendencias:
            self.gerar_relatorio_pendencias()

        return self.estatisticas

    def gerar_relatorio_pendencias(self):
        if not self.todas_pendencias:
            return

        df = pd.DataFrame(self.todas_pendencias)
        df = df[["arquivo", "contrato", "campo", "descricao", "observacao"]]
        df.columns = ["Arquivo Origem", "Contrato", "Campo", "Descrição", "Observação"]
        df = df.sort_values(["Arquivo Origem", "Contrato", "Campo"])
        data_str = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        output_path = self.pendencias_dir / f"PENDENCIAS_{data_str}.xlsx"

        with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
            df.to_excel(writer, sheet_name="Pendências", index=False)
            resumo = (
                df.groupby("Arquivo Origem")
                .agg({"Contrato": "nunique", "Campo": "count"})
                .reset_index()
            )

            resumo.columns = [
                "Arquivo",
                "Contratos com Pendência",
                "Total de Pendências",
            ]

            resumo.to_excel(writer, sheet_name="Resumo", index=False)
            por_tipo = df.groupby("Descrição").size().reset_index(name="Quantidade")
            por_tipo = por_tipo.sort_values("Quantidade", ascending=False)
            por_tipo.to_excel(writer, sheet_name="Por Tipo", index=False)

        logger.info(f"\n Relatório de pendências gerado: {output_path}")
        logger.info(f"   Total de pendências: {len(self.todas_pendencias)}")
        logger.info(f"   Contratos afetados: {df['Contrato'].nunique()}")
