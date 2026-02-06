import os
import zipfile
import tempfile


from typing import List
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import FileResponse
from pydantic import BaseModel
from ...config import get_settings

router = APIRouter(prefix="/prints", tags=["Prints"])


ALLOWED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg"}
ALLOWED_ARCHIVE_EXTENSIONS = {".zip", ".rar"}

class PrintInfo(BaseModel):
    filename: str
    contract_number: str
    size_bytes: int

class PrintListResponse(BaseModel):
    total: int
    prints: List[PrintInfo]

class UploadResponse(BaseModel):
    sucesso: bool
    total_enviados: int
    total_aceitos: int
    total_rejeitados: int
    aceitos: List[str]
    rejeitados: List[dict]
    mensagem: str

class ValidationError(BaseModel):
    filename: str
    reason: str

def get_prints_dir() -> Path:
    settings = get_settings()
    settings.prints_dir.mkdir(parents=True, exist_ok=True)
    return settings.prints_dir

def is_valid_image(filename: str) -> bool:
    ext = Path(filename).suffix.lower()
    return ext in ALLOWED_IMAGE_EXTENSIONS

def is_archive(filename: str) -> bool:
    ext = Path(filename).suffix.lower()
    return ext in ALLOWED_ARCHIVE_EXTENSIONS

def extract_contract_number(filename: str) -> str:
    return Path(filename).stem

def validate_archive_contents(archive_path: Path) -> tuple[List[str], List[dict]]:
    valid_files = []
    invalid_files = []
    ext = archive_path.suffix.lower()
    if ext == ".zip":
        try:
            with zipfile.ZipFile(archive_path, "r") as zf:
                for name in zf.namelist():
                    if name.endswith("/"):
                        continue

                    if name.startswith("__MACOSX") or name.startswith("."):
                        continue

                    basename = os.path.basename(name)
                    if not basename:
                        continue

                    if is_valid_image(basename):
                        valid_files.append(name)
                    else:
                        invalid_files.append(
                            {
                                "filename": basename,
                                "reason": f"Extensão não permitida. Apenas {', '.join(ALLOWED_IMAGE_EXTENSIONS)} são aceitos.",
                            }
                        )
        except zipfile.BadZipFile:
            invalid_files.append(
                {
                    "filename": archive_path.name,
                    "reason": "Arquivo ZIP corrompido ou inválido",
                }
            )
    elif ext == ".rar":
        try:
            import rarfile
            with rarfile.RarFile(archive_path, "r") as rf:
                for name in rf.namelist():
                    if name.endswith("/"):
                        continue

                    if name.startswith("__MACOSX") or name.startswith("."):
                        continue

                    basename = os.path.basename(name)
                    if not basename:
                        continue

                    if is_valid_image(basename):
                        valid_files.append(name)
                    else:
                        invalid_files.append(
                            {
                                "filename": basename,
                                "reason": f"Extensão não permitida. Apenas {', '.join(ALLOWED_IMAGE_EXTENSIONS)} são aceitos.",
                            }
                        )

        except ImportError:
            invalid_files.append(
                {
                    "filename": archive_path.name,
                    "reason": "Suporte a RAR não instalado. Use arquivos ZIP.",
                }
            )

        except Exception as e:
            invalid_files.append(
                {
                    "filename": archive_path.name,
                    "reason": f"Erro ao abrir arquivo RAR: {str(e)}",
                }
            )
    return valid_files, invalid_files


def extract_archive(archive_path: Path, dest_dir: Path) -> List[str]:
    extracted = []
    ext = archive_path.suffix.lower()
    if ext == ".zip":
        with zipfile.ZipFile(archive_path, "r") as zf:
            for name in zf.namelist():
                if name.endswith("/"):
                    continue

                if name.startswith("__MACOSX") or name.startswith("."):
                    continue

                basename = os.path.basename(name)
                if not basename or not is_valid_image(basename):
                    continue

                target_path = dest_dir / basename
                with zf.open(name) as source:
                    with open(target_path, "wb") as target:
                        target.write(source.read())
                extracted.append(basename)

    elif ext == ".rar":
        try:
            import rarfile
            with rarfile.RarFile(archive_path, "r") as rf:
                for name in rf.namelist():
                    if name.endswith("/"):
                        continue

                    if name.startswith("__MACOSX") or name.startswith("."):
                        continue

                    basename = os.path.basename(name)
                    if not basename or not is_valid_image(basename):
                        continue

                    target_path = dest_dir / basename
                    with rf.open(name) as source:
                        with open(target_path, "wb") as target:
                            target.write(source.read())
                    extracted.append(basename)
        except ImportError:
            pass
    return extracted

