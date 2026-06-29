"""
Testes da regra de fosfatagem (Regra A.3 — insumos de solo).
Testes unitários detalhados serão implementados na Task 4.3.
"""
from rules.fosfatagem import calcular_necessidade_fosfatagem


def test_fosfatagem_nao_aplicavel_para_cana_soca(talhao_cana_soca_calagem):
    resultado = calcular_necessidade_fosfatagem(talhao_cana_soca_calagem)
    assert resultado["regra_acionada"] == "categoria_nao_formacao"


def test_fosfatagem_retorna_sem_dado_quando_p1_ausente(talhao_dado_ausente):
    resultado = calcular_necessidade_fosfatagem(talhao_dado_ausente)
    assert resultado["orientacao"] == "SEM_DADO"


def test_fosfatagem_retorna_chaves_obrigatorias(talhao_p_muito_baixo):
    resultado = calcular_necessidade_fosfatagem(talhao_p_muito_baixo)
    for chave in ("orientacao", "valor_calculado", "regra_acionada", "detalhes"):
        assert chave in resultado
