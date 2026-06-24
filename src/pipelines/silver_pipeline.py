"""
Camada Silver — regras de qualidade + enriquecimento com solo.

A `SilverPipeline` recebe um DataFrame já no formato bronze (colunas padronizadas)
e aplica os descartes, imputações, sinalizações e a deduplicação, registrando tudo
em um `QualityReport`. Por fim, junta a análise de solo via `numero_fazenda`.
"""
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

import pandas as pd

from .io_utils import DATA_DIR, ler_arquivo, salvar_csv

logger = logging.getLogger("silver_pipeline")

# --------------------------------------------------------------------------
# Configurações — PENDENTE VALIDAÇÃO ATVOS
# --------------------------------------------------------------------------
AREA_HA_MIN, AREA_HA_MAX = 0.0, 10_000.0
TCH_MIN, TCH_MAX = 0.0, 300.0
MAX_IDADE_PLANTIO_ANOS = 10

SOLO_PATH = DATA_DIR / "Dados_analise_solo.csv"
OUTPUT_PATH = DATA_DIR / "inventario_silver.csv"

COLUNAS_CRITICAS = ["id_talhao", "unidade_industrial", "data_plantio"]
UNIDADES_OFICIAIS: set[str] = set()  # PENDENTE VALIDAÇÃO ATVOS — preencher com as UIs reais


# --------------------------------------------------------------------------
# QualityReport — auditoria das transformações da camada Silver
# --------------------------------------------------------------------------
@dataclass
class QualityReport:
    source: str
    linhas_originais: int = 0
    _descartes: list = field(default_factory=list)
    _imputacoes: list = field(default_factory=list)
    _sinalizacoes: list = field(default_factory=list)

    def registrar_descarte(self, campo, valor_original, motivo, n):
        self._descartes.append({"campo": campo, "motivo": motivo, "n": n, "exemplo": str(valor_original)[:80]})
        logger.warning(f"[DESCARTE] {campo} | {motivo} | n={n}")

    def registrar_imputacao(self, campo, estrategia, n):
        self._imputacoes.append({"campo": campo, "estrategia": estrategia, "n": n})
        logger.info(f"[IMPUTAÇÃO] {campo} | {estrategia} | n={n}")

    def registrar_sinalizacao(self, campo, motivo, n):
        self._sinalizacoes.append({"campo": campo, "motivo": motivo, "n": n})
        logger.info(f"[SINALIZAÇÃO] {campo} | {motivo} | n={n}")

    def imprimir(self):
        print(f"\n{'='*60}")
        print(f"  QUALITY REPORT — {self.source}")
        print(f"{'='*60}")
        print(f"  Linhas originais : {self.linhas_originais}")
        if self._descartes:
            print(f"\n  DESCARTES ({len(self._descartes)} regras):")
            for d in self._descartes:
                print(f"    • [{d['campo']}] {d['motivo']} — n={d['n']}")
        if self._imputacoes:
            print(f"\n  IMPUTAÇÕES ({len(self._imputacoes)} regras):")
            for i in self._imputacoes:
                print(f"    • [{i['campo']}] {i['estrategia']} — n={i['n']}")
        if self._sinalizacoes:
            print(f"\n  SINALIZAÇÕES ({len(self._sinalizacoes)} regras):")
            for s in self._sinalizacoes:
                print(f"    • [{s['campo']}] {s['motivo']} — n={s['n']}")
        print(f"{'='*60}\n")

    def imprimir_nulos(self, df: pd.DataFrame, colunas: list[str]):
        print("  NULOS NAS COLUNAS CRÍTICAS (silver):")
        for col in colunas:
            if col in df.columns:
                n = int(df[col].isna().sum())
                print(f"    • {col}: {n} nulos")
        print()


