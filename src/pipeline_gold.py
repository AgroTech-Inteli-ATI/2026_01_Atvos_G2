import logging
import math
import pandas as pd

from rules import (
    calcular_necessidade_calagem,
    calcular_necessidade_gessagem,
    calcular_necessidade_fosfatagem,
    calcular_erradicacao,
    calcular_janela_plantio,
)
from rules.insumos import (
    calcular_dose_fosfatagem,
    calcular_dose_dessecacao,
    estagio_soqueira_de_no_corte,
    infestacao_de_sit_talhao,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("pipeline_gold")

INPUT_PATH = "../DATA/inventario_silver.csv"
OUTPUT_PATH = "../DATA/inventario_gold.csv"


def _id_ausente(id_talhao) -> bool:
    if id_talhao is None:
        return True
    if isinstance(id_talhao, float) and math.isnan(id_talhao):
        return True
    if str(id_talhao).strip() in ("", "nan", "None"):
        return True
    return False


def _area_ha(talhao: dict) -> float | None:
    v = talhao.get("area_ha")
    try:
        return float(v) if v is not None else None
    except (ValueError, TypeError):
        return None


def _calcular_insumos(talhao: dict, erradicacao_result: dict) -> dict:
    """
    Calcula os insumos aplicáveis ao talhão e retorna um dict plano com
    prefixos fosfato_ e dessecacao_, pronto para ser inserido diretamente
    na linha do Gold.

    Chaves produzidas (valor None quando o insumo não se aplica):
        fosfato_insumo, fosfato_dose_kg_ha, fosfato_quantidade_total_kg,
        fosfato_orientacao, fosfato_regra
        dessecacao_insumo, dessecacao_dose_kg_ha, dessecacao_dose_l_ha,
        dessecacao_quantidade_total_kg, dessecacao_orientacao, dessecacao_regra
    """
    area = _area_ha(talhao)

    # Valores padrão (insumo não aplicável ou dados ausentes)
    row: dict = {
        "fosfato_insumo": None,
        "fosfato_dose_kg_ha": None,
        "fosfato_quantidade_total_kg": None,
        "fosfato_orientacao": None,
        "fosfato_regra": None,
        "dessecacao_insumo": None,
        "dessecacao_dose_kg_ha": None,
        "dessecacao_dose_l_ha": None,
        "dessecacao_quantidade_total_kg": None,
        "dessecacao_orientacao": None,
        "dessecacao_regra": None,
    }

    # — Fosfatagem
    dose_fosf = calcular_dose_fosfatagem(
        p_disponivel=talhao.get("p1"),
        textura_solo=talhao.get("tipo_solo"),
        tchan_estimado=talhao.get("tch_prod"),
    )
    if dose_fosf.get("orientacao") != "SEM_DADO" and dose_fosf.get("dose_kg_ha", 0) > 0:
        d = dose_fosf["dose_kg_ha"]
        row.update({
            "fosfato_insumo": dose_fosf["insumo"],
            "fosfato_dose_kg_ha": d,
            "fosfato_quantidade_total_kg": round(d * area, 2) if area else None,
            "fosfato_orientacao": dose_fosf["orientacao"],
            "fosfato_regra": dose_fosf["regra_acionada"],
        })

    # — Dessecação (apenas quando reforma recomendada)
    reforma = (
        erradicacao_result.get("detalhes", {}).get("reforma_recomendada", False)
        if erradicacao_result.get("orientacao") != "SEM_DADO"
        else False
    )
    if reforma:
        estagio = estagio_soqueira_de_no_corte(talhao.get("no_corte"))
        infestacao = infestacao_de_sit_talhao(talhao.get("sit_talhao"))
        dose_dss = calcular_dose_dessecacao(infestacao, estagio)
        if dose_dss.get("orientacao") != "SEM_DADO":
            d_kg = dose_dss["dose_kg_ha"]
            row.update({
                "dessecacao_insumo": dose_dss["insumo"],
                "dessecacao_dose_kg_ha": d_kg,
                "dessecacao_dose_l_ha": dose_dss.get("dose_l_ha"),
                "dessecacao_quantidade_total_kg": round(d_kg * area, 2) if area else None,
                "dessecacao_orientacao": dose_dss["orientacao"],
                "dessecacao_regra": dose_dss["regra_acionada"],
            })

    return row


def processar_talhao(talhao: dict) -> dict | None:
    id_talhao = talhao.get("id_talhao")

    if _id_ausente(id_talhao):
        logger.error(f"Talhão sem id_talhao válido — registro pulado: {talhao}")
        return None

    try:
        erradicacao_result = calcular_erradicacao(talhao)
        insumos = _calcular_insumos(talhao, erradicacao_result)

        return {
            "id_talhao": id_talhao,
            "calagem": calcular_necessidade_calagem(talhao),
            "gessagem": calcular_necessidade_gessagem(talhao),
            "fosfatagem": calcular_necessidade_fosfatagem(talhao),
            "erradicacao": erradicacao_result,
            "janela_plantio": calcular_janela_plantio(talhao),
            "_insumos": insumos,
        }
    except Exception as exc:
        logger.error(f"Erro inesperado ao processar talhão '{id_talhao}': {exc}")
        return None


def _montar_tabela_gold(resultados: list[dict]) -> pd.DataFrame:
    """
    Uma linha por talhão com todas as orientações agronômicas e os insumos
    já pivotados em colunas planas (fosfato_* e dessecacao_*).
    """
    rows = []
    for r in resultados:
        row = {
            "id_talhao": r["id_talhao"],
            # Calagem
            "calagem_orientacao": r["calagem"].get("orientacao"),
            "calagem_dose_tha": r["calagem"].get("valor_calculado"),
            "calagem_regra": r["calagem"].get("regra_acionada"),
            # Gessagem
            "gessagem_orientacao": r["gessagem"].get("orientacao"),
            "gessagem_dose_kgha": r["gessagem"].get("valor_calculado"),
            "gessagem_regra": r["gessagem"].get("regra_acionada"),
            # Fosfatagem (regra de solo)
            "fosfatagem_orientacao": r["fosfatagem"].get("orientacao"),
            "fosfatagem_dose_kgha": r["fosfatagem"].get("valor_calculado"),
            "fosfatagem_regra": r["fosfatagem"].get("regra_acionada"),
            # Erradicação
            "erradicacao_orientacao": r["erradicacao"].get("orientacao"),
            "erradicacao_tch": r["erradicacao"].get("valor_calculado"),
            "erradicacao_regra": r["erradicacao"].get("regra_acionada"),
            # Janela de plantio
            "janela_plantio_orientacao": r["janela_plantio"].get("orientacao"),
            "janela_plantio_regra": r["janela_plantio"].get("regra_acionada"),
        }
        # Insumos pivotados — fosfato_* e dessecacao_*
        row.update(r["_insumos"])
        rows.append(row)
    return pd.DataFrame(rows)


def processar_pipeline_gold(
    input_path: str = INPUT_PATH,
    output_path: str = OUTPUT_PATH,
) -> pd.DataFrame:
    """
    Executa o pipeline Gold completo e salva um único CSV.

    O CSV de saída contém uma linha por talhão com:
      - orientações de todas as regras agronômicas
      - insumos calculados em colunas planas:
          fosfato_insumo, fosfato_dose_kg_ha, fosfato_quantidade_total_kg,
          dessecacao_insumo, dessecacao_dose_kg_ha, dessecacao_dose_l_ha,
          dessecacao_quantidade_total_kg
    """
    try:
        df = pd.read_csv(input_path)
    except FileNotFoundError:
        logger.error(f"Arquivo de entrada não encontrado: {input_path}")
        raise
    except Exception as exc:
        logger.error(f"Erro ao ler arquivo de entrada '{input_path}': {exc}")
        raise

    resultados = []
    erros = 0

    for _, row in df.iterrows():
        resultado = processar_talhao(row.to_dict())
        if resultado is not None:
            resultados.append(resultado)
        else:
            erros += 1

    logger.info(
        f"Pipeline Gold: {len(resultados)} registros processados, "
        f"{erros} erro(s) ignorado(s)."
    )

    df_gold = _montar_tabela_gold(resultados)
    df_gold.to_csv(output_path, index=False)
    logger.info(f"Gold salvo em {output_path} ({len(df_gold)} talhões)")

    return df_gold


if __name__ == "__main__":
    processar_pipeline_gold()
