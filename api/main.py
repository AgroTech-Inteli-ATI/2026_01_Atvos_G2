"""
FastAPI server — ponte entre o frontend React e o motor de regras Python.

Aceita upload de CSV ou XLSX, executa silver + gold pipeline,
retorna os resultados no formato esperado pelo frontend.

Rotas:
  POST /api/run          — processa arquivo e retorna resultados
  GET  /api/historico    — lista histórico de importações
  GET  /api/health       — liveness check
"""
import io
import json
import sys
import uuid
from collections import Counter
from datetime import datetime
from pathlib import Path

import pandas as pd
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

SRC_DIR = Path(__file__).resolve().parent.parent / "src"
DATA_DIR = Path(__file__).resolve().parent.parent / "DATA"
sys.path.insert(0, str(SRC_DIR))

from pipelines import CAMADAS_INICIAIS, Pipeline

# Instância única reutilizada entre as requisições
PIPELINE = Pipeline()

HISTORY_FILE = Path(__file__).parent / "historico.json"
TEMP_DIR = Path(__file__).parent / "temp"
TEMP_DIR.mkdir(exist_ok=True)

app = FastAPI(title="ATVOS Motor de Regras API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Mapeamento: (processo_label, coluna_orientacao, coluna_dose, coluna_regra, coluna_insumo)
# ---------------------------------------------------------------------------
PROCESSOS_MAP = [
    ("Calagem",           "calagem_orientacao",       "calagem_dose_tha",      "calagem_regra",        None),
    ("Gessagem",          "gessagem_orientacao",       "gessagem_dose_kgha",    "gessagem_regra",       None),
    ("Fosfatagem",        "fosfatagem_orientacao",     "fosfatagem_dose_kgha",  "fosfatagem_regra",     None),
    ("Erradicação",       "erradicacao_orientacao",    "erradicacao_tch",       "erradicacao_regra",    None),
    ("Janela de Plantio", "janela_plantio_orientacao", None,                    "janela_plantio_regra", None),
    ("Insumo Fosfato",    "fosfato_orientacao",        "fosfato_dose_kg_ha",    "fosfato_regra",        "fosfato_insumo"),
    ("Dessecação",        "dessecacao_orientacao",     "dessecacao_dose_kg_ha", "dessecacao_regra",     "dessecacao_insumo"),
]

PROCESSOS_PREVENTIVOS = {"Calagem", "Gessagem", "Fosfatagem", "Insumo Fosfato", "Janela de Plantio"}
ALERT_KEYWORDS = ("reforma recomendada", "urgente", "imediatamente", "crítico", "alta prioridade")

ORIENTACOES_INVALIDAS = {"", "SEM_DADO", "NAO_APLICAVEL", "NÃO_APLICÁVEL", "None", "nan"}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _is_valid_orientacao(val) -> bool:
    if val is None:
        return False
    return str(val).strip() not in ORIENTACOES_INVALIDAS


def _is_alert(orientacao: str) -> bool:
    s = orientacao.lower()
    return any(k in s for k in ALERT_KEYWORDS)


def _safe_str(val) -> str:
    if val is None:
        return "-"
    if isinstance(val, float) and pd.isna(val):
        return "-"
    s = str(val).strip()
    return s if s not in ("nan", "None", "") else "-"


def _safe_float_str(val) -> str:
    if val is None:
        return "-"
    if isinstance(val, float) and pd.isna(val):
        return "-"
    try:
        return f"{float(val):.2f}"
    except (TypeError, ValueError):
        return "-"


def _gold_to_resultados(df_gold: pd.DataFrame) -> list[dict]:
    hoje = datetime.now().strftime("%d/%m/%Y")
    resultados = []
    for _, row in df_gold.iterrows():
        id_talhao = _safe_str(row.get("id_talhao"))
        unidade = _safe_str(row.get("unidade_industrial"))
        for processo, ori_col, dose_col, regra_col, insumo_col in PROCESSOS_MAP:
            ori = row.get(ori_col)
            if not _is_valid_orientacao(ori):
                continue
            resultados.append({
                "id":        id_talhao,
                "unidade":   unidade,
                "processo":  processo,
                "orientacao": str(ori),
                "alert":     _is_alert(str(ori)),
                "insumo":    _safe_str(row.get(insumo_col)) if insumo_col else "-",
                "dose":      _safe_float_str(row.get(dose_col)) if dose_col else "-",
                "regra":     _safe_str(row.get(regra_col)),
                "data":      hoje,
            })
    return resultados


def _compute_charts(resultados: list[dict]) -> tuple[list, list]:
    counts = Counter(r["processo"] for r in resultados)
    bar_data = [{"name": k, "value": v} for k, v in sorted(counts.items(), key=lambda x: -x[1])]

    prev = sum(v for k, v in counts.items() if k in PROCESSOS_PREVENTIVOS)
    corr = sum(v for k, v in counts.items() if k not in PROCESSOS_PREVENTIVOS)
    total = prev + corr
    pie_data = [
        {"name": "Preventiva", "value": prev, "pct": f"{prev / total * 100:.1f}%" if total else "0%"},
        {"name": "Corretiva",  "value": corr, "pct": f"{corr / total * 100:.1f}%" if total else "0%"},
    ]
    return bar_data, pie_data


def _compute_metrics(df_gold: pd.DataFrame, resultados: list[dict]) -> dict:
    total = len(df_gold)
    alert_ids = {r["id"] for r in resultados if r["alert"]}
    ori_cols = [c for c in df_gold.columns if c.endswith("_orientacao")]
    sem_dado = sum(
        1 for _, row in df_gold.iterrows()
        if any(str(row.get(c, "")).strip() == "SEM_DADO" for c in ori_cols)
    )
    return {
        "total_talhoes":       total,
        "talhoes_alerta":      len(alert_ids),
        "pct_dado_ausente":    round(sem_dado / total * 100, 1) if total else 0.0,
        "processos_avaliados": len(PROCESSOS_MAP),
    }


def _load_history() -> list:
    if HISTORY_FILE.exists():
        try:
            return json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return []
    return []


def _save_history(history: list) -> None:
    HISTORY_FILE.write_text(
        json.dumps(history, ensure_ascii=False, indent=2), encoding="utf-8"
    )


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.post("/api/run")
async def run_pipeline(
    file: UploadFile = File(...),
    nome: str = Form(...),
    camada_inicial: str = Form("raw"),
):
    ext = Path(file.filename or "").suffix.lower()
    if ext not in (".csv", ".xlsx", ".xls"):
        raise HTTPException(400, detail=f"Formato não suportado: '{ext}'. Use .csv ou .xlsx")

    if camada_inicial not in CAMADAS_INICIAIS:
        raise HTTPException(
            400,
            detail=f"Camada inicial inválida: '{camada_inicial}'. Use uma de {list(CAMADAS_INICIAIS)}.",
        )

    run_id = uuid.uuid4().hex[:8]

    try:
        contents = await file.read()

        # 1. Leitura do arquivo enviado
        if ext in (".xlsx", ".xls"):
            df_raw = pd.read_excel(io.BytesIO(contents), engine="openpyxl")
        else:
            df_raw = None
            for enc in ("utf-8", "utf-8-sig", "latin-1"):
                try:
                    df_raw = pd.read_csv(io.BytesIO(contents), encoding=enc)
                    break
                except UnicodeDecodeError:
                    continue
            if df_raw is None:
                raise HTTPException(400, detail="Não foi possível decodificar o CSV. Use UTF-8 ou Latin-1.")

        # 2. Validação do formato esperado para a camada de entrada escolhida
        if camada_inicial == "raw":
            if "TALHAO" not in df_raw.columns:
                raise HTTPException(
                    422,
                    detail="O modo 'raw' espera a planilha bruta do ATVOS (coluna 'TALHAO' ausente).",
                )
        else:  # bronze / silver — já devem estar com colunas padronizadas
            if "id_talhao" not in df_raw.columns:
                raise HTTPException(
                    422,
                    detail=f"O modo '{camada_inicial}' espera uma base já padronizada (coluna 'id_talhao' ausente).",
                )

        # 3. Executa a pipeline a partir da camada escolhida até o Gold
        df_silver, df_gold, _ = PIPELINE.executar(df_raw, camada_inicial, TEMP_DIR, run_id)

        if df_gold.empty:
            raise HTTPException(422, detail="Nenhum talhão válido encontrado no arquivo.")

        # 4. Enriquecer gold com unidade_industrial (vem do silver)
        if "unidade_industrial" in df_silver.columns and "id_talhao" in df_silver.columns:
            id_to_unidade = (
                df_silver.dropna(subset=["id_talhao"])
                .set_index("id_talhao")["unidade_industrial"]
                .to_dict()
            )
            df_gold["unidade_industrial"] = df_gold["id_talhao"].map(id_to_unidade).fillna("-")

        # 5. Transformar para formato do frontend
        resultados = _gold_to_resultados(df_gold)
        metrics = _compute_metrics(df_gold, resultados)
        bar_data, pie_data = _compute_charts(resultados)
        alert_cards = [
            {"id": r["id"], "processo": r["processo"], "orientacao": r["orientacao"]}
            for r in resultados if r["alert"]
        ][:4]

        # 6. Histórico
        processos_usados = sorted({r["processo"] for r in resultados})
        entry = {
            "data":           datetime.now().strftime("%d/%m/%Y"),
            "nome":           nome,
            "talhoes":        int(len(df_gold)),
            "processos":      processos_usados,
            "camada_inicial": camada_inicial,
        }
        history = _load_history()
        history.insert(0, entry)
        _save_history(history)

        return {
            "resultados":      resultados,
            "metrics":         metrics,
            "bar_data":        bar_data,
            "pie_data":        pie_data,
            "alert_cards":     alert_cards,
            "historico_entry": entry,
        }

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(500, detail=str(exc))

    finally:
        # Limpa os CSVs intermediários desta execução (bronze/silver/gold)
        for p in TEMP_DIR.glob(f"*_{run_id}.csv"):
            try:
                p.unlink()
            except OSError:
                pass


@app.get("/api/historico")
def get_historico():
    return {"historico": _load_history()}


@app.get("/api/health")
def health():
    return {"status": "ok"}
