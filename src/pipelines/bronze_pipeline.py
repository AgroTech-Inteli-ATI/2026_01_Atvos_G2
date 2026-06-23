"""
Camada Bronze — padronização estrutural.

A `BronzePipeline` recebe a planilha bruta (export ATVOS) e a deixa na estrutura
canônica do projeto: seleciona/renomeia as colunas de interesse e normaliza o
encoding das strings. Não aplica regras de qualidade nem descarta linhas.
"""
import logging
from pathlib import Path

import pandas as pd

from .io_utils import ler_arquivo, salvar_csv

logger = logging.getLogger("bronze_pipeline")

# Mapeamento colunas Excel (export ATVOS) → nomes internos padronizados
COLUNAS_RENAME = {
    "NUM"          : "numero_fazenda",
    "TALHAO"       : "id_talhao",
    "UNID_IND"     : "unidade_industrial",
    "DATA_PLANTIO" : "data_plantio",
    "AREA_HA"      : "area_ha",
    "AREA_PROD"    : "area_prod",
    "TCH_PROD"     : "tch_prod",
    "TON_ESTIM"    : "ton_estim",
    "VARIED"       : "variedade",
    "NO_CORTE"     : "no_corte",
    "ESTAGIO"      : "estagio",
    "CATEGORIA"    : "categoria",
    "SIT_TALHAO"   : "sit_talhao",
    "EMPRESA"      : "empresa",
    "SAFRA"        : "safra",
    "FAZENDA"      : "fazenda",
    "SETOR"        : "setor",
    "BLOCO"        : "bloco",
    "DE_TP_SOLO"   : "tipo_solo",
    "LATITUDE"     : "latitude",
    "LONGITUDE"    : "longitude",
}


class BronzePipeline:
    """Padronização estrutural do inventário bruto (camada Bronze)."""

    def __init__(self, colunas_rename: dict[str, str] | None = None):
        self.colunas_rename = colunas_rename or COLUNAS_RENAME

    # — Processos da camada -------------------------------------------------

    def selecionar_e_renomear(self, df: pd.DataFrame) -> pd.DataFrame:
        colunas_presentes = {k: v for k, v in self.colunas_rename.items() if k in df.columns}
        ausentes = set(self.colunas_rename) - set(colunas_presentes)
        if ausentes:
            logger.warning(f"Colunas esperadas não encontradas no Excel: {ausentes}")
        return df[list(colunas_presentes)].rename(columns=colunas_presentes)

    def padronizar_encoding(self, df: pd.DataFrame) -> pd.DataFrame:
        for col in df.select_dtypes(include=["object", "string"]).columns:
            df[col] = df[col].astype(str).str.strip()
            df[col] = df[col].replace({"nan": None, "None": None, "": None})
        return df

    # — Orquestração da camada ---------------------------------------------

    def processar(self, df_raw: pd.DataFrame) -> pd.DataFrame:
        """Aplica a camada Bronze em memória e retorna o DataFrame padronizado."""
        df = df_raw.copy()
        df = self.selecionar_e_renomear(df)
        df = self.padronizar_encoding(df)
        return df

    def executar(self, input_path: str | Path, output_path: str | Path) -> pd.DataFrame:
        """Lê o raw (xlsx/csv), aplica a camada Bronze e grava o CSV bronze."""
        df_bronze = self.processar(ler_arquivo(input_path))
        salvar_csv(df_bronze, output_path)
        return df_bronze
