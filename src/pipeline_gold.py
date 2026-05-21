import pandas as pd
from datetime import date
import os

# Leitura do Silver
df = pd.read_csv("DATA/inventario_silver.csv")
print(f"Silver carregado: {len(df)} linhas")

# Stubs temporários — substituir pelos imports reais quando Task 2.3 finalizar
def calcular_necessidade_calagem(talhao: dict) -> dict:
    return {"orientacao": "STUB", "valor_calculado": None, "regra_acionada": "stub"}

def calcular_gessagem(talhao: dict) -> dict:
    return {"orientacao": "STUB", "valor_calculado": None, "regra_acionada": "stub"}

# Loop por talhão
resultados = []

for _, row in df.iterrows():
    talhao = row.to_dict()

    chamadas = [
        ("calagem",  calcular_necessidade_calagem(talhao)),
        ("gessagem", calcular_gessagem(talhao)),
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

os.makedirs("data/gold", exist_ok=True)
hoje = date.today().isoformat()
df_gold.to_parquet(f"data/gold/orientacoes_{hoje}.parquet", index=False)
df_gold.to_csv(f"data/gold/orientacoes_{hoje}.csv", index=False)

print(f"✅ Gold gerado: {len(df_gold)} linhas | {df_gold['id_talhao'].nunique()} talhões | {df_gold['processo'].nunique()} processos") 