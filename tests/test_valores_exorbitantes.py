"""
Testes de valores exorbitantes e fronteiras numericas extraidas do manual.

O foco aqui nao e o caso feliz: estes cenarios documentam limites, entradas
fisicamente invalidas e lacunas onde o manual nao define comportamento seguro.
"""
import math

import pandas as pd
import pytest

from pipelines import GoldPipeline
from rules.calagem import calcular_necessidade_calagem
from rules.erradicacao import calcular_erradicacao
from rules.fosfatagem import calcular_necessidade_fosfatagem
from rules.gessagem import calcular_necessidade_gessagem
from rules.insumos import calcular_dose_fosfatagem
from rules.utils import campo_invalido


EPS = 0.001
FORMACAO = "Formação"


def _talhao_calagem(**overrides):
    talhao = {
        "id_talhao": "T_EDGE_CAL",
        "categoria": FORMACAO,
        "V1": 50.0,
        "CTC1": 80.0,
        "mg1": 6.0,
    }
    talhao.update(overrides)
    return talhao


def _talhao_gessagem(**overrides):
    talhao = {
        "id_talhao": "T_EDGE_GES",
        "categoria": FORMACAO,
        "ca2": 3.5,
        "al2": 8.0,
        "sb2": 10.0,
        "tipo_solo": "Argiloso",
    }
    talhao.update(overrides)
    return talhao


def _talhao_fosfatagem(**overrides):
    talhao = {
        "id_talhao": "T_EDGE_FOS",
        "categoria": FORMACAO,
        "p1": 9.0,
    }
    talhao.update(overrides)
    return talhao


def _talhao_erradicacao(**overrides):
    talhao = {
        "id_talhao": "T_EDGE_ERR",
        "categoria": "Cana Soca",
        "tch_prod": 75.0,
        "no_corte": 3,
        "sit_talhao": "Cana Soca",
    }
    talhao.update(overrides)
    return talhao


@pytest.mark.parametrize(
    "valor",
    [None, "alto", math.nan, math.inf, -math.inf, -1, True],
)
def test_campo_invalido_rejeita_tipos_e_extremos(valor):
    assert campo_invalido(valor) is True


@pytest.mark.parametrize(
    "campo, valor",
    [
        ("V1", math.inf),
        ("V1", math.nan),
        ("V1", -EPS),
        ("CTC1", -1.0),
        ("CTC1", "oitenta"),
        ("mg1", -EPS),
        ("mg1", -math.inf),
    ],
)
def test_calagem_retorna_sem_dado_para_invalidos_extremos(campo, valor):
    resultado = calcular_necessidade_calagem(_talhao_calagem(**{campo: valor}))

    assert resultado["orientacao"] == "SEM_DADO"
    assert resultado["regra_acionada"] == f"dado_ausente_{campo}"


@pytest.mark.parametrize(
    "v1, regra_prefixo, dose_esperada",
    [
        (60.0 - EPS, "calagem_necessaria_calc", None),
        (60.0, "calagem_nao_necessaria", 0.0),
        (60.0 + EPS, "calagem_nao_necessaria", 0.0),
    ],
)
def test_calagem_fronteira_saturacao_bases_60(v1, regra_prefixo, dose_esperada):
    resultado = calcular_necessidade_calagem(_talhao_calagem(V1=v1))

    assert resultado["regra_acionada"].startswith(regra_prefixo)
    if dose_esperada is not None:
        assert resultado["valor_calculado"] == dose_esperada
    else:
        assert resultado["valor_calculado"] > 0


@pytest.mark.parametrize(
    "mg1, regra_prefixo, dose_minima",
    [
        (5.0 - EPS, "calagem_necessaria_dolom", 1.0),
        (5.0, "calagem_necessaria_calc", 0.0),
        (5.0 + EPS, "calagem_necessaria_calc", 0.0),
    ],
)
def test_calagem_fronteira_magnesio_5(mg1, regra_prefixo, dose_minima):
    resultado = calcular_necessidade_calagem(_talhao_calagem(V1=50.0, mg1=mg1))

    assert resultado["regra_acionada"].startswith(regra_prefixo)
    assert resultado["valor_calculado"] >= dose_minima


