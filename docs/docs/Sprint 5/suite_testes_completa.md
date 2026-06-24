---
sidebar_position: 4
title: "5.3 - Suite Completa de Testes"
---

# Tarefa 5.3 - Suite Completa de Testes

## Objetivo

Documentar a cobertura completa da pasta `tests/`, explicando o papel de cada arquivo, quais comportamentos da pipeline estão protegidos e como interpretar o resultado atual da execucao. Esta secao é uma continuação direta da documentação da seção 4.1 da Sprint 4, que apresentou a configuração inicial da suite pytest.

Esta pagina complementa a documentacao da tarefa 5.2. A 5.2 aprofunda os testes de valores exorbitantes; esta pagina registra a suite inteira.

---

## Visao Geral da Suite

A pasta `tests/` contem testes unitarios de regras, testes de integracao da camada Gold, testes da pipeline modular e testes parametrizados de valores extremos.

```text
tests/
|-- conftest.py
|-- test_calagem.py
|-- test_gessagem.py
|-- test_insumos.py
|-- test_pipeline_gold.py
|-- test_pipeline_modular.py
`-- test_valores_exorbitantes.py
```

Resultado de coleta:

```text
pytest tests/ --collect-only -q
93 tests collected
```

Resultado esperado da execucao completa:

```text
92 passed, 1 xfailed, 3 warnings
```

---

## Resumo por Arquivo

| Arquivo | Quantidade coletada | Tipo de teste | Responsabilidade |
|---|---:|---|---|
| `conftest.py` | N/A | Fixtures | Dados simulados reutilizaveis para todos os testes |
| `test_calagem.py` | 3 | Unitario | Resiliencia basica da regra de calagem |
| `test_gessagem.py` | 3 | Unitario | Resiliencia basica da regra de gessagem |
| `test_insumos.py` | 3 | Unitario | Regra de fosfatagem de solo, apesar do nome do arquivo |
| `test_pipeline_gold.py` | 9 | Integracao | GoldPipeline com CSV temporario, registros invalidos e insumos pivotados |
| `test_pipeline_modular.py` | 7 | Integracao/arquitetura | Bronze, Silver e orquestradora `Pipeline` |
| `test_valores_exorbitantes.py` | 68 | Parametrizado/borda | Fronteiras, valores extremos e gap de regra |

---

## `conftest.py` - Fixtures Compartilhadas

O `conftest.py` centraliza os dados de entrada usados pelos demais testes. O pytest carrega essas fixtures automaticamente, sem necessidade de import manual nos arquivos de teste.

As fixtures cobrem:

| Grupo | Exemplos | Uso |
|---|---|---|
| Calagem | `talhao_calagem_dolomitico`, `talhao_calagem_calcitico`, `talhao_calagem_nao_necessaria` | Simular V%, CTC e Mg em diferentes faixas |
| Gessagem | `talhao_gessagem_ca_baixo`, `talhao_gessagem_al_alto`, `talhao_gessagem_nao_necessaria` | Simular Ca, Al, SB e tipo de solo |
| Fosfatagem | `talhao_p_muito_baixo`, `talhao_p_baixo`, `talhao_p_medio`, `talhao_p_suficiente` | Simular fosforo disponivel em diferentes faixas |
| Erradicacao | `talhao_longevidade_maxima`, `talhao_tch_baixo_corte_maduro`, `talhao_produtivo` | Simular TCH, numero de cortes e situacao do talhao |
| Dados invalidos | `talhao_dado_ausente`, `talhao_tipo_invalido`, `talhao_sem_id` | Validar resiliencia contra nulos, tipos errados e ID ausente |

Essas fixtures tornam os testes menores e evitam duplicacao de dicionarios de talhao.

---

## Testes Unitarios das Regras

### `test_calagem.py`

Esse arquivo valida o contrato minimo da funcao `calcular_necessidade_calagem`.

| Teste | O que garante |
|---|---|
| `test_calagem_retorna_sem_dado_quando_v1_ausente` | Se `V1` estiver ausente, a regra retorna `SEM_DADO` |
| `test_calagem_retorna_sem_dado_para_tipo_invalido` | Se `V1` vier como string, a regra nao quebra e retorna `SEM_DADO` |
| `test_calagem_retorna_chaves_obrigatorias` | O retorno contem `orientacao`, `valor_calculado`, `regra_acionada` e `detalhes` |

Esses testes protegem o contrato de resposta da regra. Mesmo quando nao ha dado confiavel, a funcao deve retornar um dicionario padronizado.

### `test_gessagem.py`

Esse arquivo valida o comportamento basico da funcao `calcular_necessidade_gessagem`.

| Teste | O que garante |
|---|---|
| `test_gessagem_nao_aplicavel_para_cana_soca` | Gessagem de incorporacao nao se aplica a cana soca |
| `test_gessagem_retorna_sem_dado_quando_ca2_ausente` | Se `ca2` estiver ausente, a regra retorna `SEM_DADO` |
| `test_gessagem_retorna_chaves_obrigatorias` | O retorno segue o contrato padrao das regras |

Esses testes garantem que a regra sabe diferenciar caso nao aplicavel de dado ausente.

### `test_insumos.py`

Apesar do nome, este arquivo testa a funcao `calcular_necessidade_fosfatagem`, em `src/rules/fosfatagem.py`.

| Teste | O que garante |
|---|---|
| `test_fosfatagem_nao_aplicavel_para_cana_soca` | Fosfatagem de implantacao nao se aplica a cana soca |
| `test_fosfatagem_retorna_sem_dado_quando_p1_ausente` | Se `p1` estiver ausente, a regra retorna `SEM_DADO` |
| `test_fosfatagem_retorna_chaves_obrigatorias` | O retorno segue o contrato padrao das regras |

A observacao importante e que esse arquivo ainda nao cobre todas as funcoes de `src/rules/insumos.py`; essa cobertura foi ampliada nos testes de valores exorbitantes.

---

## Testes da GoldPipeline

O arquivo `test_pipeline_gold.py` valida a camada `GoldPipeline`, responsavel por aplicar as regras agronomicas sobre a base Silver e montar a tabela Gold.

### Cenarios de resiliencia por talhao

| Teste | O que garante |
|---|---|
| `test_talhao_sem_id_talhao_e_pulado` | Talhao sem `id_talhao` retorna `None` e nao entra no Gold |
| `test_talhao_com_id_talhao_nulo_e_pulado` | `id_talhao = None` tambem e pulado |
| `test_talhao_com_tipo_invalido_nao_levanta_excecao` | Tipo errado em campo de solo nao derruba o processamento |
| `test_talhao_sem_colunas_de_solo_nao_levanta_excecao` | Ausencia de colunas de solo vira `SEM_DADO`, nao exception |

Esses testes protegem uma decisao importante da Sprint 4: erro em um talhao nao deve derrubar a pipeline inteira.

### Cenarios de pipeline com arquivo

| Teste | O que garante |
|---|---|
| `test_pipeline_processa_dataframe_valido` | CSV Silver valido gera uma linha Gold e grava arquivo de saida |
| `test_pipeline_gold_contem_colunas_insumos_pivotadas` | O Gold contem colunas `fosfato_*` e `dessecacao_*` |
| `test_pipeline_fosfato_calcula_quantidade_total` | Quantidade total = dose por hectare x area |
| `test_pipeline_pula_registros_sem_id_e_continua` | Registro invalido e pulado, mas registros validos continuam |
| `test_pipeline_arquivo_nao_encontrado_levanta_file_not_found` | Arquivo inexistente levanta `FileNotFoundError` |

Esses testes usam `tmp_path` para criar CSVs temporarios. Por isso podem ser afetados por permissao no diretorio temporario do sistema se o pytest nao for executado com `--basetemp=.pytest_tmp`.

---

## Testes da Pipeline Modular

O arquivo `test_pipeline_modular.py` valida a arquitetura introduzida na Sprint 5: `BronzePipeline`, `SilverPipeline`, `GoldPipeline` e a orquestradora `Pipeline`.

| Teste | O que garante |
|---|---|
| `test_bronze_renomeia_colunas_sem_dropar_linhas` | Bronze padroniza nomes sem descartar linhas |
| `test_silver_aplica_regras_de_qualidade` | Silver aplica filtros, normalizacao e qualidade de dados |
| `test_silver_bloqueia_id_talhao_nulo` | ID ausente e bloqueado na camada Silver |
| `test_camadas_iniciais_validas` | As camadas iniciais permitidas sao `raw`, `bronze` e `silver` |
| `test_pipeline_a_partir_de_silver_pula_limpeza` | Pipeline iniciada em Silver pula Bronze/Silver e roda ate Gold |
| `test_pipeline_a_partir_de_raw_roda_todas_as_camadas` | Pipeline iniciada em Raw executa Bronze, Silver e Gold |
| `test_pipeline_camada_invalida_levanta_erro` | Camada inicial desconhecida levanta `ValueError` |

Esses testes protegem a modularizacao: a pipeline nao e mais um fluxo unico fixo; ela pode comecar em diferentes pontos conforme o estado da planilha recebida.

---

## Testes de Valores Exorbitantes

O arquivo `test_valores_exorbitantes.py` foi documentado em detalhe na tarefa 5.2, mas dentro da suite completa ele tem tres papeis:

1. Validar fronteiras numericas extraidas do manual.
2. Forcar entradas invalidas como `NaN`, `Infinity`, negativos e strings.
3. Registrar gaps de regra sem quebrar a entrega.

Ele representa a maior parte dos testes coletados porque usa `pytest.mark.parametrize`: um unico teste gera varios cenarios.

---

## Como Rodar

Comando recomendado no Bash:

```bash
./.venv/Scripts/pytest.exe tests/ -q --basetemp=.pytest_tmp
```

Para ver todos os nomes dos testes:

```bash
./.venv/Scripts/pytest.exe tests/ --collect-only -q
```

Para rodar apenas um arquivo:

```bash
./.venv/Scripts/pytest.exe tests/test_pipeline_gold.py -q --basetemp=.pytest_tmp
```

---

## Interpretacao do Resultado

| Saida | Significado |
|---|---|
| `passed` | Teste executou e a condicao esperada foi satisfeita |
| `failed` | Teste executou, mas algum `assert` falhou |
| `error` | Teste nao conseguiu executar corretamente, geralmente por setup/import/permissao |
| `xfailed` | Falha esperada e documentada, usada para gap de regra |
| `warning` | Aviso tecnico, nao necessariamente quebra funcional |

No resultado atual:

```text
92 passed, 1 xfailed, 3 warnings
```

A suite esta verde. O `xfailed` e intencional e os warnings nao bloqueiam a entrega.

---

## Resumo

- A suite cobre regras unitarias, GoldPipeline, pipeline modular e valores extremos.
- Os testes unitarios garantem contratos de retorno padronizados.
- Os testes de Gold validam leitura, escrita, resiliencia e insumos pivotados.
- Os testes modulares garantem que a execucao por camada inicial funciona.
- Os testes extremos documentam fronteiras, entradas invalidas e gaps de regra.
