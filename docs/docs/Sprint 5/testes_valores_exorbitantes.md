---
sidebar_position: 3
title: "5.2 - Testes de Valores Exorbitantes"
---

# Tarefa 5.2 - Testes de Valores Exorbitantes

## Objetivo

Ampliar a suite de testes da pipeline para cobrir **valores extremos, fora de faixa e entradas invalidas** nas regras agronomicas ja implementadas.

A suite anterior validava principalmente resiliencia geral, integracao da pipeline modular e alguns cenarios basicos das regras. Esta etapa adiciona uma camada de QA mais agressiva: testar fronteiras numericas do manual tecnico e valores que nao deveriam aparecer em dados reais, como `NaN`, `Infinity`, negativos, strings e numeros absurdamente grandes.

---

## Fonte das Regras

Os cenarios foram derivados do manual tecnico de manejo de cana-de-acucar e aplicados somente as regras que ja existem no codigo.

Nao foram criados testes para regras qualitativas ou para etapas que ainda nao possuem funcao implementada na pipeline. Quando o manual nao define claramente o comportamento esperado para um valor extremo, o caso foi tratado como **gap de regra**, e nao como uma regra inventada.

---

## Arquivo Criado

```text
tests/
`-- test_valores_exorbitantes.py
```

Esse arquivo concentra os testes parametrizados de valores extremos. A ideia e manter separados os testes basicos das regras e os testes de borda, facilitando a leitura da suite.

---

## Funcoes Testadas

| Funcao | Modulo | O que os testes extremos cobrem |
|---|---|---|
| `campo_invalido` | `src/rules/utils.py` | `None`, string, `NaN`, `Infinity`, `-Infinity`, negativos e booleanos |
| `calcular_necessidade_calagem` | `src/rules/calagem.py` | V% na fronteira de 60%, Mg na fronteira de 5, CTC extremo e entradas invalidas |
| `calcular_necessidade_gessagem` | `src/rules/gessagem.py` | Ca `< 4`, saturacao por Al `> 40%`, fronteiras e combinacoes inconsistentes |
| `calcular_necessidade_fosfatagem` | `src/rules/fosfatagem.py` | P nas fronteiras 6, 12 e 25, valor muito alto e entradas invalidas |
| `calcular_erradicacao` | `src/rules/erradicacao.py` | TCH na fronteira de 55, cortes 6 e 8, cortes/TCH extremos e invalidos |
| `calcular_dose_fosfatagem` | `src/rules/insumos.py` | Dose dinamica de fosfato com P na fronteira e TCH invalido |
| `GoldPipeline.processar` | `src/pipelines/gold_pipeline.py` | `area_ha` invalida no calculo de quantidade total de insumo |

---

## Matriz Resumida de Cenarios

| Classe de cenario | Exemplo | Resultado esperado |
|---|---|---|
| Tipo invalido | `"alto"`, `"baixo"`, `"dez"` | Retornar `SEM_DADO` |
| Valor ausente | `None`, `NaN` | Retornar `SEM_DADO` |
| Infinito | `math.inf`, `-math.inf` | Retornar `SEM_DADO` |
| Valor negativo | `-1`, `-0.001` | Retornar `SEM_DADO` |
| Fronteira exata | V% `60`, Mg `5`, P `6/12/25`, TCH `55` | Acionar a regra correta da fronteira |
| Fronteira inferior/superior | `limite - EPS`, `limite + EPS` | Confirmar mudanca correta de faixa |
| Overflow numerico | `1e18` | Aceitar somente quando a regra atual possui comportamento definido |
| Combinacao inconsistente | Ca baixo sem Al alto; Al alto sem Ca baixo | Nao aplicar gessagem, pois o manual exige os dois criterios |
| Area invalida | `0`, negativo, infinito, string, `None` | Nao calcular quantidade total de insumo |

---

## Alteracoes de Logica Necessarias

Os testes revelaram alguns pontos em que a pipeline precisava ser mais rigida para tratar dados fora de faixa.

### `campo_invalido`

O helper passou a considerar invalidos:

- booleanos;
- numeros nao finitos (`Infinity`, `-Infinity`, `NaN`);
- valores negativos.

Isso evita que regras agronomicas aceitem valores que sao numericamente validos para o Python, mas invalidos como dado de solo, produtividade, corte ou area.

### Gessagem

O manual define a gessagem como recomendada quando:

```text
Ca < 4 mmolc/dm3 E saturacao por Al > 40%
```

Antes, a regra aceitava `Ca < 4` **ou** `Al > 40%`. Os testes de combinacao inconsistente deixaram isso explicito, e a regra foi ajustada para usar `AND`.

### Area no Gold

A quantidade total de insumo e calculada por:

```text
dose por hectare x area do talhao
```

Se `area_ha` for `0`, negativa, infinita, string ou ausente, a pipeline agora nao calcula quantidade total. A dose por hectare pode existir, mas o total em kg fica sem valor confiavel.

---

## Como os Testes Funcionam

O arquivo usa `pytest.mark.parametrize` para concentrar varios inputs extremos em um unico teste por regra.

Exemplo conceitual:

```python
@pytest.mark.parametrize("p1", [-0.001, math.inf, -math.inf, math.nan, "baixo"])
def test_fosfatagem_retorna_sem_dado_para_invalidos_extremos(p1):
    resultado = calcular_necessidade_fosfatagem({"p1": p1, ...})
    assert resultado["orientacao"] == "SEM_DADO"
