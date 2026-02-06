
import shutil
from typing import Optional, List
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, BackgroundTasks
from fastapi.responses import FileResponse

from ...models.schemas import (
    ProcessingRequest,
    ProcessingResponse,
    ContractListResponse,
    PendenciasResponse,
    ContractResult
)
from ...services.contract_service import get_contract_service, ContractProcessingService
from ...config import get_settings

router = APIRouter(prefix="/contracts", tags=["Contracts"])


def get_service() -> ContractProcessingService:
    return get_contract_service()


async def save_upload_file(upload_file: UploadFile, destination: Path) -> Path:
    content = await upload_file.read()
    destination.parent.mkdir(parents=True, exist_ok=True)
    with open(destination, "wb") as f:
        f.write(content)
    return destination


@router.post(
    "/list",
    response_model=ContractListResponse,
    summary="Listar contratos do Excel",
    description="Lista todos os contratos disponíveis em um arquivo Excel"
)
async def list_contracts(
    file: UploadFile = File(..., description="Arquivo Excel (.xlsx)"),
    service: ContractProcessingService = Depends(get_service)
):

    settings = get_settings()
    
    if not file.filename.lower().endswith(('.xlsx', '.xls')):
        raise HTTPException(
            status_code=400,
            detail="Apenas arquivos Excel (.xlsx, .xls) são permitidos"
        )
    
    import uuid
    import gc
    temp_path = settings.temp_dir / f"{uuid.uuid4()}_{file.filename}"
    await save_upload_file(file, temp_path)
    
    try:
        result = await service.list_contracts(temp_path)
        return ContractListResponse(**result)
    finally:
        gc.collect()
        try:
            if temp_path.exists():
                temp_path.unlink()
        except PermissionError:
            pass


@router.post(
    "/pendencias",
    response_model=PendenciasResponse,
    summary="Verificar pendências",
    description="Verifica pendências nos contratos sem gerar documentos"
)
async def verify_pendencias(
    file: UploadFile = File(..., description="Arquivo Excel (.xlsx)"),
    service: ContractProcessingService = Depends(get_service)
):

    settings = get_settings()
    
    if not file.filename.lower().endswith(('.xlsx', '.xls')):
        raise HTTPException(
            status_code=400,
            detail="Apenas arquivos Excel (.xlsx, .xls) são permitidos"
        )
    
    import uuid
    import gc
    temp_path = settings.temp_dir / f"{uuid.uuid4()}_{file.filename}"
    await save_upload_file(file, temp_path)
    
    try:
        result = await service.verify_pendencias(temp_path)
        return PendenciasResponse(**result)
    finally:
        gc.collect()
        try:
            if temp_path.exists():
                temp_path.unlink()
        except PermissionError:
            pass


@router.post(
    "/process",
    response_model=ProcessingResponse,
    summary="Processar contratos",
    description="Processa contratos e gera documentos Word preenchidos"
)
async def process_contracts(
    template_id: str = Form(..., description="ID do template a usar"),
    file: UploadFile = File(..., description="Arquivo Excel com os contratos"),
    contratos: Optional[str] = Form(None, description="Lista de contratos separados por vírgula (vazio = todos)"),
    service: ContractProcessingService = Depends(get_service)
):

    settings = get_settings()
    
    if not file.filename.lower().endswith(('.xlsx', '.xls')):
        raise HTTPException(
            status_code=400,
            detail="Apenas arquivos Excel (.xlsx, .xls) são permitidos"
        )
    
    import uuid
    import gc
    temp_path = settings.temp_dir / f"{uuid.uuid4()}_{file.filename}"
    await save_upload_file(file, temp_path)
    
    try:
        contract_list = None
        if contratos and contratos.strip():
            contract_list = [c.strip() for c in contratos.split(",") if c.strip()]
        
        result = await service.process_contracts(
            excel_path=temp_path,
            template_id=template_id,
            contract_numbers=contract_list
        )
        
        if result.get("sucesso") == False:
            raise HTTPException(
                status_code=400,
                detail=result.get("mensagem", "Erro ao processar contratos")
            )
        
        return ProcessingResponse(
            job_id=result["job_id"],
            status=result["status"],
            total_contratos=result["total_contratos"],
            processados=result["processados"],
            sucessos=result["sucessos"],
            falhas=result["falhas"],
            resultados=[ContractResult(**r) for r in result["resultados"]],
            download_url=result.get("download_url"),
            mensagem=result.get("mensagem", "")
        )
    
    finally:
        gc.collect()
        try:
            if temp_path.exists():
                temp_path.unlink()
        except PermissionError:
            pass


@router.get(
    "/job/{job_id}",
    response_model=ProcessingResponse,
    summary="Status do processamento",
    description="Obtém o status de um job de processamento"
)
async def get_job_status(
    job_id: str,
    service: ContractProcessingService = Depends(get_service)
):
    job = await service.get_job(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail="Job não encontrado")
    
    return ProcessingResponse(
        job_id=job["job_id"],
        status=job["status"],
        total_contratos=job["total_contratos"],
        processados=job["processados"],
        sucessos=job["sucessos"],
        falhas=job["falhas"],
        resultados=[ContractResult(**r) for r in job["resultados"]],
        download_url=job.get("download_url"),
        mensagem=job.get("mensagem", "")
    )


@router.get(
    "/download/{job_id}",
    summary="Download dos documentos",
    description="Faz download do ZIP com os documentos gerados"
)
async def download_documents(
    job_id: str,
    service: ContractProcessingService = Depends(get_service)
):

    zip_path = service.get_download_path(job_id)
    
    if not zip_path:
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")
    
    return FileResponse(
        path=str(zip_path),
        filename=f"contratos_{job_id}.zip",
        media_type="application/zip"
    )


@router.delete(
    "/job/{job_id}",
    summary="Limpar job",
    description="Remove os arquivos de um job de processamento"
)
async def cleanup_job(
    job_id: str,
    service: ContractProcessingService = Depends(get_service)
):
    success = await service.cleanup_job(job_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Job não encontrado")
    
    return {"message": "Job limpo com sucesso"}
