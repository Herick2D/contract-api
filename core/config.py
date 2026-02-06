import json
from pathlib import Path
from typing import Dict, Any

DEFAULT_CONFIG = {
    "advogado_nome": "João Thomaz Prazeres Gondim",
    "advogado_oab": "270.757",
    "escritorio_telefone": "(21) 2262-7979",
    "escritorio_whatsapp": "(21) 96975-0156",
    "escritorio_email": "quintoandar@gondimadv.com.br",
    "escritorio_email_intimacoes": "camaras.arbitrais@gondimadv.com.br",
    "escritorio_endereco": "Avenida Paulo de Frontin, 1, Centro Empresarial, Cidade Nova, Rio de Janeiro - RJ, 20260-010",
    "nacionalidade_padrao": "brasileiro(a)",
}

CONFIG_FILE = "config.json"

def load_config(config_path: str = None) -> Dict[str, Any]:

    if config_path is None:
        config_path = CONFIG_FILE

    config_file = Path(config_path)

    if config_file.exists():
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return {**DEFAULT_CONFIG, **config}
        except Exception as e:
            print(f"Aviso: Erro ao carregar config.json: {e}. Usando padrões.")
            return DEFAULT_CONFIG.copy()

    return DEFAULT_CONFIG.copy()


def save_config(config: Dict[str, Any], config_path: str = None) -> bool:

    if config_path is None:
        config_path = CONFIG_FILE

    try:
        config_file = Path(config_path)
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Erro ao salvar config.json: {e}")
        return False


def get_config() -> Dict[str, Any]:
    return load_config()


def update_config(updates: Dict[str, Any], config_path: str = None) -> bool:
    config = load_config(config_path)
    config.update(updates)
    return save_config(config, config_path)
