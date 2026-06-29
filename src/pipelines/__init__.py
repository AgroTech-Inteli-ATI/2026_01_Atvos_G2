"""
Pipelines do Motor de Regras Agronômicas (padrão medallion).

Cada camada é uma classe em seu próprio arquivo:
    - BronzePipeline  (bronze_pipeline.py)  — padronização estrutural
    - SilverPipeline  (silver_pipeline.py)  — regras de qualidade + join com solo
    - GoldPipeline    (gold_pipeline.py)    — aplicação das regras agronômicas

A classe `Pipeline` (pipeline.py) orquestra as três a partir de uma camada inicial.
"""
from .bronze_pipeline import BronzePipeline, COLUNAS_RENAME
from .silver_pipeline import SilverPipeline, QualityReport
from .gold_pipeline import GoldPipeline
from .pipeline import Pipeline, executar_pipeline, CAMADAS_INICIAIS

__all__ = [
    "BronzePipeline",
    "SilverPipeline",
    "GoldPipeline",
    "Pipeline",
    "executar_pipeline",
    "CAMADAS_INICIAIS",
    "QualityReport",
    "COLUNAS_RENAME",
]