class SilverPipeline:
    """Limpeza de qualidade do inventário + join com a análise de solo (camada Silver)."""

    def __init__(
        self,
        solo_path: Path = SOLO_PATH,
        area_range: tuple[float, float] = (AREA_HA_MIN, AREA_HA_MAX),
        tch_range: tuple[float, float] = (TCH_MIN, TCH_MAX),
        max_idade_plantio_anos: int = MAX_IDADE_PLANTIO_ANOS,
        unidades_oficiais: set[str] | None = None,
    ):
        self.solo_path = solo_path
        self.area_min, self.area_max = area_range
        self.tch_min, self.tch_max = tch_range
        self.max_idade_plantio_anos = max_idade_plantio_anos
        self.unidades_oficiais = unidades_oficiais if unidades_oficiais is not None else UNIDADES_OFICIAIS
        self.report: QualityReport | None = None

    # — Utilitários ---------------------------------------------------------

    @staticmethod
    def _coerce_float(df: pd.DataFrame, campo: str) -> pd.DataFrame:
        df[campo] = pd.to_numeric(df[campo], errors="coerce")
        return df

    # — Processos da camada (cada um registra no self.report) ---------------

    def bloquear_campo_obrigatorio(self, df: pd.DataFrame, campo: str) -> pd.DataFrame:
        nulos = df[campo].isna()
        n = int(nulos.sum())
        if n:
            self.report.registrar_descarte(
                campo=campo, valor_original="NULL",
                motivo=f"{campo} nulo — campo obrigatório, registro bloqueado", n=n,
            )
            df = df[~nulos].copy()
        return df

    def normalizar_id_talhao(self, df: pd.DataFrame) -> pd.DataFrame:
        df["id_talhao"] = (
            df["id_talhao"].astype(str)
            .str.replace(r"\s+", "", regex=True)
            .str.upper()
        )
        return df

    def tratar_data_plantio(self, df: pd.DataFrame) -> pd.DataFrame:
        campo = "data_plantio"
        df[campo] = pd.to_datetime(df[campo], errors="coerce")

        nulos = df[campo].isna()
        n_nul = int(nulos.sum())
        if n_nul:
            self.report.registrar_descarte(campo=campo, valor_original="NaT",
                                           motivo="data_plantio nula — registro bloqueado", n=n_nul)
            df = df[~nulos].copy()

        hoje = pd.Timestamp(datetime.utcnow().date())
        cutoff = hoje - pd.DateOffset(years=self.max_idade_plantio_anos)
        antigas = df[campo] < cutoff
        n_ant = int(antigas.sum())
        if n_ant:
            df.loc[antigas, "flag_plantio_antigo"] = True
            self.report.registrar_sinalizacao(
                campo=campo,
                motivo=f"data_plantio anterior a {self.max_idade_plantio_anos} anos — sinalizado para revisão",
                n=n_ant)

        futuras = df[campo] > hoje
        n_fut = int(futuras.sum())
        if n_fut:
            self.report.registrar_descarte(campo=campo, valor_original=df.loc[futuras, campo].dt.date.tolist(),
                                           motivo="data_plantio no futuro — inválida", n=n_fut)
            df = df[~futuras].copy()

        if "flag_plantio_antigo" not in df.columns:
            df["flag_plantio_antigo"] = False
        df["flag_plantio_antigo"] = df["flag_plantio_antigo"].fillna(False)
        return df

    def tratar_unidade_industrial(self, df: pd.DataFrame) -> pd.DataFrame:
        campo = "unidade_industrial"
        df[campo] = df[campo].astype(str).str.strip().str.upper()
        df[campo] = df[campo].replace({"NAN": None, "": None})

        df = self.bloquear_campo_obrigatorio(df, campo)

        if self.unidades_oficiais:
            invalidos = ~df[campo].isin(self.unidades_oficiais)
            n_inv = int(invalidos.sum())
            if n_inv:
                df.loc[invalidos, "flag_ui_revisao"] = True
                self.report.registrar_sinalizacao(
                    campo=campo,
                    motivo="unidade_industrial fora da lista oficial — sinalizado para revisão",
                    n=n_inv)
        else:
            logger.warning("UNIDADES_OFICIAIS vazia — validação de lista DESABILITADA.")

        if "flag_ui_revisao" not in df.columns:
            df["flag_ui_revisao"] = False
        df["flag_ui_revisao"] = df["flag_ui_revisao"].fillna(False)
        return df

    def tratar_area_ha(self, df: pd.DataFrame) -> pd.DataFrame:
        campo = "area_ha"
        df = self._coerce_float(df, campo)

        invalidos = df[campo].notna() & ~df[campo].between(self.area_min, self.area_max)
        n_inv = int(invalidos.sum())
        if n_inv:
            self.report.registrar_descarte(campo=campo, valor_original=df.loc[invalidos, campo].tolist(),
                                           motivo=f"area_ha fora do range [{self.area_min}-{self.area_max} ha]", n=n_inv)
            df = df[~invalidos].copy()

        nulos = df[campo].isna()
        if int(nulos.sum()):
            self.report.registrar_sinalizacao(campo=campo,
                                              motivo="area_ha nula — talhão sem área registrada",
                                              n=int(nulos.sum()))
        return df

    def tratar_tch_prod(self, df: pd.DataFrame) -> pd.DataFrame:
        campo = "tch_prod"
        if campo not in df.columns:
            return df
        df = self._coerce_float(df, campo)

        invalidos = df[campo].notna() & ~df[campo].between(self.tch_min, self.tch_max)
        n_inv = int(invalidos.sum())
        if n_inv:
            self.report.registrar_descarte(campo=campo, valor_original=df.loc[invalidos, campo].tolist(),
                                           motivo=f"tch_prod fora do range [{self.tch_min}-{self.tch_max} t/ha]", n=n_inv)
            df = df[~invalidos].copy()

        nulos = df[campo].isna()
        if int(nulos.sum()):
            medias = df.groupby("unidade_industrial")[campo].transform("mean")
            df.loc[nulos, campo] = medias[nulos]
            ainda_nulos = df[campo].isna()
            self.report.registrar_imputacao(campo=campo,
                                            estrategia="imputação com média da unidade_industrial",
                                            n=int(nulos.sum()) - int(ainda_nulos.sum()))
            if int(ainda_nulos.sum()):
                self.report.registrar_sinalizacao(campo=campo,
                                                  motivo="tch_prod nulo — UI sem média disponível para imputar",
                                                  n=int(ainda_nulos.sum()))
        return df

    def remover_duplicatas(self, df: pd.DataFrame, chave: list[str], coluna_ordem: str) -> pd.DataFrame:
        antes = len(df)
        df = df.sort_values(coluna_ordem, ascending=False)
        df = df.drop_duplicates(subset=chave, keep="first")
        n = antes - len(df)
        if n:
            self.report.registrar_descarte(
                campo=str(chave), valor_original="duplicata",
                motivo=f"duplicata por {chave} — mantido registro mais recente", n=n)
        return df.reset_index(drop=True)

    # — Enriquecimento com solo --------------------------------------------

    def carregar_solo(self, path: Path | None = None) -> pd.DataFrame:
        path = path or self.solo_path
        df_solo = pd.read_csv(path, sep=";")
        df_solo["dt_analise1"] = pd.to_datetime(df_solo["dt_analise1"], errors="coerce")
        df_solo = df_solo.sort_values("dt_analise1", ascending=False)
        df_solo = df_solo.drop_duplicates(subset=["cd_upnivel1"], keep="first")
        df_solo = df_solo.rename(columns={"cd_upnivel1": "numero_fazenda"})
        df_solo["numero_fazenda"] = df_solo["numero_fazenda"].astype(str)
        logger.info(f"Solo carregado: {len(df_solo)} fazendas únicas")
        return df_solo

    def juntar_solo(self, df_silver: pd.DataFrame) -> pd.DataFrame:
        """Enriquece o silver com a análise de solo via `numero_fazenda`."""
        if not self.solo_path.exists():
            logger.warning(f"Arquivo de solo não encontrado: {self.solo_path}")
            return df_silver

        df_solo = self.carregar_solo()
        df_silver = df_silver.copy()
        df_silver["numero_fazenda"] = df_silver["numero_fazenda"].astype(str)
        df_silver = df_silver.merge(df_solo, on="numero_fazenda", how="left")
        logger.info(f"Join com solo concluído: {len(df_silver):,} linhas")
        return df_silver

    # — Orquestração da camada ---------------------------------------------

    def processar(self, df_bronze: pd.DataFrame) -> tuple[pd.DataFrame, QualityReport]:
        """
        Aplica as regras de qualidade em memória. Retorna `(df_silver, report)`.
        O join com solo NÃO é feito aqui — use `juntar_solo` ou `executar`.
        """
        self.report = QualityReport(source="INVENTARIO_ATVOS")
        self.report.linhas_originais = len(df_bronze)

        df = df_bronze.copy()
        df = self.bloquear_campo_obrigatorio(df, "id_talhao")
        df = self.normalizar_id_talhao(df)
        df = self.tratar_data_plantio(df)
        df = self.tratar_unidade_industrial(df)
        df = self.tratar_area_ha(df)
        df = self.tratar_tch_prod(df)
        df = self.remover_duplicatas(df, ["id_talhao", "safra"], "data_plantio")

        return df, self.report

    def executar(self, input_path: str | Path, output_path: str | Path) -> pd.DataFrame:
        """Lê o bronze (csv), aplica a camada Silver + join com solo e grava o CSV silver."""
        df_silver, report = self.processar(ler_arquivo(input_path))
        df_silver = self.juntar_solo(df_silver)
        salvar_csv(df_silver, output_path)
        report.imprimir()
        return df_silver
