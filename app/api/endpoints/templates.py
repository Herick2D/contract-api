from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from fastapi.responses import FileResponse
from ...models.schemas import (
    TemplateResponse,
    TemplateListResponse,
    TemplateUpdateRequest,
)
from ...services.template_service import get_template_service, TemplateService
from ...config import get_settings

router = APIRouter(prefix="/templates", tags=["Templates"])


def get_service() -> TemplateService:

    return get_template_service()

@router.post(
    "/",
    response_model=TemplateResponse,
    summary="Criar novo template",
    description="Faz upload de um arquivo Word (.docx) para ser usado como template de contrato",
)
async def create_template(
    name: str = Form(..., description="Nome identificador do template"),
    description: Optional[str] = Form(None, description="Descrição do template"),
    file: UploadFile = File(..., description="Arquivo Word (.docx)"),
    service: TemplateService = Depends(get_service),
):

    settings = get_settings()

    if not file.filename.lower().endswith(".docx"):
        raise HTTPException(
            status_code=400, detail="Apenas arquivos .docx são permitidos"
        )

    content = await file.read()

    if len(content) > settings.max_upload_size:
        raise HTTPException(
            status_code=400,
            detail=f"Arquivo muito grande. Máximo: {settings.max_upload_size // (1024*1024)}MB",
        )

    template = await service.create_template(
        name=name,
        file_content=content,
        original_filename=file.filename,
        description=description,
    )

    return TemplateResponse(**template)


@router.get(
    "/",
    response_model=TemplateListResponse,
    summary="Listar templates",
    description="Lista todos os templates cadastrados",
)
async def list_templates(
    status: Optional[str] = None, service: TemplateService = Depends(get_service)
):

    templates = await service.list_templates(status=status)

    return TemplateListResponse(
        total=len(templates), templates=[TemplateResponse(**t) for t in templates]
    )


@router.get(
    "/{template_id}",
    response_model=TemplateResponse,
    summary="Obter template",
    description="Obtém detalhes de um template específico",
)
async def get_template(
    template_id: str, service: TemplateService = Depends(get_service)
):

    template = await service.get_template(template_id)

    if not template:

        raise HTTPException(status_code=404, detail="Template não encontrado")

    return TemplateResponse(**template)


@router.put(
    "/{template_id}",
    response_model=TemplateResponse,
    summary="Atualizar template",
    description="Atualiza informações de um template",
)
async def update_template(
    template_id: str,
    update_data: TemplateUpdateRequest,
    service: TemplateService = Depends(get_service),
):

    template = await service.update_template(
        template_id=template_id,
        name=update_data.name,
        description=update_data.description,
        status=update_data.status.value if update_data.status else None,
    )

    if not template:

        raise HTTPException(status_code=404, detail="Template não encontrado")

    return TemplateResponse(**template)


@router.delete(
    "/{template_id}",
    summary="Deletar template",
    description="Remove um template do sistema",
)
async def delete_template(
    template_id: str, service: TemplateService = Depends(get_service)
):

    success = await service.delete_template(template_id)
    if not success:
        raise HTTPException(status_code=404, detail="Template não encontrado")

    return {"message": "Template deletado com sucesso"}


@router.get(
    "/{template_id}/download",
    summary="Download do template",
    description="Faz download do arquivo Word do template",
)
async def download_template(
    template_id: str, service: TemplateService = Depends(get_service)
):

    template = await service.get_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template não encontrado")

    file_path = service.get_template_path(template_id)

    if not file_path:
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")
    return FileResponse(
        path=str(file_path),
        filename=template["filename"],
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )
