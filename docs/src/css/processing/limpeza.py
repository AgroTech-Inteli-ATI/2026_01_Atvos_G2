import logging
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("clean_solo")

# ---------------------------------------------------------------------------
# Configurações — PENDENTE VALIDAÇÃO ATVOS
# ---------------------------------------------------------------------------
PH_MIN, PH_MAX = 4.0, 8.5
CALCARIO_MIN, CALCARIO_MAX = 0.0, 100.0
FOSFORO_MIN, FOSFORO_MAX = 0.0, 500.0
MAX_IDADE_ANALISE_ANOS = 5

BASE_DIR   = Path(__file__).resolve().parents[3]
OUTPUT_PATH = BASE_DIR / "static" / "data" / "processed" / "solo_silver.parquet"
RAW_PATH    = BASE_DIR / "static" / "data" / "raw"       / "solo_raw.parquet"

UNIDADES_OFICIAIS: set[str] = {
    "UNIDADE_A", "UNIDADE_B", "UNIDADE_C",  # PENDENTE VALIDAÇÃO ATVOS
}

COLUNAS_CRITICAS = ["id_talhao", "unidade_industrial", "data_analise_solo"]

# ---------------------------------------------------------------------------
# QualityReport — registra tudo que acontece com os dados
# ---------------------------------------------------------------------------
@dataclass
class QualityReport:
    source: str
    linhas_originais: int = 0
    _descartes: list     = field(default_factory=list)
    _imputacoes: list    = field(default_factory=list)
    _sinalizacoes: list  = field(default_factory=list)

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
# Funções utilitárias
# ---------------------------------------------------------------------------

def padronizar_encoding(df: pd.DataFrame) -> pd.DataFrame:
    """Garante que colunas string estejam em UTF-8 sem espaços extras."""
    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].astype(str).str.strip()
        df[col] = df[col].replace({"nan": None, "None": None, "": None})
    return df


def normalizar_id_talhao(df: pd.DataFrame, campo: str) -> pd.DataFrame:
    """Remove espaços internos e coloca em maiúsculo. Ex: 'TAL 0001' → 'TAL0001'."""
    df[campo] = df[campo].astype(str).str.replace(r"\s+", "", regex=True).str.upper()
    return df


def bloquear_campo_obrigatorio(df: pd.DataFrame, campo: str, report: QualityReport) -> pd.DataFrame:
    """Remove linhas onde o campo é nulo — campo obrigatório."""
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


def remover_duplicatas(
    df: pd.DataFrame,
    chave: list[str],
    coluna_ordem: str,
    report: QualityReport,
) -> pd.DataFrame:
    """Mantém o registro mais recente para cada chave."""
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
# Regras de limpeza por campo
# ---------------------------------------------------------------------------

def tratar_ph_nulo(df: pd.DataFrame, report: QualityReport) -> pd.DataFrame:
    campo = "ph_solo"
    df = coerce_float(df, campo)

    invalidos = df[campo].notna() & ~df[campo].between(PH_MIN, PH_MAX)
    n_inv = int(invalidos.sum())
    if n_inv:
        report.registrar_descarte(campo=campo, valor_original=df.loc[invalidos, campo].tolist(),
                                  motivo=f"ph_solo fora do range [{PH_MIN}-{PH_MAX}]", n=n_inv)
        df = df[~invalidos].copy()

    nulos = df[campo].isna()
    if int(nulos.sum()):
        df.loc[nulos, "flag_ph_pendente"] = True
        report.registrar_sinalizacao(campo=campo, motivo="ph_solo nulo — talhão sinalizado como pendente",
                                     n=int(nulos.sum()))

    if "flag_ph_pendente" not in df.columns:
        df["flag_ph_pendente"] = False
    df["flag_ph_pendente"] = df["flag_ph_pendente"].fillna(False)
    return df


def tratar_calcario(df: pd.DataFrame, report: QualityReport) -> pd.DataFrame:
    campo = "teor_calcario"
    df = coerce_float(df, campo)

    invalidos = df[campo].notna() & ~df[campo].between(CALCARIO_MIN, CALCARIO_MAX)
    n_inv = int(invalidos.sum())
    if n_inv:
        report.registrar_descarte(campo=campo, valor_original=df.loc[invalidos, campo].tolist(),
                                  motivo=f"teor_calcario fora do range [{CALCARIO_MIN}-{CALCARIO_MAX}%]", n=n_inv)
        df = df[~invalidos].copy()

    nulos = df[campo].isna()
    if int(nulos.sum()):
        medias = df.groupby("unidade_industrial")[campo].transform("mean")
        df.loc[nulos, campo] = medias[nulos]
        ainda_nulos = df[campo].isna()
        report.registrar_imputacao(campo=campo, estrategia="imputação com média da unidade_industrial",
                                   n=int(nulos.sum()) - int(ainda_nulos.sum()))
        if int(ainda_nulos.sum()):
            report.registrar_sinalizacao(campo=campo,
                                         motivo="teor_calcario nulo — UI sem média disponível para imputar",
                                         n=int(ainda_nulos.sum()))
    return df


def tratar_fosforo(df: pd.DataFrame, report: QualityReport) -> pd.DataFrame:
    campo = "teor_fosforo"
    df = coerce_float(df, campo)

    invalidos = df[campo].notna() & ~df[campo].between(FOSFORO_MIN, FOSFORO_MAX)
    n_inv = int(invalidos.sum())
    if n_inv:
        report.registrar_descarte(campo=campo, valor_original=df.loc[invalidos, campo].tolist(),
                                  motivo=f"teor_fosforo fora do range [{FOSFORO_MIN}-{FOSFORO_MAX} mg/dm³]", n=n_inv)
        df = df[~invalidos].copy()

    nulos = df[campo].isna()
    if int(nulos.sum()):
        medias = df.groupby("unidade_industrial")[campo].transform("mean")
        df.loc[nulos, campo] = medias[nulos]
        ainda_nulos = df[campo].isna()
        report.registrar_imputacao(campo=campo, estrategia="imputação com média da unidade_industrial",
                                   n=int(nulos.sum()) - int(ainda_nulos.sum()))
        if int(ainda_nulos.sum()):
            report.registrar_sinalizacao(campo=campo,
                                         motivo="teor_fosforo nulo — UI sem média disponível para imputar",
                                         n=int(ainda_nulos.sum()))
    return df


def tratar_data_analise_solo(df: pd.DataFrame, report: QualityReport,
                              max_anos: int = MAX_IDADE_ANALISE_ANOS) -> pd.DataFrame:
    campo = "data_analise_solo"
    df[campo] = pd.to_datetime(df[campo], errors="coerce")

    nulos = df[campo].isna()
    n_nul = int(nulos.sum())
    if n_nul:
        report.registrar_descarte(campo=campo, valor_original="NaT",
                                  motivo="data_analise_solo nula — processamento do talhão bloqueado", n=n_nul)
        df = df[~nulos].copy()

    hoje  = pd.Timestamp(datetime.utcnow().date())
    cutoff = hoje - pd.DateOffset(years=max_anos)
    antigas = df[campo] < cutoff
    n_ant = int(antigas.sum())
    if n_ant:
        report.registrar_descarte(campo=campo, valor_original=df.loc[antigas, campo].dt.date.tolist(),
                                  motivo=f"data_analise_solo mais antiga que {max_anos} anos "
                                         f"(cutoff={cutoff.date()}) — validar com ATVOS", n=n_ant)
        df = df[~antigas].copy()

    return df


def tratar_unidade_industrial(df: pd.DataFrame, report: QualityReport,
                               unidades_validas: set[str] = UNIDADES_OFICIAIS) -> pd.DataFrame:
    campo = "unidade_industrial"
    df[campo] = df[campo].astype(str).str.strip().str.upper()
    df[campo] = df[campo].replace({"NAN": None, "": None})

    df = bloquear_campo_obrigatorio(df, campo, report)

    if unidades_validas:
        invalidos = ~df[campo].isin(unidades_validas)
        n_inv = int(invalidos.sum())
        if n_inv:
            df.loc[invalidos, "flag_ui_revisao"] = True
            report.registrar_sinalizacao(campo=campo,
                                         motivo="unidade_industrial fora da lista oficial — sinalizado para revisão manual",
                                         n=n_inv)
    else:
        logger.warning("Lista UNIDADES_OFICIAIS vazia — validação de lista DESABILITADA.")

    if "flag_ui_revisao" not in df.columns:
        df["flag_ui_revisao"] = False
    df["flag_ui_revisao"] = df["flag_ui_revisao"].fillna(False)
    return df

# ---------------------------------------------------------------------------
# Pipeline principal
# ---------------------------------------------------------------------------

def limpar_solo(df_raw: pd.DataFrame) -> tuple[pd.DataFrame, QualityReport]:
    report = QualityReport(source="SOLO")
    report.linhas_originais = len(df_raw)

    df = df_raw.copy()
    df = padronizar_encoding(df)

    df = bloquear_campo_obrigatorio(df, "id_talhao", report)
    df = bloquear_campo_obrigatorio(df, "unidade_industrial", report)
    df = normalizar_id_talhao(df, "id_talhao")

    df = tratar_data_analise_solo(df, report)
    df = tratar_unidade_industrial(df, report)
    df = tratar_ph_nulo(df, report)
    df = tratar_calcario(df, report)
    df = tratar_fosforo(df, report)

    df = remover_duplicatas(df, ["id_talhao"], "data_analise_solo", report)

    return df, report


def salvar_parquet(df: pd.DataFrame, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    table = pa.Table.from_pandas(df)
    pq.write_table(table, path, compression="snappy")
    logger.info(f"Silver salvo em {path} ({len(df):,} linhas)")

# ---------------------------------------------------------------------------
# Dados sintéticos para teste
# ---------------------------------------------------------------------------

def _gerar_dados_sinteticos() -> pd.DataFrame:
    import numpy as np
    rng = np.random.default_rng(42)
    n = 200

    data = {
        "id_talhao": [f"TAL {i:04d}" for i in range(n)],
        "unidade_industrial": rng.choice(["UNIDADE_A", "UNIDADE_B", "unidade_c", None, "INVALIDA_X"], n),
        "ph_solo": rng.choice([*rng.uniform(4.0, 8.5, 180), *rng.uniform(9.0, 12.0, 10), *([None] * 10)], n),
        "teor_calcario": rng.choice([*rng.uniform(0, 100, 180), *rng.uniform(110, 150, 10), *([None] * 10)], n),
        "teor_fosforo": rng.choice([*rng.uniform(0, 500, 180), *rng.uniform(600, 800, 10), *([None] * 10)], n),
        "data_analise_solo": rng.choice([
            *pd.date_range("2021-01-01", periods=170, freq="7D").tolist(),
            *pd.date_range("2015-01-01", periods=20,  freq="30D").tolist(),
            *([None] * 10),
        ], n),
    }
    df = pd.DataFrame(data)
    df = pd.concat([df, df.iloc[:5]], ignore_index=True)
    return df

# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

def main(df_raw: pd.DataFrame | None = None):
    if df_raw is None:
        if RAW_PATH.exists():
            df_raw = pd.read_parquet(RAW_PATH)
            logger.info(f"Lido {len(df_raw):,} registros de {RAW_PATH}")
        else:
            logger.warning("Arquivo raw não encontrado — usando dados sintéticos.")
            df_raw = _gerar_dados_sinteticos()

    df_silver, report = limpar_solo(df_raw)
    salvar_parquet(df_silver, OUTPUT_PATH)
    report.imprimir()
    report.imprimir_nulos(df_silver, COLUNAS_CRITICAS)
    return df_silver, report


if __name__ == "__main__":
    main()