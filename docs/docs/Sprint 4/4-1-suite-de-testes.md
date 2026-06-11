---
sidebar_position: 2
title: "4.1 — Suite de Testes (pytest)"
---

# Tarefa 4.1 — Configuração da Suite de Testes

## Objetivo

Estruturar a suite de testes automatizados com pytest, com fixtures reutilizáveis que simulam dados de talhões para garantir que os módulos de regras se comportam corretamente em todos os cenários — dados válidos, dados ausentes e tipos inválidos.

---

## Estrutura de Arquivos Criada

```
tests/
├── conftest.py              # fixtures compartilhadas entre todos os testes
├── test_calagem.py          # 3 testes da regra de calagem
├── test_gessagem.py         # 3 testes da regra de gessagem
├── test_insumos.py          # 3 testes da regra de fosfatagem (fosfatagem.py)
└── test_pipeline_gold.py    # 9 testes de integração do pipeline
```

> **Nota sobre nomenclatura:** O arquivo `test_insumos.py` testa a função `calcular_necessidade_fosfatagem` de `fosfatagem.py`. Na Task 4.3 (próxima sprint) ele será expandido para cobrir também as funções de `insumos.py`.

---

## Fixtures em `tests/conftest.py`

O `conftest.py` centraliza 13 fixtures que são importadas automaticamente pelo pytest em todos os arquivos de teste.

### Fixtures de calagem

```python
@pytest.fixture
def talhao_calagem_dolomitico():
    """Cana planta com Mg < 5 mmolc/dm³ — exige calcário dolomítico."""
    return {"id_talhao": "T001", "categoria": "Formação",
            "V1": 42.0, "CTC1": 90.0, "mg1": 3.5}

@pytest.fixture
def talhao_calagem_calcítico():
    """Cana planta com Mg suficiente — calcítico ou dolomítico."""
    return {"id_talhao": "T002", "categoria": "Formação",
            "V1": 50.0, "CTC1": 80.0, "mg1": 7.0}

@pytest.fixture
def talhao_calagem_nao_necessaria():
    """V% já acima de 60% — sem calagem."""
    return {"id_talhao": "T003", "categoria": "Formação",
            "V1": 65.0, "CTC1": 80.0, "mg1": 6.0}

@pytest.fixture
def talhao_cana_soca_calagem():
    """Cana soca com V% baixo — dose reduzida a 50% (aplicação superficial)."""
    return {"id_talhao": "T004", "categoria": "Cana Soca",
            "V1": 40.0, "CTC1": 100.0, "mg1": 6.0}
```

### Fixtures de gessagem

```python
@pytest.fixture
def talhao_gessagem_ca_baixo():
    """Ca subsuperficial < 4 mmolc/dm³ — gessagem obrigatória."""
    return {"id_talhao": "T010", "categoria": "Formação",
            "ca2": 2.5, "al2": 5.0, "sb2": 15.0, "tipo_solo": "Argiloso"}

@pytest.fixture
def talhao_gessagem_al_alto():
    """Saturação de Al > 40% — gessagem obrigatória."""
    return {"id_talhao": "T011", "categoria": "Formação",
            "ca2": 6.0, "al2": 10.0, "sb2": 10.0, "tipo_solo": "Médio"}

@pytest.fixture
def talhao_gessagem_nao_necessaria():
    """Ca e Al dentro dos limites — sem gessagem."""
    return {"id_talhao": "T012", "categoria": "Formação",
            "ca2": 5.0, "al2": 3.0, "sb2": 20.0, "tipo_solo": "Muito Argiloso"}
```

### Fixtures de fosfatagem (insumos)

```python
@pytest.fixture
def talhao_p_muito_baixo():
    return {"id_talhao": "T020", "categoria": "Formação", "p1": 4.5}

@pytest.fixture
def talhao_p_baixo():
    return {"id_talhao": "T021", "categoria": "Formação", "p1": 9.0}

@pytest.fixture
def talhao_p_suficiente():
    return {"id_talhao": "T023", "categoria": "Formação", "p1": 30.0}
```

### Fixtures compartilhadas — dados inválidos

```python
@pytest.fixture
def talhao_dado_ausente():
    """Todos os campos de solo nulos."""
    return {"id_talhao": "T050", "categoria": "Formação",
            "V1": None, "CTC1": None, "mg1": None,
            "ca2": None, "al2": None, "sb2": None, "p1": None}

@pytest.fixture
def talhao_tipo_invalido():
    """V1 recebe string em vez de float."""
    return {"id_talhao": "T051", "categoria": "Formação",
            "V1": "alto", "CTC1": 90.0, "mg1": 3.5}

@pytest.fixture
def talhao_sem_id():
    """Registro sem id_talhao."""
    return {"categoria": "Formação", "V1": 42.0, "CTC1": 90.0, "mg1": 3.5}
```

---

## Testes por Arquivo

### `test_calagem.py`