def test_calagem_ctc_extremo_clampa_dose_maxima_da_pipeline():
    resultado = calcular_necessidade_calagem(
        _talhao_calagem(V1=0.0, CTC1=1e18, mg1=6.0)
    )

    assert resultado["valor_calculado"] == 4.0
    assert resultado["regra_acionada"].startswith("calagem_necessaria_calc")


@pytest.mark.parametrize(
    "ca2, al2, sb2, regra_esperada, dose_esperada",
    [
        (4.0 - EPS, 8.0, 10.0, "gessagem_ca_baixo_e_al_alto", 2100.0),
        (4.0, 8.0, 10.0, "gessagem_nao_necessaria", 0.0),
        (4.0 - EPS, 1.0, 100.0, "gessagem_nao_necessaria", 0.0),
        (5.0, 100.0, 100.0, "gessagem_nao_necessaria", 0.0),
    ],
)
def test_gessagem_exige_ca_baixo_e_saturacao_al_alta(
    ca2, al2, sb2, regra_esperada, dose_esperada
):
    resultado = calcular_necessidade_gessagem(
        _talhao_gessagem(ca2=ca2, al2=al2, sb2=sb2)
    )

    assert resultado["regra_acionada"] == regra_esperada
    assert resultado["valor_calculado"] == dose_esperada


@pytest.mark.parametrize(
    "campo, valor",
    [
        ("ca2", -EPS),
        ("ca2", math.inf),
        ("al2", -EPS),
        ("al2", -math.inf),
        ("sb2", -EPS),
        ("sb2", "dez"),
    ],
)
def test_gessagem_retorna_sem_dado_para_invalidos_extremos(campo, valor):
    resultado = calcular_necessidade_gessagem(_talhao_gessagem(**{campo: valor}))

    assert resultado["orientacao"] == "SEM_DADO"
    assert resultado["regra_acionada"] == f"dado_ausente_{campo}"


@pytest.mark.parametrize(
    "p1, regra_esperada, dose_esperada",
    [
        (6.0 - EPS, "fosfatagem_p_muito_baixo", 120.0),
        (6.0, "fosfatagem_p_baixo", 80.0),
        (12.0 - EPS, "fosfatagem_p_baixo", 80.0),
        (12.0, "fosfatagem_p_medio", 40.0),
        (25.0 - EPS, "fosfatagem_p_medio", 40.0),
        (25.0, "fosfatagem_p_suficiente", 0.0),
        (1e18, "fosfatagem_p_suficiente", 0.0),
    ],
)
def test_fosfatagem_fronteiras_e_valor_muito_alto(p1, regra_esperada, dose_esperada):
    resultado = calcular_necessidade_fosfatagem(_talhao_fosfatagem(p1=p1))

    assert resultado["regra_acionada"] == regra_esperada
    assert resultado["valor_calculado"] == dose_esperada


@pytest.mark.parametrize("p1", [-EPS, math.inf, -math.inf, math.nan, "baixo"])
def test_fosfatagem_retorna_sem_dado_para_invalidos_extremos(p1):
    resultado = calcular_necessidade_fosfatagem(_talhao_fosfatagem(p1=p1))

    assert resultado["orientacao"] == "SEM_DADO"
    assert resultado["regra_acionada"] == "dado_ausente_p1"