@router.post(
    "/upload",
    response_model=UploadResponse,
    summary="Upload de prints",
    description="Faz upload de imagens das cláusulas contratuais. Aceita arquivos individuais (.png, .jpg, .jpeg) ou arquivos compactados (.zip, .rar)",
)
async def upload_prints(
    files: List[UploadFile] = File(
        ..., description="Arquivos de imagem ou ZIP/RAR contendo imagens"
    ),
    prints_dir: Path = Depends(get_prints_dir),
):

    aceitos = []
    rejeitados = []

    for file in files:
        filename = file.filename
        ext = Path(filename).suffix.lower()
        if ext in ALLOWED_IMAGE_EXTENSIONS:
            try:
                content = await file.read()
                target_path = prints_dir / filename
                with open(target_path, "wb") as f:
                    f.write(content)
                aceitos.append(filename)
            except Exception as e:
                rejeitados.append(
                    {"filename": filename, "reason": f"Erro ao salvar: {str(e)}"}
                )
        elif ext in ALLOWED_ARCHIVE_EXTENSIONS:
            with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
                content = await file.read()
                tmp.write(content)
                tmp_path = Path(tmp.name)
            try:
                valid_files, invalid_files = validate_archive_contents(tmp_path)
                if invalid_files:
                    rejeitados.append(
                        {
                            "filename": filename,
                            "reason": f"Arquivo contém {len(invalid_files)} arquivo(s) inválido(s): {', '.join([f['filename'] for f in invalid_files[:5]])}{'...' if len(invalid_files) > 5 else ''}",
                        }
                    )
                elif not valid_files:
                    rejeitados.append(
                        {
                            "filename": filename,
                            "reason": "Arquivo compactado está vazio ou não contém imagens válidas",
                        }
                    )
                else:
                    extracted = extract_archive(tmp_path, prints_dir)
                    aceitos.extend(extracted)
            finally:
                try:
                    tmp_path.unlink()
                except:
                    pass
        else:
            rejeitados.append(
                {
                    "filename": filename,
                    "reason": f"Tipo de arquivo não suportado. Aceitos: {', '.join(ALLOWED_IMAGE_EXTENSIONS | ALLOWED_ARCHIVE_EXTENSIONS)}",
                }
            )
    total_enviados = len(files)
    total_aceitos = len(aceitos)
    total_rejeitados = len(rejeitados)
    sucesso = total_rejeitados == 0 and total_aceitos > 0
    if sucesso:
        mensagem = f"{total_aceitos} arquivo(s) enviado(s) com sucesso"
    elif total_aceitos > 0:
        mensagem = f"{total_aceitos} aceito(s), {total_rejeitados} rejeitado(s)"
    else:
        mensagem = "Nenhum arquivo foi aceito"
    return UploadResponse(
        sucesso=sucesso,
        total_enviados=total_enviados,
        total_aceitos=total_aceitos,
        total_rejeitados=total_rejeitados,
        aceitos=aceitos,
        rejeitados=rejeitados,
        mensagem=mensagem,
    )

@router.get(
    "/",
    response_model=PrintListResponse,
    summary="Listar prints",
    description="Lista todos os prints disponíveis",
)
async def list_prints(prints_dir: Path = Depends(get_prints_dir)):

    prints = []

    for ext in ALLOWED_IMAGE_EXTENSIONS:

        for file_path in prints_dir.glob(f"*{ext}"):

            prints.append(
                PrintInfo(
                    filename=file_path.name,
                    contract_number=extract_contract_number(file_path.name),
                    size_bytes=file_path.stat().st_size,
                )
            )

        for file_path in prints_dir.glob(f"*{ext.upper()}"):

            prints.append(
                PrintInfo(
                    filename=file_path.name,
                    contract_number=extract_contract_number(file_path.name),
                    size_bytes=file_path.stat().st_size,
                )
            )

    seen = set()
    unique_prints = []

    for p in prints:
        if p.filename not in seen:
            seen.add(p.filename)
            unique_prints.append(p)
    unique_prints.sort(key=lambda x: x.contract_number)
    return PrintListResponse(total=len(unique_prints), prints=unique_prints)


@router.get(
    "/{contract_number}",
    summary="Obter print",
    description="Obtém a imagem de um contrato específico",
)
async def get_print(contract_number: str, prints_dir: Path = Depends(get_prints_dir)):
    for ext in [".png", ".jpg", ".jpeg", ".PNG", ".JPG", ".JPEG"]:
        file_path = prints_dir / f"{contract_number}{ext}"
        if file_path.exists():
            media_type = "image/png" if ext.lower() == ".png" else "image/jpeg"
            return FileResponse(
                path=str(file_path), filename=file_path.name, media_type=media_type
            )

    raise HTTPException(
        status_code=404, detail=f"Print do contrato {contract_number} não encontrado"
    )

@router.delete(
    "/{contract_number}",
    summary="Deletar print",
    description="Remove a imagem de um contrato",
)
async def delete_print(
    contract_number: str, prints_dir: Path = Depends(get_prints_dir)
):

    deleted = False
    for ext in [".png", ".jpg", ".jpeg", ".PNG", ".JPG", ".JPEG"]:
        file_path = prints_dir / f"{contract_number}{ext}"
        if file_path.exists():
            file_path.unlink()
            deleted = True

    if not deleted:

        raise HTTPException(
            status_code=404,
            detail=f"Print do contrato {contract_number} não encontrado",
        )

    return {"message": f"Print do contrato {contract_number} removido com sucesso"}

@router.delete(
    "/", summary="Limpar todos os prints", description="Remove todos os prints salvos"
)
async def clear_prints(prints_dir: Path = Depends(get_prints_dir)):
    count = 0

    for ext in ALLOWED_IMAGE_EXTENSIONS:
        for file_path in prints_dir.glob(f"*{ext}"):
            file_path.unlink()
            count += 1

        for file_path in prints_dir.glob(f"*{ext.upper()}"):
            file_path.unlink()
            count += 1
    return {"message": f"{count} print(s) removido(s)"}
