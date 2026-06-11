---
sidebar_position: 3
title: "4.2 — Resiliência do Pipeline"
---

# Tarefa 4.2 — Resiliência a Dados Inválidos

## Objetivo

Garantir que o pipeline Gold não quebre quando encontrar dados inválidos, ausentes ou inesperados. O comportamento implementado é: **logar o erro + pular o talhão problemático + continuar processando os demais**.

---

## Contexto: Estado Anterior

Antes desta tarefa, os módulos de regras estavam em estado de stub:

| Arquivo | Estado anterior | Problema |
|---|---|---|
| `src/rules/calagem.py` | Função com `pass` e import dentro do corpo | Sempre retornava `None` |
| `src/rules/gessagem.py` | Retornava `{"orientacao": "PENDENTE"}` | Nenhuma lógica executada |
| `src/rules/fosfatagem.py` | Retornava `{"orientacao": "PENDENTE"}` | Nenhuma lógica executada |
| `src/rules/erradicacao.py` | Retornava `{"orientacao": "PENDENTE"}` | Nenhuma lógica executada |
| `src/processing/rules.py` | Lógica real presente mas em funções aninhadas nunca chamadas | Código morto |
| `src/pipeline_gold.py` | Sem try/except, sem validação de id | Qualquer erro quebrava toda a execução |

---

## Correções Implementadas

### 1. Módulos de regras reescritos

Os quatro arquivos de regras foram reescritos usando a lógica completa do pseudocódigo (Sprint 2) e os helpers de `utils.py`:

```python
# src/rules/utils.py — helpers reutilizados em todos os módulos
def campo_invalido(valor):
    """Retorna True para None, NaN, ou qualquer não-numérico."""
    if valor is None: return True
    if isinstance(valor, float) and math.isnan(valor): return True
    if not isinstance(valor, (int, float)): return True
    return False

def sem_dado(regra_acionada):
    return {"orientacao": "SEM_DADO", "valor_calculado": None,
            "regra_acionada": regra_acionada}
```

A função `campo_invalido` cobre os três cenários de dado inválido:
- `None` (campo ausente)
- `NaN` (pandas representa nulos numéricos como float NaN)
- String em vez de número (ex: `"alto"` em vez de `5.2`)

### 2. Pipeline com isolamento por talhão

```python
def _id_ausente(id_talhao) -> bool:
    if id_talhao is None: return True
    if isinstance(id_talhao, float) and math.isnan(id_talhao): return True
    if str(id_talhao).strip() in ("", "nan", "None"): return True
    return False


def processar_talhao(talhao: dict) -> dict | None:
    id_talhao = talhao.get("id_talhao")

    if _id_ausente(id_talhao):
        logger.error(f"Talhão sem id_talhao válido — registro pulado: {talhao}")
        return None

    try:
        erradicacao_result = calcular_erradicacao(talhao)
        insumos = _calcular_insumos(talhao, erradicacao_result)
        return {
            "id_talhao": id_talhao,
            "calagem": calcular_necessidade_calagem(talhao),
            ...
        }
    except Exception as exc:
        logger.error(f"Erro inesperado ao processar talhão '{id_talhao}': {exc}")
        return None
```

O loop principal filtra os `None` e reporta o total ao final:

```python
resultados = []
erros = 0
for _, row in df.iterrows():
    resultado = processar_talhao(row.to_dict())
    if resultado is not None:
        resultados.append(resultado)
    else:
        erros += 1

logger.info(f"Pipeline Gold: {len(resultados)} registros processados, "
            f"{erros} erro(s) ignorado(s).")
```

### 3. Leitura de arquivo com tratamento explícito

```python
try:
    df = pd.read_csv(input_path)
except FileNotFoundError:
    logger.error(f"Arquivo de entrada não encontrado: {input_path}")
    raise  # re-levanta para o chamador tratar
except Exception as exc:
    logger.error(f"Erro ao ler arquivo de entrada '{input_path}': {exc}")
    raise
```

---

## Cenários de Falha Cobertos

| # | Cenário | Como é tratado | Teste |
|---|---|---|---|
| F1 | `id_talhao` ausente (campo não existe no dict) | `_id_ausente()` detecta → log ERROR + `None` | `test_talhao_sem_id_talhao_e_pulado` |
| F2 | `id_talhao = None` (campo existe mas é nulo) | `_id_ausente()` detecta → log ERROR + `None` | `test_talhao_com_id_talhao_nulo_e_pulado` |
| F3 | Tipo de dado errado (`V1 = "alto"`) | `campo_invalido()` detecta string → `SEM_DADO` sem exception | `test_talhao_com_tipo_invalido_nao_levanta_excecao` |
| F4 | Coluna inteira ausente (arquivo sem join de solo) | `.get()` retorna `None` → `campo_invalido()` → `SEM_DADO` | `test_talhao_sem_colunas_de_solo_nao_levanta_excecao` |
| F5 | Arquivo CSV não encontrado | `FileNotFoundError` logado e re-levantado | `test_pipeline_arquivo_nao_encontrado_levanta_file_not_found` |
| F6 | Pipeline com registros mistos (válidos + inválidos) | Válidos processados, inválidos pulados, contagem reportada | `test_pipeline_pula_registros_sem_id_e_continua` |

---

## Log Real de Execução

Simulação do cenário F6 (1 registro sem id + 1 válido):

```
2026-06-11 ERROR    pipeline_gold — Talhão sem id_talhao válido — registro pulado:
    {'id_talhao': nan, 'categoria': 'Formação', 'V1': 40.0, 'CTC1': 90.0, 'mg1': 5.0, ...}
2026-06-11 INFO     pipeline_gold — Pipeline Gold: 1 registros processados, 1 erro(s) ignorado(s).
2026-06-11 INFO     pipeline_gold — Gold salvo em /tmp/.../gold.csv (1 talhões)
```

---

## Critérios de Aceite

| Critério | Resultado |
|---|---|
| Todos os 6 cenários cobertos por testes | ✅ |
| Pipeline não lança exceção não tratada em nenhum cenário | ✅ |
| `campo_invalido()` cobre `None`, `NaN` e tipos não numéricos | ✅ |
| Contagem de talhões ignorados reportada no log ao final | ✅ |
| `pytest tests/test_pipeline_gold.py` passa 100% | ✅ 9/9 |
