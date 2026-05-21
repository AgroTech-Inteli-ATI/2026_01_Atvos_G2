import logging
import pandas as pd


from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("clean_inventario")

# ---------------------------------------------------------------------------
# Configurações — PENDENTE VALIDAÇÃO ATVOS
# ---------------------------------------------------------------------------
AREA_HA_MIN, AREA_HA_MAX   = 0.0, 10_000.0
TCH_MIN, TCH_MAX           = 0.0, 300.0
MAX_IDADE_PLANTIO_ANOS     = 10

# Estrutura: <raiz>/src/processing/limpeza.py
# parents[0] = processing/, parents[1] = src/, parents[2] = <raiz>/
BASE_DIR    = Path(__file__).resolve().parents[2]
SOLO_PATH   = BASE_DIR / "DATA" / "Dados_analise_solo.csv"
RAW_PATH    = BASE_DIR / "DATA" / "Inventario_atvos.xlsx"
OUTPUT_PATH = BASE_DIR / "DATA" / "inventario_silver.csv"

# Mapeamento colunas Excel → nomes internos padronizados
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

COLUNAS_CRITICAS = ["id_talhao", "unidade_industrial", "data_plantio"]

UNIDADES_OFICIAIS: set[str] = set()  # PENDENTE VALIDAÇÃO ATVOS — preencher com as UIs reais

# ---------------------------------------------------------------------------
# QualityReport
# ---------------------------------------------------------------------------
@dataclass
class QualityReport:
    source: str
    linhas_originais: int = 0
    _descartes: list  = field(default_factory=list)
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

# ---------------------------------------------------------------------------
# Utilitários
# ---------------------------------------------------------------------------

def selecionar_e_renomear(df: pd.DataFrame) -> pd.DataFrame:
    colunas_presentes = {k: v for k, v in COLUNAS_RENAME.items() if k in df.columns}
    ausentes = set(COLUNAS_RENAME.keys()) - set(colunas_presentes.keys())
    if ausentes:
        logger.warning(f"Colunas esperadas não encontradas no Excel: {ausentes}")
    return df[list(colunas_presentes.keys())].rename(columns=colunas_presentes)


def padronizar_encoding(df: pd.DataFrame) -> pd.DataFrame:
    for col in df.select_dtypes(include=["object", "string"]).columns:
        df[col] = df[col].astype(str).str.strip()
        df[col] = df[col].replace({"nan": None, "None": None, "": None})
    return df


def normalizar_id_talhao(df: pd.DataFrame) -> pd.DataFrame:
    df["id_talhao"] = (
        df["id_talhao"].astype(str)
        .str.replace(r"\s+", "", regex=True)
        .str.upper()
    )
    return df


def bloquear_campo_obrigatorio(df: pd.DataFrame, campo: str, report: QualityReport) -> pd.DataFrame:
    nulos = df[campo].isna()
    n = int(nulos.sum())
    if n:
        report.registrar_descarte(
            campo=campo,
            valor_original="NULL",
            motivo=f"{campo} nulo — campo obrigatório, registro bloqueado",
            n=n,
        )
        df = df[~nulos].copy()
    return df


def remover_duplicatas(df: pd.DataFrame, chave: list[str],
                       coluna_ordem: str, report: QualityReport) -> pd.DataFrame:
    antes = len(df)
    df = df.sort_values(coluna_ordem, ascending=False)
    df = df.drop_duplicates(subset=chave, keep="first")
    n = antes - len(df)
    if n:
        report.registrar_descarte(
            campo=str(chave),
            valor_original="duplicata",
            motivo=f"duplicata por {chave} — mantido registro mais recente",
            n=n,
        )
    return df.reset_index(drop=True)


def coerce_float(df: pd.DataFrame, campo: str) -> pd.DataFrame:
    df[campo] = pd.to_numeric(df[campo], errors="coerce")
    return df

