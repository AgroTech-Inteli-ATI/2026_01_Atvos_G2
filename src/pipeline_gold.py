import pandas as pd
from datetime import date
import os

from src.rules import (
    calcular_necessidade_calagem,
    calcular_necessidade_gessagem,
    calcular_necessidade_fosfatagem,
    calcular_erradicacao,
    calcular_janela_plantio,
)

# Leitura do Silver
df = pd.read_csv("DATA/inventario_silver.csv")
print(f"Silver carregado: {len(df)} linhas")

# Loop por talhão
resultados = []

for _, row in df.iterrows():
    talhao = row.to_dict()

    chamadas = [
        ("calagem",        calcular_necessidade_calagem(talhao)),
        ("gessagem",       calcular_necessidade_gessagem(talhao)),
        ("fosfatagem",     calcular_necessidade_fosfatagem(talhao)),
        ("erradicacao",    calcular_erradicacao(talhao)),
        ("janela_plantio", calcular_janela_plantio(talhao)),
    ]

    for processo, resultado in chamadas:
        resultados.append({
            "id_talhao":       talhao["id_talhao"],
            "unidade":         talhao.get("unidade_industrial"),
            "processo":        processo,
            "orientacao":      resultado["orientacao"],
            "valor_calculado": resultado.get("valor_calculado"),
            "regra_acionada":  resultado["regra_acionada"],
            "data_geracao":    date.today().isoformat(),
        })

# Consolidar e salvar
df_gold = pd.DataFrame(resultados)

os.makedirs("DATA/gold", exist_ok=True)
hoje = date.today().isoformat()
df_gold.to_parquet(f"DATA/gold/orientacoes_{hoje}.parquet", index=False)
df_gold.to_csv(f"DATA/gold/orientacoes_{hoje}.csv", index=False)

print(f"✅ Gold gerado: {len(df_gold)} linhas | {df_gold['id_talhao'].nunique()} talhões | {df_gold['processo'].nunique()} processos")

if __name__ == "__main__":
    pass