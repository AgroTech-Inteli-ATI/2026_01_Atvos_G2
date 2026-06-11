"""
Testes de integração e resiliência do pipeline_gold.
Cobre: dados inválidos, id ausente, tipos errados, colunas faltando.
"""
import pandas as pd
import pytest

import pipeline_gold
from pipeline_gold import processar_talhao


# ---------------------------------------------------------------------------
# Cenários de falha — processar_talhao
# ---------------------------------------------------------------------------

def test_talhao_sem_id_talhao_e_pulado(talhao_sem_id):
    resultado = processar_talhao(talhao_sem_id)
    assert resultado is None


def test_talhao_com_id_talhao_nulo_e_pulado():
    resultado = processar_talhao({"id_talhao": None, "categoria": "Formação"})
    assert resultado is None


def test_talhao_com_tipo_invalido_nao_levanta_excecao(talhao_tipo_invalido):
    # Tipos inválidos devem resultar em SEM_DADO nas regras, nunca em exceção
    resultado = processar_talhao(talhao_tipo_invalido)
    assert resultado is not None
    assert resultado["calagem"]["orientacao"] == "SEM_DADO"


def test_talhao_sem_colunas_de_solo_nao_levanta_excecao():
    # Colunas de solo completamente ausentes (arquivo sem join com solo)
    talhao = {"id_talhao": "T_SEM_SOLO", "categoria": "Formação"}
    resultado = processar_talhao(talhao)
    assert resultado is not None
    assert resultado["calagem"]["orientacao"] == "SEM_DADO"


# ---------------------------------------------------------------------------
# Pipeline completo — CSV único com insumos pivotados
# ---------------------------------------------------------------------------

def test_pipeline_processa_dataframe_valido(tmp_path):
    csv_entrada = tmp_path / "silver.csv"
    csv_saida = tmp_path / "gold.csv"

    df = pd.DataFrame([{
        "id_talhao": "T001",
        "categoria": "Formação",
        "V1": 42.0, "CTC1": 90.0, "mg1": 3.5,
        "ca2": 2.5, "al2": 5.0, "sb2": 15.0,
        "p1": 4.5, "area_ha": 25.0,
        "tch_prod": 80.0, "no_corte": 0,
        "sit_talhao": "Cana Planta", "tipo_solo": "Argiloso",
    }])
    df.to_csv(csv_entrada, index=False)

    output = pipeline_gold.processar_pipeline_gold(str(csv_entrada), str(csv_saida))

    assert len(output) == 1
    assert output.iloc[0]["id_talhao"] == "T001"
    assert csv_saida.exists()


def test_pipeline_gold_contem_colunas_insumos_pivotadas(tmp_path):
    csv_entrada = tmp_path / "silver.csv"

    df = pd.DataFrame([{
        "id_talhao": "T001",
        "categoria": "Formação",
        "p1": 4.5, "area_ha": 25.0, "tch_prod": 80.0,
        "tipo_solo": "Argiloso",
    }])
    df.to_csv(csv_entrada, index=False)

    output = pipeline_gold.processar_pipeline_gold(
        str(csv_entrada), str(tmp_path / "gold.csv")
    )

    colunas_esperadas = [
        "fosfato_insumo", "fosfato_dose_kg_ha", "fosfato_quantidade_total_kg",
        "dessecacao_insumo", "dessecacao_dose_kg_ha", "dessecacao_dose_l_ha",
        "dessecacao_quantidade_total_kg",
    ]
    for col in colunas_esperadas:
        assert col in output.columns, f"Coluna ausente no Gold: {col}"


def test_pipeline_fosfato_calcula_quantidade_total(tmp_path):
    csv_entrada = tmp_path / "silver.csv"

    df = pd.DataFrame([{
        "id_talhao": "T001", "categoria": "Formação",
        "p1": 4.5, "area_ha": 20.0, "tch_prod": 80.0, "tipo_solo": "Argiloso",
    }])
    df.to_csv(csv_entrada, index=False)

    output = pipeline_gold.processar_pipeline_gold(
        str(csv_entrada), str(tmp_path / "gold.csv")
    )
    row = output.iloc[0]
    assert row["fosfato_dose_kg_ha"] is not None
    assert row["fosfato_quantidade_total_kg"] == pytest.approx(
        row["fosfato_dose_kg_ha"] * 20.0, abs=0.1
    )


def test_pipeline_pula_registros_sem_id_e_continua(tmp_path):
    csv_entrada = tmp_path / "silver.csv"
    csv_saida = tmp_path / "gold.csv"

    df = pd.DataFrame([
        {"id_talhao": None, "categoria": "Formação", "V1": 40.0, "CTC1": 90.0, "mg1": 5.0},
        {"id_talhao": "T002", "categoria": "Cana Soca", "tch_prod": 60.0, "no_corte": 3, "sit_talhao": "Cana Soca"},
    ])
    df.to_csv(csv_entrada, index=False)

    output = pipeline_gold.processar_pipeline_gold(str(csv_entrada), str(csv_saida))
    assert len(output) == 1
    assert output.iloc[0]["id_talhao"] == "T002"


def test_pipeline_arquivo_nao_encontrado_levanta_file_not_found(tmp_path):
    with pytest.raises(FileNotFoundError):
        pipeline_gold.processar_pipeline_gold(
            str(tmp_path / "inexistente.csv"),
            str(tmp_path / "gold.csv"),
        )
