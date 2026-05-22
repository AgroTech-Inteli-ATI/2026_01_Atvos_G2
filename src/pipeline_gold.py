"""
Pipeline principal ATVOS — orquestrador Silver → Gold.

Uso (a partir da raiz do projeto):
    python src/pipeline_gold.py
"""
import sys
from datetime import date
from pathlib import Path

import pandas as pd

# Garante que a raiz do projeto esteja no sys.path ao rodar diretamente
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.processing.limpeza import main as _rodar_silver
from src.rules import (
    calcular_necessidade_calagem,
    calcular_necessidade_gessagem,
    calcular_necessidade_fosfatagem,
    calcular_erradicacao,
    calcular_janela_plantio,
)

_REGRAS_SEM_ACAO = {
    "sem_necessidade_calagem",
    "sem_necessidade_gessagem",
    "sem_necessidade_fosfatagem",
    "sem_necessidade_reforma",
    "nao_aplicavel_categoria",
    "nao_aplicavel_formacao",
}

_SEPARADOR = "=" * 60


# ============================================================
# FASE 1 — SILVER  (limpeza + enriquecimento com solo)
# ============================================================

def rodar_silver() -> pd.DataFrame:
    print(f"\n{_SEPARADOR}")
    print("  FASE 1 — SILVER")
    print(_SEPARADOR)
    df_silver, _ = _rodar_silver()
    print(f"Silver finalizado: {len(df_silver):,} talhões\n")
    return df_silver


# ============================================================
# FASE 2 — GOLD  (motor de regras agronômicas)
# ============================================================

def rodar_gold(df_silver: pd.DataFrame) -> pd.DataFrame:
    print(_SEPARADOR)
    print("  FASE 2 — GOLD (motor de regras)")
    print(_SEPARADOR)

    resultados = []

    for _, row in df_silver.iterrows():
        talhao = row.to_dict()

        janela = calcular_janela_plantio(talhao)

        chamadas = [
            ("calagem",    calcular_necessidade_calagem(talhao)),
            ("gessagem",   calcular_necessidade_gessagem(talhao)),
            ("fosfatagem", calcular_necessidade_fosfatagem(talhao)),
            ("erradicacao", calcular_erradicacao(talhao)),
        ]

        base = {
            "id_talhao":         talhao["id_talhao"],
            "unidade":           talhao.get("unidade_industrial"),
            "janela_orientacao": janela["orientacao"],
            "janela_regra":      janela["regra_acionada"],
            "data_geracao":      date.today().isoformat(),
        }

        todos_sem_acao = all(r["regra_acionada"] in _REGRAS_SEM_ACAO for _, r in chamadas)

        if todos_sem_acao:
            resultados.append({
                **base,
                "processo":        "nenhum processo",
                "orientacao":      "nenhuma intervenção corretiva necessária para este talhão",
                "valor_calculado": None,
                "regra_acionada":  "sem_necessidade_todos",
            })
        else:
            for processo, resultado in chamadas:
                if resultado["regra_acionada"] not in _REGRAS_SEM_ACAO:
                    resultados.append({
                        **base,
                        "processo":        processo,
                        "orientacao":      resultado["orientacao"],
                        "valor_calculado": resultado.get("valor_calculado"),
                        "regra_acionada":  resultado["regra_acionada"],
                    })

    df_gold = pd.DataFrame(resultados)

    out_dir = Path(__file__).resolve().parents[1] / "DATA" / "gold"
    out_dir.mkdir(parents=True, exist_ok=True)
    hoje = date.today().isoformat()

    df_gold.to_parquet(out_dir / f"orientacoes_{hoje}.parquet", index=False)
    df_gold.to_csv(out_dir / f"orientacoes_{hoje}.csv", index=False)

    print(f"Gold gerado: {len(df_gold):,} linhas | {df_gold['id_talhao'].nunique():,} talhões")
    print(f"Arquivos salvos em: DATA/gold/orientacoes_{hoje}.[parquet|csv]\n")

    return df_gold


# ============================================================
# ENTRYPOINT
# ============================================================

if __name__ == "__main__":
    print("\nIniciando pipeline ATVOS...\n")
    df_silver = rodar_silver()
    df_gold   = rodar_gold(df_silver)
    print("Pipeline concluída.")
