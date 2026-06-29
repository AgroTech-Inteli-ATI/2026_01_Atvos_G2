"""
Utilitários de I/O compartilhados pelas pipelines.

Centraliza a leitura de arquivos de entrada (Excel/CSV), a gravação de CSVs e os
caminhos base do projeto, evitando duplicação entre Bronze, Silver e Gold.
"""
import logging
from pathlib import Path

import pandas as pd

logger = logging.getLogger("pipelines.io")

# <raiz>/src/pipelines/io_utils.py → parents[2] = <raiz>
BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "DATA"


def ler_arquivo(input_path: str | Path) -> pd.DataFrame:
    """Lê um arquivo de entrada — Excel (.xlsx/.xls) ou CSV — em DataFrame."""
    path = Path(input_path)
    if path.suffix.lower() in (".xlsx", ".xls"):
        return pd.read_excel(path, engine="openpyxl")
    return pd.read_csv(path)


def salvar_csv(df: pd.DataFrame, path: str | Path) -> None:
    """Grava um DataFrame em CSV (UTF-8 com BOM), criando o diretório se preciso."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, encoding="utf-8-sig")
    logger.info(f"CSV salvo em {path} ({len(df):,} linhas)")
