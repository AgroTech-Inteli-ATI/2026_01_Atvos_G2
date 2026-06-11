"""
Testes da regra de calagem (Regra A.1).
Testes unitários detalhados serão implementados na Task 4.3.
"""
from rules.calagem import calcular_necessidade_calagem


def test_calagem_retorna_sem_dado_quando_v1_ausente(talhao_dado_ausente):
    resultado = calcular_necessidade_calagem(talhao_dado_ausente)
    assert resultado["orientacao"] == "SEM_DADO"


def test_calagem_retorna_sem_dado_para_tipo_invalido(talhao_tipo_invalido):
    resultado = calcular_necessidade_calagem(talhao_tipo_invalido)
    assert resultado["orientacao"] == "SEM_DADO"


def test_calagem_retorna_chaves_obrigatorias(talhao_calagem_dolomitico):
    resultado = calcular_necessidade_calagem(talhao_calagem_dolomitico)
    for chave in ("orientacao", "valor_calculado", "regra_acionada", "detalhes"):
        assert chave in resultado
