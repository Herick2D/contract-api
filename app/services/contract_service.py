
import os
import sys
import uuid
import shutil
import zipfile
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from core.excel_reader import ExcelReader
from core.document_generator import DocumentGenerator
from core.validators import VerificadorPendencias
from ..config import get_settings
from .template_service import get_template_service


class ContractProcessingService:

    def __init__(self):
        self.settings = get_settings()
        self.temp_dir = self.settings.temp_dir
        self.outputs_dir = self.settings.outputs_dir
        self.prints_dir = self.settings.prints_dir
        self.template_service = get_template_service()

        self.jobs: Dict[str, Dict[str, Any]] = {}
    
    async def list_contracts(self, excel_path: Path) -> Dict[str, Any]:

        try:
            reader = ExcelReader(str(excel_path))
            contratos = reader.listar_contratos()
            
            return {
                "sucesso": True,
                "total": len(contratos),
                "contratos": contratos,
                "mensagem": ""
            }
        except Exception as e:
            return {
                "sucesso": False,
                "total": 0,
                "contratos": [],
                "mensagem": f"Erro ao listar contratos: {str(e)}"
            }
    
    async def verify_pendencias(
        self,
        excel_path: Path,
        prints_dir: Optional[Path] = None
    ) -> Dict[str, Any]:

        try:
            import pandas as pd

            if prints_dir is None:
                prints_dir = self.prints_dir
            
            verificador = VerificadorPendencias(str(prints_dir) if prints_dir and prints_dir.exists() else None)
            
            xlsx = pd.ExcelFile(excel_path)
            df_contatos = None
            
            try:
                for sheet in xlsx.sheet_names:
                    if 'contato' in sheet.lower() or 'base' in sheet.lower():
                        df_contatos = pd.read_excel(xlsx, sheet_name=sheet, dtype=str)
                        df_contatos.columns = [str(c).strip().lower() for c in df_contatos.columns]
                        break
            finally:
                xlsx.close()
            
            if df_contatos is None or 'contrato' not in df_contatos.columns:
                return {
                    "sucesso": False,
                    "mensagem": "Planilha sem aba de contatos válida"
                }
            
            todas_pendencias = []
            contratos_pendentes = 0
            
            for _, row in df_contatos.iterrows():
                numero = str(row.get('contrato', ''))
                if not numero or numero == 'nan':
                    continue
                
                pendencias = verificador.verificar_contrato(row, numero)
                if pendencias:
                    contratos_pendentes += 1
                    for p in pendencias:
                        todas_pendencias.append({
                            "contrato": p.get("contrato", numero),
                            "campo": p.get("campo", ""),
                            "descricao": p.get("descricao", ""),
                            "observacao": p.get("observacao", "")
                        })
            
            total_contratos = len(df_contatos)
            
            return {
                "sucesso": True,
                "total_contratos": total_contratos,
                "contratos_completos": total_contratos - contratos_pendentes,
                "contratos_pendentes": contratos_pendentes,
                "pendencias": todas_pendencias,
                "mensagem": ""
            }
        
        except Exception as e:
            return {
                "sucesso": False,
                "total_contratos": 0,
                "contratos_completos": 0,
                "contratos_pendentes": 0,
                "pendencias": [],
                "mensagem": f"Erro ao verificar pendências: {str(e)}"
            }
    
    async def process_contracts(
        self,
        excel_path: Path,
        template_id: str,
        contract_numbers: Optional[List[str]] = None,
        prints_dir: Optional[Path] = None
    ) -> Dict[str, Any]:

        if prints_dir is None:
            prints_dir = self.prints_dir
        
        template = await self.template_service.get_template(template_id)
        if not template:
            return {
                "sucesso": False,
                "mensagem": f"Template {template_id} não encontrado"
            }
        
        template_path = Path(template["file_path"])
        if not template_path.exists():
            return {
                "sucesso": False,
                "mensagem": f"Arquivo do template não encontrado"
            }
        
        job_id = str(uuid.uuid4())[:12]
        job_output_dir = self.outputs_dir / job_id
        job_output_dir.mkdir(parents=True, exist_ok=True)
        job = {
            "job_id": job_id,
            "status": "processing",
            "total_contratos": 0,
            "processados": 0,
            "sucessos": 0,
            "falhas": 0,
            "resultados": [],
            "download_url": None,
            "created_at": datetime.now().isoformat(),
            "completed_at": None,
            "mensagem": ""
        }
        
        self.jobs[job_id] = job
        
        try:
            reader = ExcelReader(str(excel_path))

            if contract_numbers:
                contratos = contract_numbers
            else:
                contratos = reader.listar_contratos()
            
            job["total_contratos"] = len(contratos)
            
            generator = DocumentGenerator(
                str(template_path),
                str(prints_dir) if prints_dir and prints_dir.exists() else None
            )
            
            resultados = []
            
            for numero in contratos:
                resultado = {
                    "contrato": numero,
                    "sucesso": False,
                    "arquivo": None,
                    "mensagem": "",
                    "dados": {}
                }
                
                try:
                    contrato = reader.obter_contrato(numero)
                    
                    if not contrato:
                        resultado["mensagem"] = "Contrato não encontrado"
                    else:
                        resultado["dados"] = {
                            "inquilinos": len(contrato.inquilinos),
                            "proprietarios": len(contrato.proprietarios),
                            "valor_causa": contrato.valor_causa,
                            "cidade": contrato.cidade
                        }
                        
                        output_filename = f"INICIAL_ARBITRAL_{numero}.docx"
                        output_path = job_output_dir / output_filename
                        
                        sucesso, msg = generator.gerar(contrato, str(output_path))
                        
                        resultado["sucesso"] = sucesso
                        resultado["mensagem"] = msg
                        if sucesso:
                            resultado["arquivo"] = output_filename
                            job["sucessos"] += 1
                        else:
                            job["falhas"] += 1
                
                except Exception as e:
                    resultado["mensagem"] = f"Erro: {str(e)}"
                    job["falhas"] += 1
                
                resultados.append(resultado)
                job["processados"] += 1
                job["resultados"] = resultados
            
            zip_filename = f"contratos_{job_id}.zip"
            zip_path = job_output_dir / zip_filename
            
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file in job_output_dir.glob("*.docx"):
                    zipf.write(file, file.name)
            
            job["status"] = "completed"
            job["download_url"] = f"/api/v1/contracts/download/{job_id}"
            job["completed_at"] = datetime.now().isoformat()
            job["mensagem"] = f"Processamento concluído: {job['sucessos']} sucessos, {job['falhas']} falhas"
            
            return job
        
        except Exception as e:
            job["status"] = "failed"
            job["mensagem"] = f"Erro no processamento: {str(e)}"
            job["completed_at"] = datetime.now().isoformat()
            return job
    
    async def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        return self.jobs.get(job_id)
    
    def get_download_path(self, job_id: str) -> Optional[Path]:
        job_output_dir = self.outputs_dir / job_id
        zip_path = job_output_dir / f"contratos_{job_id}.zip"
        
        if zip_path.exists():
            return zip_path
        
        return None
    
    async def cleanup_job(self, job_id: str) -> bool:
        try:
            job_output_dir = self.outputs_dir / job_id
            if job_output_dir.exists():
                shutil.rmtree(job_output_dir)
            
            if job_id in self.jobs:
                del self.jobs[job_id]
            
            return True
        except:
            return False


_contract_service: Optional[ContractProcessingService] = None


def get_contract_service() -> ContractProcessingService:
    global _contract_service
    if _contract_service is None:
        _contract_service = ContractProcessingService()
    return _contract_service
