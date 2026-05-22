import pandas as pd

from rules import (
    calcular_necessidade_calagem,
    calcular_necessidade_gessagem,
    calcular_necessidade_fosfatagem,
    calcular_erradicacao,
    calcular_janela_plantio
)

INPUT_PATH = "../DATA/inventario_silver.csv"
OUTPUT_PATH = "../DATA/inventario_gold.csv"


def processar_pipeline_gold():

    df = pd.read_csv(INPUT_PATH)

    resultados = []

    for _, row in df.iterrows():

        talhao = row.to_dict()

        resultado = {
            "id_talhao": talhao.get("id_talhao"),

            "calagem":
                calcular_necessidade_calagem(talhao),

            "gessagem":
                calcular_necessidade_gessagem(talhao),

            "fosfatagem":
                calcular_necessidade_fosfatagem(talhao),

            "erradicacao":
                calcular_erradicacao(talhao),

            "janela_plantio":
                calcular_janela_plantio(talhao)
        }

        resultados.append(resultado)

    output = pd.DataFrame(resultados)

    output.to_csv(OUTPUT_PATH, index=False)

    print("Pipeline Gold executado com sucesso.")


if __name__ == "__main__":
    processar_pipeline_gold()