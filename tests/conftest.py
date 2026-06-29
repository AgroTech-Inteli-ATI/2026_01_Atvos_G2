import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


# ---------------------------------------------------------------------------
# Fixtures — calagem
# ---------------------------------------------------------------------------

@pytest.fixture
def talhao_calagem_dolomitico():
    """Cana planta com Mg abaixo do limiar (< 5): exige calcário dolomítico."""
    return {
        "id_talhao": "T001",
        "categoria": "Formação",
        "V1": 42.0,
        "CTC1": 90.0,
        "mg1": 3.5,
    }


@pytest.fixture
def talhao_calagem_calcítico():
    """Cana planta com Mg suficiente: calcítico ou dolomítico."""
    return {
        "id_talhao": "T002",
        "categoria": "Formação",
        "V1": 50.0,
        "CTC1": 80.0,
        "mg1": 7.0,
    }


@pytest.fixture
def talhao_calagem_nao_necessaria():
    """V% já acima do alvo (60%): sem calagem."""
    return {
        "id_talhao": "T003",
        "categoria": "Formação",
        "V1": 65.0,
        "CTC1": 80.0,
        "mg1": 6.0,
    }


@pytest.fixture
def talhao_cana_soca_calagem():
    """Cana soca com V% baixo: dose reduzida a 50% (aplicação superficial)."""
    return {
        "id_talhao": "T004",
        "categoria": "Cana Soca",
        "V1": 40.0,
        "CTC1": 100.0,
        "mg1": 6.0,
    }


# ---------------------------------------------------------------------------
# Fixtures — gessagem
# ---------------------------------------------------------------------------

@pytest.fixture
def talhao_gessagem_ca_baixo():
    """Ca subsuperficial < 4 mmolc/dm³ em cana planta: gessagem obrigatória."""
    return {
        "id_talhao": "T010",
        "categoria": "Formação",
        "ca2": 2.5,
        "al2": 5.0,
        "sb2": 15.0,
        "tipo_solo": "Argiloso",
    }


@pytest.fixture
def talhao_gessagem_al_alto():
    """Saturação de Al > 40% em cana planta: gessagem obrigatória."""
    return {
        "id_talhao": "T011",
        "categoria": "Formação",
        "ca2": 6.0,
        "al2": 10.0,
        "sb2": 10.0,
        "tipo_solo": "Médio",
    }


@pytest.fixture
def talhao_gessagem_nao_necessaria():
    """Ca e Al dentro dos limites: sem gessagem."""
    return {
        "id_talhao": "T012",
        "categoria": "Formação",
        "ca2": 5.0,
        "al2": 3.0,
        "sb2": 20.0,
        "tipo_solo": "Muito Argiloso",
    }


@pytest.fixture
def talhao_solo_tipo_desconhecido():
    """Solo não mapeado na tabela de argila: usa fallback 'A Definir'."""
    return {
        "id_talhao": "T013",
        "categoria": "Formação",
        "ca2": 2.0,
        "al2": 8.0,
        "sb2": 12.0,
        "tipo_solo": "Solo Exótico Não Mapeado",
    }


# ---------------------------------------------------------------------------
# Fixtures — fosfatagem (insumos)
# ---------------------------------------------------------------------------

@pytest.fixture
def talhao_p_muito_baixo():
    return {"id_talhao": "T020", "categoria": "Formação", "p1": 4.5}


@pytest.fixture
def talhao_p_baixo():
    return {"id_talhao": "T021", "categoria": "Formação", "p1": 9.0}


@pytest.fixture
def talhao_p_medio():
    return {"id_talhao": "T022", "categoria": "Formação", "p1": 18.0}


@pytest.fixture
def talhao_p_suficiente():
    return {"id_talhao": "T023", "categoria": "Formação", "p1": 30.0}


# ---------------------------------------------------------------------------
# Fixtures — erradicação
# ---------------------------------------------------------------------------

@pytest.fixture
def talhao_longevidade_maxima():
    """8+ cortes: reforma obrigatória independente de TCH."""
    return {
        "id_talhao": "T030",
        "categoria": "Cana Soca",
        "tch_prod": 60.0,
        "no_corte": 9,
        "sit_talhao": "Fechado",
    }


@pytest.fixture
def talhao_tch_baixo_corte_maduro():
    """TCH < 55 com 3+ cortes: reforma de alta prioridade."""
    return {
        "id_talhao": "T031",
        "categoria": "Cana Soca",
        "tch_prod": 48.0,
        "no_corte": 4,
        "sit_talhao": "Cana Soca",
    }


@pytest.fixture
def talhao_produtivo():
    """TCH ok, poucos cortes: continuar ciclo."""
    return {
        "id_talhao": "T032",
        "categoria": "Cana Soca",
        "tch_prod": 75.0,
        "no_corte": 3,
        "sit_talhao": "Cana Soca",
    }


# ---------------------------------------------------------------------------
# Fixtures — dados inválidos / ausentes (compartilhadas entre módulos)
# ---------------------------------------------------------------------------

@pytest.fixture
def talhao_dado_ausente():
    """Todos os campos de solo nulos."""
    return {
        "id_talhao": "T050",
        "categoria": "Formação",
        "V1": None,
        "CTC1": None,
        "mg1": None,
        "ca2": None,
        "al2": None,
        "sb2": None,
        "p1": None,
    }


@pytest.fixture
def talhao_tipo_invalido():
    """V1 recebe string em vez de float."""
    return {
        "id_talhao": "T051",
        "categoria": "Formação",
        "V1": "alto",
        "CTC1": 90.0,
        "mg1": 3.5,
    }


@pytest.fixture
def talhao_sem_id():
    """Registro sem id_talhao."""
    return {
        "categoria": "Formação",
        "V1": 42.0,
        "CTC1": 90.0,
        "mg1": 3.5,
    }