# ---------------------------------------------------------------------------
# Regras por campo
# ---------------------------------------------------------------------------

def tratar_data_plantio(df: pd.DataFrame, report: QualityReport,
                         max_anos: int = MAX_IDADE_PLANTIO_ANOS) -> pd.DataFrame:
    campo = "data_plantio"
    df[campo] = pd.to_datetime(df[campo], errors="coerce")

    nulos = df[campo].isna()
    n_nul = int(nulos.sum())
    if n_nul:
        report.registrar_descarte(campo=campo, valor_original="NaT",
                                  motivo="data_plantio nula — registro bloqueado", n=n_nul)
        df = df[~nulos].copy()

    hoje   = pd.Timestamp(datetime.utcnow().date())
    cutoff = hoje - pd.DateOffset(years=max_anos)
    antigas = df[campo] < cutoff
    n_ant = int(antigas.sum())
    if n_ant:
        df.loc[antigas, "flag_plantio_antigo"] = True
        report.registrar_sinalizacao(campo=campo,
                                     motivo=f"data_plantio anterior a {max_anos} anos — sinalizado para revisão",
                                     n=n_ant)

    futuras = df[campo] > hoje
    n_fut = int(futuras.sum())
    if n_fut:
        report.registrar_descarte(campo=campo, valor_original=df.loc[futuras, campo].dt.date.tolist(),
                                  motivo="data_plantio no futuro — inválida", n=n_fut)
        df = df[~futuras].copy()

    if "flag_plantio_antigo" not in df.columns:
        df["flag_plantio_antigo"] = False
    df["flag_plantio_antigo"] = df["flag_plantio_antigo"].fillna(False)
    return df


def tratar_unidade_industrial(df: pd.DataFrame, report: QualityReport) -> pd.DataFrame:
    campo = "unidade_industrial"
    df[campo] = df[campo].astype(str).str.strip().str.upper()
    df[campo] = df[campo].replace({"NAN": None, "": None})

    df = bloquear_campo_obrigatorio(df, campo, report)

    if UNIDADES_OFICIAIS:
        invalidos = ~df[campo].isin(UNIDADES_OFICIAIS)
        n_inv = int(invalidos.sum())
        if n_inv:
            df.loc[invalidos, "flag_ui_revisao"] = True
            report.registrar_sinalizacao(campo=campo,
                                         motivo="unidade_industrial fora da lista oficial — sinalizado para revisão",
                                         n=n_inv)
    else:
        logger.warning("UNIDADES_OFICIAIS vazia — validação de lista DESABILITADA.")

    if "flag_ui_revisao" not in df.columns:
        df["flag_ui_revisao"] = False
    df["flag_ui_revisao"] = df["flag_ui_revisao"].fillna(False)
    return df


def tratar_area_ha(df: pd.DataFrame, report: QualityReport) -> pd.DataFrame:
    campo = "area_ha"
    df = coerce_float(df, campo)

    invalidos = df[campo].notna() & ~df[campo].between(AREA_HA_MIN, AREA_HA_MAX)
    n_inv = int(invalidos.sum())
    if n_inv:
        report.registrar_descarte(campo=campo, valor_original=df.loc[invalidos, campo].tolist(),
                                  motivo=f"area_ha fora do range [{AREA_HA_MIN}-{AREA_HA_MAX} ha]", n=n_inv)
        df = df[~invalidos].copy()

    nulos = df[campo].isna()
    if int(nulos.sum()):
        report.registrar_sinalizacao(campo=campo,
                                     motivo="area_ha nula — talhão sem área registrada",
                                     n=int(nulos.sum()))
    return df


