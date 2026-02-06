
from pathlib import Path
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    app_name: str = "Contract Generator API"
    app_version: str = "1.0.0"
    debug: bool = False
    base_dir: Path = Path(__file__).resolve().parent.parent
    storage_dir: Path = base_dir / "storage"
    templates_dir: Path = storage_dir / "templates"
    temp_dir: Path = storage_dir / "temp"
    outputs_dir: Path = storage_dir / "outputs"
    prints_dir: Path = storage_dir / "prints"
    max_upload_size: int = 50 * 1024 * 1024
    allowed_excel_extensions: set = {".xlsx", ".xls"}
    allowed_template_extensions: set = {".docx"}
    max_workers: int = 4
    advogado_nome: str = "João Thomaz Prazeres Gondim"
    advogado_oab: str = "270.757"
    escritorio_telefone: str = "(21) 2262-7979"
    escritorio_whatsapp: str = "(21) 96975-0156"
    escritorio_email: str = "quintoandar@gondimadv.com.br"
    escritorio_email_intimacoes: str = "camaras.arbitrais@gondimadv.com.br"
    escritorio_endereco: str = (
        "Avenida Paulo de Frontin, 1, Centro Empresarial, Cidade Nova, Rio de Janeiro - RJ, 20260-010"
    )
    nacionalidade_padrao: str = "brasileiro(a)"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
    def setup_directories(self):
        for dir_path in [
            self.storage_dir,
            self.templates_dir,
            self.temp_dir,
            self.outputs_dir,
            self.prints_dir,
        ]:

            dir_path.mkdir(parents=True, exist_ok=True)


@lru_cache()
def get_settings() -> Settings:
    settings = Settings()
    settings.setup_directories()
    return settings
