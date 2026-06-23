"""
Orquestrador da pipeline por ponto de partida.

A pipeline segue o padrão medallion `raw → bronze → silver → gold` e sempre roda
até o Gold. O que muda é a **camada de entrada**: dependendo do estado da planilha
recebida, o usuário escolhe começar em `raw`, `bronze` ou `silver`.

A classe `Pipeline` compõe as três pipelines de camada (`BronzePipeline`,
`SilverPipeline`, `GoldPipeline`) e pode ser reutilizada/reinstanciada com
implementações customizadas de cada camada. Cada camada produzida é materializada
em um CSV próprio (um arquivo por camada).
"""
import logging
from pathlib import Path

import pandas as pd

from .bronze_pipeline import BronzePipeline
from .silver_pipeline import SilverPipeline
from .gold_pipeline import GoldPipeline
from .io_utils import salvar_csv

logger = logging.getLogger("pipeline")

CAMADAS_INICIAIS = ("raw", "bronze", "silver")


class Pipeline:
    """Orquestra Bronze → Silver → Gold a partir de uma camada de entrada escolhida."""

    def __init__(
        self,
        bronze: BronzePipeline | None = None,
        silver: SilverPipeline | None = None,
        gold: GoldPipeline | None = None,
    ):
        self.bronze = bronze or BronzePipeline()
        self.silver = silver or SilverPipeline()
        self.gold = gold or GoldPipeline()

    def executar(
        self,
        df_input: pd.DataFrame,
        camada_inicial: str,
        temp_dir: str | Path,
        run_id: str,
    ) -> tuple[pd.DataFrame, pd.DataFrame, list[Path]]:
        """
        Executa a pipeline a partir de `camada_inicial` até o Gold.

        Args:
            df_input: DataFrame já lido do arquivo enviado, no estado da `camada_inicial`.
            camada_inicial: "raw", "bronze" ou "silver".
            temp_dir: diretório onde os CSVs intermediários são gravados.
            run_id: identificador único da execução (compõe o nome dos arquivos).

        Returns:
            (df_silver, df_gold, paths) — onde `paths` lista os CSVs gerados, para
            que o chamador possa limpá-los depois.
        """
        if camada_inicial not in CAMADAS_INICIAIS:
            raise ValueError(
                f"camada_inicial inválida: '{camada_inicial}'. Use uma de {CAMADAS_INICIAIS}."
            )

        temp_dir = Path(temp_dir)
        bronze_path = temp_dir / f"bronze_{run_id}.csv"
        silver_path = temp_dir / f"silver_{run_id}.csv"
        gold_path = temp_dir / f"gold_{run_id}.csv"
        paths: list[Path] = []

        logger.info(f"Iniciando pipeline a partir da camada '{camada_inicial}' (run={run_id})")

        df = df_input

        # — Bronze (só quando entrada é raw)
        if camada_inicial == "raw":
            df = self.bronze.processar(df)
            salvar_csv(df, bronze_path)
            paths.append(bronze_path)

        # — Silver (quando entrada é raw ou bronze; já-pronto quando entrada é silver)
        if camada_inicial in ("raw", "bronze"):
            df_silver, report = self.silver.processar(df)
            df_silver = self.silver.juntar_solo(df_silver)
            report.imprimir()
        else:  # silver
            df_silver = df

        salvar_csv(df_silver, silver_path)
        paths.append(silver_path)

        # — Gold (sempre)
        df_gold = self.gold.processar(df_silver)
        df_gold.to_csv(gold_path, index=False)
        logger.info(f"Gold salvo em {gold_path} ({len(df_gold)} talhões)")
        paths.append(gold_path)

        return df_silver, df_gold, paths


def executar_pipeline(
    df_input: pd.DataFrame,
    camada_inicial: str,
    temp_dir: str | Path,
    run_id: str,
) -> tuple[pd.DataFrame, pd.DataFrame, list[Path]]:
    """Atalho funcional: instancia uma `Pipeline` padrão e executa."""
    return Pipeline().executar(df_input, camada_inicial, temp_dir, run_id)