def tratar_tch_prod(df: pd.DataFrame, report: QualityReport) -> pd.DataFrame:
    campo = "tch_prod"
    if campo not in df.columns:
        return df
    df = coerce_float(df, campo)

    invalidos = df[campo].notna() & ~df[campo].between(TCH_MIN, TCH_MAX)
    n_inv = int(invalidos.sum())
    if n_inv:
        report.registrar_descarte(campo=campo, valor_original=df.loc[invalidos, campo].tolist(),
                                  motivo=f"tch_prod fora do range [{TCH_MIN}-{TCH_MAX} t/ha]", n=n_inv)
        df = df[~invalidos].copy()

    nulos = df[campo].isna()
    if int(nulos.sum()):
        medias = df.groupby("unidade_industrial")[campo].transform("mean")
        df.loc[nulos, campo] = medias[nulos]
        ainda_nulos = df[campo].isna()
        report.registrar_imputacao(campo=campo,
                                   estrategia="imputação com média da unidade_industrial",
                                   n=int(nulos.sum()) - int(ainda_nulos.sum()))
        if int(ainda_nulos.sum()):
            report.registrar_sinalizacao(campo=campo,
                                         motivo="tch_prod nulo — UI sem média disponível para imputar",
                                         n=int(ainda_nulos.sum()))
    return df

def carregar_solo(path: Path) -> pd.DataFrame:
    df_solo = pd.read_csv(path, sep=";")
    df_solo["dt_analise1"] = pd.to_datetime(df_solo["dt_analise1"], errors="coerce")
    df_solo = df_solo.sort_values("dt_analise1", ascending=False)
    df_solo = df_solo.drop_duplicates(subset=["cd_upnivel1"], keep="first")
    df_solo = df_solo.rename(columns={"cd_upnivel1": "numero_fazenda"})
    df_solo["numero_fazenda"] = df_solo["numero_fazenda"].astype(str)
    logger.info(f"Solo carregado: {len(df_solo)} fazendas únicas")
    return df_solo
# ---------------------------------------------------------------------------
# Pipeline principal
# ---------------------------------------------------------------------------

def limpar_inventario(df_raw: pd.DataFrame) -> tuple[pd.DataFrame, QualityReport]:
    report = QualityReport(source="INVENTARIO_ATVOS")
    report.linhas_originais = len(df_raw)

    df = df_raw.copy()
    df = selecionar_e_renomear(df)
    df = padronizar_encoding(df)

    df = bloquear_campo_obrigatorio(df, "id_talhao", report)
    df = normalizar_id_talhao(df)

    df = tratar_data_plantio(df, report)
    df = tratar_unidade_industrial(df, report)
    df = tratar_area_ha(df, report)
    df = tratar_tch_prod(df, report)

    df = remover_duplicatas(df, ["id_talhao", "safra"], "data_plantio", report)

    return df, report


def salvar_csv(df: pd.DataFrame, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)

    df.to_csv(path, index=False, encoding="utf-8-sig")
    logger.info(f"Silver salvo em {path} ({len(df):,} linhas)")

# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

def main(df_raw: pd.DataFrame | None = None):
    if df_raw is None:
        if RAW_PATH.exists():
            df_raw = pd.read_excel(RAW_PATH, engine="openpyxl")
            logger.info(f"Lido {len(df_raw):,} registros de {RAW_PATH}")
        else:
            raise FileNotFoundError(f"Arquivo não encontrado: {RAW_PATH}")

    df_silver, report = limpar_inventario(df_raw)

    # Join com análise de solo
    if SOLO_PATH.exists():
        df_solo = carregar_solo(SOLO_PATH)
        df_silver["numero_fazenda"] = df_silver["numero_fazenda"].astype(str)
        df_silver = df_silver.merge(df_solo, on="numero_fazenda", how="left")
        logger.info(f"Join com solo concluído: {len(df_silver):,} linhas")
    else:
        logger.warning(f"Arquivo de solo não encontrado: {SOLO_PATH}")

    salvar_csv(df_silver, OUTPUT_PATH)
    report.imprimir()
    report.imprimir_nulos(df_silver, COLUNAS_CRITICAS)
    return df_silver, report
if __name__ == "__main__":
    main()