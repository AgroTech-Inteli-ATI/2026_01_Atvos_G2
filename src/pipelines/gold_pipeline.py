"""
Camada Gold — aplicação das regras agronômicas.

A `GoldPipeline` recebe o DataFrame silver e produz a tabela Gold (uma linha por
talhão) com as orientações de todas as regras agronômicas e os insumos calculados
pivotados em colunas planas (`fosfato_*` e `dessecacao_*`).

As regras agronômicas em si vivem em `src/rules/` — esta camada apenas as orquestra.
"""
import logging
import math
from pathlib import Path

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

from .io_utils import DATA_DIR

logger = logging.getLogger("gold_pipeline")

INPUT_PATH = DATA_DIR / "inventario_silver.csv"
OUTPUT_PATH = DATA_DIR / "inventario_gold.csv"


class GoldPipeline:
    """Aplica as regras agronômicas sobre o silver e monta a tabela Gold."""

    # — Utilitários ---------------------------------------------------------

    @staticmethod
    def _id_ausente(id_talhao) -> bool:
        if id_talhao is None:
            return True
        if isinstance(id_talhao, float) and math.isnan(id_talhao):
            return True
        if str(id_talhao).strip() in ("", "nan", "None"):
            return True
        return False

    @staticmethod
    def _area_ha(talhao: dict) -> float | None:
        v = talhao.get("area_ha")
        try:
            return float(v) if v is not None else None
        except (ValueError, TypeError):
            return None

    # — Cálculo de insumos --------------------------------------------------

    def _calcular_insumos(self, talhao: dict, erradicacao_result: dict) -> dict:
        """
        Calcula os insumos aplicáveis ao talhão e retorna um dict plano com
        prefixos fosfato_ e dessecacao_, pronto para ser inserido na linha do Gold.
        """
        area = self._area_ha(talhao)

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

    # — Processos da camada -------------------------------------------------

    def processar_talhao(self, talhao: dict) -> dict | None:
        """Aplica todas as regras a um único talhão. Retorna None se o id for inválido."""
        id_talhao = talhao.get("id_talhao")

        if self._id_ausente(id_talhao):
            logger.error(f"Talhão sem id_talhao válido — registro pulado: {talhao}")
            return None

        try:
            erradicacao_result = calcular_erradicacao(talhao)
            insumos = self._calcular_insumos(talhao, erradicacao_result)

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

    @staticmethod
    def _montar_tabela_gold(resultados: list[dict]) -> pd.DataFrame:
        """Uma linha por talhão, com orientações e insumos pivotados em colunas planas."""
        rows = []
        for r in resultados:
            row = {
                "id_talhao": r["id_talhao"],
                "calagem_orientacao": r["calagem"].get("orientacao"),
                "calagem_dose_tha": r["calagem"].get("valor_calculado"),
                "calagem_regra": r["calagem"].get("regra_acionada"),
                "gessagem_orientacao": r["gessagem"].get("orientacao"),
                "gessagem_dose_kgha": r["gessagem"].get("valor_calculado"),
                "gessagem_regra": r["gessagem"].get("regra_acionada"),
                "fosfatagem_orientacao": r["fosfatagem"].get("orientacao"),
                "fosfatagem_dose_kgha": r["fosfatagem"].get("valor_calculado"),
                "fosfatagem_regra": r["fosfatagem"].get("regra_acionada"),
                "erradicacao_orientacao": r["erradicacao"].get("orientacao"),
                "erradicacao_tch": r["erradicacao"].get("valor_calculado"),
                "erradicacao_regra": r["erradicacao"].get("regra_acionada"),
                "janela_plantio_orientacao": r["janela_plantio"].get("orientacao"),
                "janela_plantio_regra": r["janela_plantio"].get("regra_acionada"),
            }
            row.update(r["_insumos"])  # insumos pivotados — fosfato_* e dessecacao_*
            rows.append(row)
        return pd.DataFrame(rows)

    # — Orquestração da camada ---------------------------------------------

    def processar(self, df_silver: pd.DataFrame) -> pd.DataFrame:
        """Aplica todas as regras sobre o silver (em memória) e retorna o DataFrame Gold."""
        resultados = []
        erros = 0

        for _, row in df_silver.iterrows():
            resultado = self.processar_talhao(row.to_dict())
            if resultado is not None:
                resultados.append(resultado)
            else:
                erros += 1

        logger.info(
            f"Pipeline Gold: {len(resultados)} registros processados, "
            f"{erros} erro(s) ignorado(s)."
        )
        return self._montar_tabela_gold(resultados)

    def executar(
        self,
        input_path: str | Path = INPUT_PATH,
        output_path: str | Path = OUTPUT_PATH,
    ) -> pd.DataFrame:
        """Lê o silver (csv), aplica as regras e grava o CSV gold."""
        try:
            df = pd.read_csv(input_path)
        except FileNotFoundError:
            logger.error(f"Arquivo de entrada não encontrado: {input_path}")
            raise
        except Exception as exc:
            logger.error(f"Erro ao ler arquivo de entrada '{input_path}': {exc}")
            raise

        df_gold = self.processar(df)
        df_gold.to_csv(output_path, index=False)
        logger.info(f"Gold salvo em {output_path} ({len(df_gold)} talhões)")
        return df_gold
