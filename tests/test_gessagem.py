"""
Testes da regra de gessagem (Regra A.2).
Testes unitários detalhados serão implementados na Task 4.3.
"""
from rules.gessagem import calcular_necessidade_gessagem


def test_gessagem_nao_aplicavel_para_cana_soca(talhao_cana_soca_calagem):
    resultado = calcular_necessidade_gessagem(talhao_cana_soca_calagem)
    assert resultado["regra_acionada"] == "categoria_nao_formacao"


def test_gessagem_retorna_sem_dado_quando_ca2_ausente(talhao_dado_ausente):
    resultado = calcular_necessidade_gessagem(talhao_dado_ausente)
    assert resultado["orientacao"] == "SEM_DADO"


def test_gessagem_retorna_chaves_obrigatorias(talhao_gessagem_ca_baixo):
    resultado = calcular_necessidade_gessagem(talhao_gessagem_ca_baixo)
    for chave in ("orientacao", "valor_calculado", "regra_acionada", "detalhes"):
        assert chave in resultado