@pytest.mark.parametrize(
    "tch_prod, no_corte, regra_esperada, reforma_esperada",
    [
        (55.0 - EPS, 3, "reforma_tch_baixo_corte_maduro", True),
        (55.0, 3, "sem_reforma_talhao_produtivo", False),
        (75.0, 6, "reforma_preventiva_longevidade", True),
        (75.0, 8, "reforma_longevidade_maxima", True),
        (1e18, 1e18, "reforma_longevidade_maxima", True),
    ],
)
def test_erradicacao_fronteiras_tch_e_cortes(
    tch_prod, no_corte, regra_esperada, reforma_esperada
):
    resultado = calcular_erradicacao(
        _talhao_erradicacao(tch_prod=tch_prod, no_corte=no_corte)
    )

    assert resultado["regra_acionada"] == regra_esperada
    assert resultado["detalhes"]["reforma_recomendada"] is reforma_esperada


@pytest.mark.parametrize(
    "campo, valor",
    [
        ("tch_prod", -EPS),
        ("tch_prod", math.inf),
        ("no_corte", -1),
        ("no_corte", math.nan),
        ("no_corte", -math.inf),
    ],
)
def test_erradicacao_retorna_sem_dado_para_invalidos_extremos(campo, valor):
    resultado = calcular_erradicacao(_talhao_erradicacao(**{campo: valor}))

    assert resultado["orientacao"] == "SEM_DADO"
    assert resultado["regra_acionada"] == f"dado_ausente_{campo}"


@pytest.mark.parametrize(
    "p_disponivel, tchan_estimado, regra_esperada",
    [
        (6.0 - EPS, 80.0, "insumo_fosfato_muito_baixo"),
        (6.0, 80.0, "insumo_fosfato_baixo"),
        (12.0, 80.0, "insumo_fosfato_medio"),
        (25.0, 80.0, "insumo_fosfato_nao_necessario"),
    ],
)
def test_insumo_fosfato_fronteiras_p_disponivel(
    p_disponivel, tchan_estimado, regra_esperada
):
    resultado = calcular_dose_fosfatagem(
        p_disponivel=p_disponivel,
        textura_solo="Argiloso",
        tchan_estimado=tchan_estimado,
    )

    assert resultado["regra_acionada"] == regra_esperada


@pytest.mark.parametrize(
    "p_disponivel, tchan_estimado, regra_esperada",
    [
        (-EPS, 80.0, "dado_ausente_p_disponivel"),
        (math.inf, 80.0, "dado_ausente_p_disponivel"),
        (4.5, -EPS, "dado_ausente_tchan_estimado"),
        (4.5, math.inf, "dado_ausente_tchan_estimado"),
    ],
)
def test_insumo_fosfato_retorna_sem_dado_para_invalidos_extremos(
    p_disponivel, tchan_estimado, regra_esperada
):
    resultado = calcular_dose_fosfatagem(
        p_disponivel=p_disponivel,
        textura_solo="Argiloso",
        tchan_estimado=tchan_estimado,
    )

    assert resultado["orientacao"] == "SEM_DADO"
    assert resultado["regra_acionada"] == regra_esperada


@pytest.mark.xfail(
    reason=(
        "GAP DE REGRA: o manual nao define limite superior de TCH estimado; "
        "a pipeline ainda nao tem flag fora de faixa para 1e18."
    )
)
def test_insumo_fosfato_tchan_overflow_extremo_deveria_ser_sinalizado():
    resultado = calcular_dose_fosfatagem(
        p_disponivel=4.5,
        textura_solo="Argiloso",
        tchan_estimado=1e18,
    )

    assert resultado["orientacao"] == "SEM_DADO"


@pytest.mark.parametrize("area_ha", [0.0, -1.0, math.inf, -math.inf, "vinte", None])
def test_gold_pipeline_nao_calcula_quantidade_total_com_area_invalida(area_ha):
    gold = GoldPipeline()
    df = pd.DataFrame([
        {
            "id_talhao": "T_AREA_EDGE",
            "categoria": FORMACAO,
            "p1": 4.5,
            "area_ha": area_ha,
            "tch_prod": 80.0,
            "tipo_solo": "Argiloso",
        }
    ])

    output = gold.processar(df)
    row = output.iloc[0]

    assert row["fosfato_dose_kg_ha"] is not None
    assert pd.isna(row["fosfato_quantidade_total_kg"])
