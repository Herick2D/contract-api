import logging
from typing import Dict, List, Optional, Any
from .processors import ProcessadorIniciais, ProcessadorLote
from .config import get_config, save_config, update_config

logger = logging.getLogger(__name__)

class ProcessingService:

    @staticmethod
    def processar_contrato_unico(
        excel_path: str,
        template_path: str,
        numero_contrato: str,
        output_dir: str = "output",
        prints_dir: Optional[str] = None,
    ) -> Dict[str, Any]:

        try:
            processador = ProcessadorIniciais(
                excel_path=excel_path,
                template_path=template_path,
                output_dir=output_dir,
                prints_dir=prints_dir,
            )

            resultado = processador.processar_contrato(numero_contrato)
            return resultado

        except Exception as e:

            logger.error(f"Erro ao processar contrato {numero_contrato}: {e}")

            return {
                "sucesso": False,
                "contrato": numero_contrato,
                "arquivo": None,
                "mensagem": f"Erro: {str(e)}",
                "dados": {},
            }

    @staticmethod
    def processar_lista_contratos(
        excel_path: str,
        template_path: str,
        numeros_contratos: List[str],
        output_dir: str = "output",
        prints_dir: Optional[str] = None,
    ) -> Dict[str, Any]:

        try:
            processador = ProcessadorIniciais(
                excel_path=excel_path,
                template_path=template_path,
                output_dir=output_dir,
                prints_dir=prints_dir,
            )

            resultados = processador.processar_lista(numeros_contratos)
            sucessos = sum(1 for r in resultados if r["sucesso"])
            falhas = len(resultados) - sucessos

            return {
                "sucesso": falhas == 0,
                "total": len(resultados),
                "sucessos": sucessos,
                "falhas": falhas,
                "resultados": resultados,
            }

        except Exception as e:
            logger.error(f"Erro ao processar lista de contratos: {e}")

            return {
                "sucesso": False,
                "total": len(numeros_contratos),
                "sucessos": 0,
                "falhas": len(numeros_contratos),
                "resultados": [],
                "mensagem": f"Erro: {str(e)}",
            }

    @staticmethod
    def processar_todos_contratos(
        excel_path: str,
        template_path: str,
        output_dir: str = "output",
        prints_dir: Optional[str] = None,
        max_workers: int = 4,
    ) -> Dict[str, Any]:

        try:

            processador = ProcessadorIniciais(
                excel_path=excel_path,
                template_path=template_path,
                output_dir=output_dir,
                prints_dir=prints_dir,
            )

            resultados = processador.processar_todos(max_workers=max_workers)
            sucessos = sum(1 for r in resultados if r["sucesso"])
            falhas = len(resultados) - sucessos

            return {
                "sucesso": falhas == 0,
                "total": len(resultados),
                "sucessos": sucessos,
                "falhas": falhas,
                "resultados": resultados,
            }

        except Exception as e:
            logger.error(f"Erro ao processar todos os contratos: {e}")

            return {
                "sucesso": False,
                "total": 0,
                "sucessos": 0,
                "falhas": 0,
                "resultados": [],
                "mensagem": f"Erro: {str(e)}",
            }

    @staticmethod
    def processar_lote(
        excel_dir: str,
        template_path: str,
        output_dir: str = "output",
        prints_dir: Optional[str] = None,
        pendencias_dir: str = "pendencias",
    ) -> Dict[str, Any]:

        try:

            processador = ProcessadorLote(
                excel_dir=excel_dir,
                template_path=template_path,
                output_dir=output_dir,
                prints_dir=prints_dir,
                pendencias_dir=pendencias_dir,
            )

            stats = processador.processar_todos()
            stats["sucesso"] = True
            return stats

        except Exception as e:
            logger.error(f"Erro ao processar lote: {e}")
            return {
                "sucesso": False,
                "arquivos_processados": 0,
                "contratos_total": 0,
                "contratos_completos": 0,
                "contratos_pendentes": 0,
                "documentos_gerados": 0,
                "mensagem": f"Erro: {str(e)}",
            }

    @staticmethod
    def listar_contratos(excel_path: str) -> Dict[str, Any]:

        try:
            from .excel_reader import ExcelReader
            reader = ExcelReader(excel_path)
            contratos = reader.listar_contratos()
            return {"sucesso": True, "total": len(contratos), "contratos": contratos}

        except Exception as e:

            logger.error(f"Erro ao listar contratos: {e}")

            return {
                "sucesso": False,
                "total": 0,
                "contratos": [],
                "mensagem": f"Erro: {str(e)}",
            }

    @staticmethod
    def obter_configuracao() -> Dict[str, Any]:

        try:
            return get_config()

        except Exception as e:
            logger.error(f"Erro ao obter configuração: {e}")
            return {}

    @staticmethod
    def salvar_configuracao(config: Dict[str, Any]) -> Dict[str, Any]:
        try:
            sucesso = save_config(config)
            return {
                "sucesso": sucesso,
                "mensagem": (
                    "Configuração salva com sucesso"
                    if sucesso
                    else "Erro ao salvar configuração"
                ),
            }

        except Exception as e:
            logger.error(f"Erro ao salvar configuração: {e}")
            return {"sucesso": False, "mensagem": f"Erro: {str(e)}"}

    @staticmethod
    def atualizar_configuracao(updates: Dict[str, Any]) -> Dict[str, Any]:
        try:
            sucesso = update_config(updates)
            return {
                "sucesso": sucesso,
                "mensagem": (
                    "Configuração atualizada com sucesso"
                    if sucesso
                    else "Erro ao atualizar configuração"
                ),
            }

        except Exception as e:
            logger.error(f"Erro ao atualizar configuração: {e}")
            return {"sucesso": False, "mensagem": f"Erro: {str(e)}"}

    @staticmethod
    def verificar_pendencias(
        excel_path: str, prints_dir: Optional[str] = None
    ) -> Dict[str, Any]:

        try:
            import pandas as pd
            from .validators import VerificadorPendencias
            verificador = VerificadorPendencias(prints_dir)
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
                return {
                    "sucesso": False,
                    "mensagem": "Planilha sem aba de contatos válida",
                }

            todas_pendencias = []
            contratos_pendentes = 0

            for _, row in df_contatos.iterrows():
                numero = str(row.get("contrato", ""))
                if not numero or numero == "nan":
                    continue

                pendencias = verificador.verificar_contrato(row, numero)
                if pendencias:
                    contratos_pendentes += 1
                    todas_pendencias.extend(pendencias)

            total_contratos = len(df_contatos)
            contratos_completos = total_contratos - contratos_pendentes

            return {
                "sucesso": True,
                "total_contratos": total_contratos,
                "contratos_completos": contratos_completos,
                "contratos_pendentes": contratos_pendentes,
                "pendencias": todas_pendencias,
            }

        except Exception as e:
            logger.error(f"Erro ao verificar pendências: {e}")

            return {
                "sucesso": False,
                "total_contratos": 0,
                "contratos_completos": 0,
                "contratos_pendentes": 0,
                "pendencias": [],
                "mensagem": f"Erro: {str(e)}",
            }
