"""
Testes da modularização da pipeline por ponto de partida.

Cobre:
  - Camada Bronze (padronização estrutural sem descartar linhas)
  - Camada Silver (regras de qualidade)
  - Orquestrador a partir de 'silver' (pula bronze/silver) e de 'raw' (roda tudo)
"""
import pandas as pd
import pytest

from pipelines import BronzePipeline, SilverPipeline, Pipeline, CAMADAS_INICIAIS


@pytest.fixture
def df_raw():
    """Planilha bruta no formato do export ATVOS (nomes de coluna originais)."""
    return pd.DataFrame({
        "TALHAO":       ["t1 ", "T2"],
        "UNID_IND":     ["ui-a", "ui-a"],
        "DATA_PLANTIO": ["2024-01-01", "2024-02-01"],
        "AREA_HA":      [10.0, 20.0],
        "NUM":          ["100", "100"],
        "SAFRA":        ["25", "25"],
    })


# ---------------------------------------------------------------------------
# Bronze
# ---------------------------------------------------------------------------

def test_bronze_renomeia_colunas_sem_dropar_linhas(df_raw):
    df_bronze = BronzePipeline().processar(df_raw)
    # Renomeou para os nomes internos
    assert "id_talhao" in df_bronze.columns
    assert "unidade_industrial" in df_bronze.columns
    assert "TALHAO" not in df_bronze.columns
    # Estrutural: não descarta linhas
    assert len(df_bronze) == len(df_raw)


# ---------------------------------------------------------------------------
# Silver
# ---------------------------------------------------------------------------

def test_silver_aplica_regras_de_qualidade(df_raw):
    df_bronze = BronzePipeline().processar(df_raw)
    df_silver, report = SilverPipeline().processar(df_bronze)
    # id_talhao normalizado (trim + upper)
    assert set(df_silver["id_talhao"]) == {"T1", "T2"}
    # QualityReport foi produzido
    assert report.linhas_originais == len(df_bronze)


def test_silver_bloqueia_id_talhao_nulo():
    df_bronze = pd.DataFrame({
        "id_talhao":          ["X1", None],
        "unidade_industrial": ["UI", "UI"],
        "data_plantio":       ["2024-01-01", "2024-01-02"],
        "area_ha":            [10.0, 12.0],
        "safra":              ["25", "25"],
    })
    df_silver, _ = SilverPipeline().processar(df_bronze)
    assert len(df_silver) == 1
    assert df_silver.iloc[0]["id_talhao"] == "X1"


# ---------------------------------------------------------------------------
# Orquestrador
# ---------------------------------------------------------------------------

def test_camadas_iniciais_validas():
    assert CAMADAS_INICIAIS == ("raw", "bronze", "silver")


def test_pipeline_a_partir_de_silver_pula_limpeza(tmp_path):
    df_silver = pd.DataFrame({
        "id_talhao": ["A1", "A2"],
        "area_ha":   [10.0, 20.0],
        "tch_prod":  [80.0, 90.0],
    })
    _, df_gold, paths = Pipeline().executar(df_silver, "silver", tmp_path, "t_silver")
    nomes = [p.name for p in paths]
    assert len(df_gold) == 2
    # Não gera artefato bronze quando começa no silver
    assert not any("bronze" in n for n in nomes)
    assert any("silver" in n for n in nomes)
    assert any("gold" in n for n in nomes)


def test_pipeline_a_partir_de_raw_roda_todas_as_camadas(df_raw, tmp_path):
    df_silver, df_gold, paths = Pipeline().executar(df_raw, "raw", tmp_path, "t_raw")
    nomes = [p.name for p in paths]
    assert any("bronze" in n for n in nomes)
    assert any("silver" in n for n in nomes)
    assert any("gold" in n for n in nomes)
    assert len(df_gold) == len(df_silver)


def test_pipeline_camada_invalida_levanta_erro(df_raw, tmp_path):
    with pytest.raises(ValueError):
        Pipeline().executar(df_raw, "ouro", tmp_path, "t_bad")