| Teste | O que verifica |
|---|---|
| `test_calagem_retorna_sem_dado_quando_v1_ausente` | `V1 = None` → `orientacao == "SEM_DADO"` |
| `test_calagem_retorna_sem_dado_para_tipo_invalido` | `V1 = "alto"` → `orientacao == "SEM_DADO"` |
| `test_calagem_retorna_chaves_obrigatorias` | retorno sempre contém `orientacao`, `valor_calculado`, `regra_acionada`, `detalhes` |

### `test_gessagem.py`

| Teste | O que verifica |
|---|---|
| `test_gessagem_nao_aplicavel_para_cana_soca` | categoria ≠ "Formação" → `regra_acionada == "categoria_nao_formacao"` |
| `test_gessagem_retorna_sem_dado_quando_ca2_ausente` | `ca2 = None` → `orientacao == "SEM_DADO"` |
| `test_gessagem_retorna_chaves_obrigatorias` | retorno contém as 4 chaves obrigatórias |

### `test_insumos.py`

| Teste | O que verifica |
|---|---|
| `test_fosfatagem_nao_aplicavel_para_cana_soca` | categoria ≠ "Formação" → `regra_acionada == "categoria_nao_formacao"` |
| `test_fosfatagem_retorna_sem_dado_quando_p1_ausente` | `p1 = None` → `orientacao == "SEM_DADO"` |
| `test_fosfatagem_retorna_chaves_obrigatorias` | retorno contém as 4 chaves obrigatórias |

### `test_pipeline_gold.py`

| Teste | O que verifica |
|---|---|
| `test_talhao_sem_id_talhao_e_pulado` | `processar_talhao` retorna `None` quando id está ausente |
| `test_talhao_com_id_talhao_nulo_e_pulado` | idem para `id_talhao = None` |
| `test_talhao_com_tipo_invalido_nao_levanta_excecao` | tipo errado → `SEM_DADO`, sem exception |
| `test_talhao_sem_colunas_de_solo_nao_levanta_excecao` | todas as colunas de solo ausentes → `SEM_DADO` |
| `test_pipeline_processa_dataframe_valido` | pipeline lê CSV, processa, grava saída, retorna 1 linha |
| `test_pipeline_gold_contem_colunas_insumos_pivotadas` | Gold contém `fosfato_*` e `dessecacao_*` |
| `test_pipeline_fosfato_calcula_quantidade_total` | `fosfato_quantidade_total_kg == fosfato_dose_kg_ha × area_ha` |
| `test_pipeline_pula_registros_sem_id_e_continua` | pipeline com 2 rows (1 sem id) → só 1 no output |
| `test_pipeline_arquivo_nao_encontrado_levanta_file_not_found` | `FileNotFoundError` propagado corretamente |

---

## Resultado da Coleta

```
pytest tests/ --collect-only -q

tests/test_calagem.py::test_calagem_retorna_sem_dado_quando_v1_ausente
tests/test_calagem.py::test_calagem_retorna_sem_dado_para_tipo_invalido
tests/test_calagem.py::test_calagem_retorna_chaves_obrigatorias
tests/test_gessagem.py::test_gessagem_nao_aplicavel_para_cana_soca
tests/test_gessagem.py::test_gessagem_retorna_sem_dado_quando_ca2_ausente
tests/test_gessagem.py::test_gessagem_retorna_chaves_obrigatorias
tests/test_insumos.py::test_fosfatagem_nao_aplicavel_para_cana_soca
tests/test_insumos.py::test_fosfatagem_retorna_sem_dado_quando_p1_ausente
tests/test_insumos.py::test_fosfatagem_retorna_chaves_obrigatorias
tests/test_pipeline_gold.py::test_talhao_sem_id_talhao_e_pulado
tests/test_pipeline_gold.py::test_talhao_com_id_talhao_nulo_e_pulado
tests/test_pipeline_gold.py::test_talhao_com_tipo_invalido_nao_levanta_excecao
tests/test_pipeline_gold.py::test_talhao_sem_colunas_de_solo_nao_levanta_excecao
tests/test_pipeline_gold.py::test_pipeline_processa_dataframe_valido
tests/test_pipeline_gold.py::test_pipeline_gold_contem_colunas_insumos_pivotadas
tests/test_pipeline_gold.py::test_pipeline_fosfato_calcula_quantidade_total
tests/test_pipeline_gold.py::test_pipeline_pula_registros_sem_id_e_continua
tests/test_pipeline_gold.py::test_pipeline_arquivo_nao_encontrado_levanta_file_not_found

18 tests collected in 0.23s
```

## Execução Completa

```
pytest tests/ -v

18 passed in 0.31s
```

---

## Critérios de Aceite

| Critério | Resultado |
|---|---|
| `pytest --collect-only` lista testes sem erros de importação | ✅ 18 testes coletados |
| Fixtures reutilizáveis em `conftest.py` | ✅ 13 fixtures usadas em 4 arquivos |
| Fixtures de dado ausente e tipo inválido presentes | ✅ `talhao_dado_ausente`, `talhao_tipo_invalido`, `talhao_sem_id` |
| `pytest tests/` passa 100% | ✅ 18/18 |