```

Esse padrao reduz duplicacao e deixa claro qual classe de valores esta sendo validada.

---

## O `xfail`

A suite possui um teste marcado como `xfail`:

```text
test_insumo_fosfato_tchan_overflow_extremo_deveria_ser_sinalizado
```

`xfail` significa **expected failure**: o teste representa uma falha esperada e documentada, nao um erro inesperado da suite.

O caso testado e:

```text
tchan_estimado = 1e18
```

Esse valor e absurdo agronomicamente, mas o manual nao define um limite superior formal para `tchan_estimado`. A funcao `calcular_dose_fosfatagem` consegue fazer a conta matematicamente, mas isso nao significa que o resultado seja uma recomendacao agronomica valida.

Por isso o teste foi marcado como gap:

```text
GAP DE REGRA - decisao de produto necessaria
```

Quando o produto decidir o comportamento esperado, existem tres caminhos possiveis:

| Decisao de produto | Comportamento no teste |
|---|---|
| Tratar TCH extremo como invalido | Remover `xfail` e esperar `SEM_DADO` |
| Limitar por teto maximo | Remover `xfail` e validar o clamp |
| Gerar alerta de revisao | Remover `xfail` e validar o flag/alerta |

Enquanto isso nao for definido, o `xfail` mantem a lacuna visivel sem quebrar a entrega.

---

## Warnings

Ao rodar a suite completa, aparecem warnings como:

```text
DeprecationWarning: datetime.datetime.utcnow() is deprecated
```

Eles vem de `src/pipelines/silver_pipeline.py`, onde a data atual e obtida com `datetime.utcnow()`.

Esses warnings **nao sao falhas de teste**. Eles indicam que uma API do Python continua funcionando hoje, mas esta marcada para remocao ou mudanca futura.

O ajuste recomendado no futuro e usar data/hora com timezone explicito, por exemplo `datetime.now(datetime.UTC)`. Como isso nao afeta o comportamento testado nesta etapa, os warnings foram registrados, mas nao bloqueiam a suite.

---

## Erro de Permissao no Diretorio Temporario

Durante a execucao local no Windows, alguns testes de pipeline podem falhar com:

```text
PermissionError: [WinError 5] Acesso negado:
C:\Users\Inteli\AppData\Local\Temp\pytest-of-Inteli
```

Isso acontece antes de o teste rodar, durante o setup da fixture `tmp_path` do pytest. Nao e falha das regras nem da pipeline; e permissao do sistema no diretorio temporario padrao.

A solucao e rodar o pytest com um diretorio temporario dentro do projeto:

```bash
./.venv/Scripts/pytest.exe tests/ -q --basetemp=.pytest_tmp
```

O arquivo `pytest.ini` tambem fixa `testpaths = tests`, garantindo que a coleta padrao fique restrita a pasta de testes do projeto.

---

## Resultado Atual

Resultado esperado da suite apos os testes extremos:

```text
92 passed, 1 xfailed, 3 warnings
```

Interpretacao:

| Saida | Significado |
|---|---|
| `92 passed` | Testes passaram |
| `1 xfailed` | Gap de regra documentado para TCH extremo |
| `3 warnings` | Avisos de depreciacao, sem quebra funcional |

---

## Resumo

- A suite agora testa valores extremos, nao apenas casos felizes.
- Os limites do manual foram convertidos em testes de fronteira.
- Entradas fisicamente invalidas retornam `SEM_DADO`.
- A gessagem foi alinhada ao criterio combinado do manual (`Ca < 4` e `Al > 40%`).
- Quantidade total de insumo nao e calculada quando `area_ha` e invalida.
- O `xfail` documenta uma decisao de produto pendente, sem quebrar a suite.
