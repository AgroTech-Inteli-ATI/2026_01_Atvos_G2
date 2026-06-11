---
sidebar_position: 2
title: "3.3 — Módulo de Insumos e Doses"
---

# Tarefa 3.3 — Módulo de Gestão de Insumos e Doses

## Objetivo

Implementar `src/rules/insumos.py` com funções que calculam doses de insumos por talhão variando **dinamicamente** com o TCH estimado (`tch_prod`). Atualizar o `pipeline_gold.py` para incluir os insumos calculados no CSV de saída em um único arquivo, com colunas planas por tipo de insumo.

---

## Decisões Técnicas

### Separação de responsabilidades

O módulo `fosfatagem.py` (Sprint 2) responde à pergunta **"o solo precisa de correção de P?"** com base na análise química (campo `p1`). O novo `insumos.py` responde **"quanto aplicar?"**, ajustando a dose pela produtividade esperada e fixação do solo. As duas lógicas são complementares e independentes.

### Formato de saída — CSV único

Em vez de dois arquivos (`inventario_gold.csv` + `inventario_gold_insumos.csv`), os insumos são **pivotados em colunas planas** diretamente no Gold. Isso facilita a integração com o frontend, que lê um único arquivo sem precisar fazer join.

---

## Pseudocódigo das Regras

### Fosfatagem dinâmica

```
DEFINIÇÕES:
  TCH_REFERENCIA       = 80 t/ha
  P_EXPORTADO_POR_TON  = 0.40 kg P₂O₅/t

  DOSES_BASE (kg P₂O₅/ha):
    muito_baixo (p1 < 6)   = 120
    baixo       (6 ≤ p1 < 12)  = 80
    medio       (12 ≤ p1 < 25) = 40
    suficiente  (p1 ≥ 25)  = 0

  FATOR_TEXTURA:
    "Muito Argiloso" = 1.20  (maior fixação → dose maior)
    "Argiloso"       = 1.00  (referência)
    "Médio"          = 0.85
    "Arenoso"        = 0.70  (menor fixação → dose menor)

PARA CADA talhão:
  SE p_disponivel É NULO OU tch_estimado É NULO:
    RETORNAR SEM_DADO

  dose_base      = DOSES_BASE[faixa de p_disponivel]
  fator_tex      = FATOR_TEXTURA[textura_solo] ou 1.00 se não mapeado
  ajuste_tchan   = (tch_estimado - TCH_REFERENCIA) × P_EXPORTADO_POR_TON
  dose_final     = MAX(0, dose_base × fator_tex + ajuste_tchan)
```

**Exemplo numérico:**
- Talhão com p1 = 4.5, solo Argiloso, TCH estimado = 90 t/ha
- dose_base = 120, fator_tex = 1.00, ajuste = (90 − 80) × 0.40 = +4.0
- **dose_final = 120 × 1.00 + 4.0 = 124.0 kg P₂O₅/ha**

### Dessecação pré-reforma

```
DEFINIÇÕES:
  DOSES_BASE (L/ha de Glifosato 480 g/L):
    "baixa"  = 1.5
    "média"  = 2.0
    "alta"   = 3.0

  FATOR_ESTAGIO (longevidade da soqueira):
    "jovem"  (no_corte < 3) = 1.00
    "maduro" (3 ≤ no_corte < 6) = 1.10
    "velho"  (no_corte ≥ 6) = 1.20

  CONCENTRAÇÃO = 480 g i.a./L → dose_kg_ha = dose_l_ha × 0.48

PARA CADA talhão ONDE reforma_recomendada == VERDADEIRO:
  estagio    = classificar_no_corte(no_corte)
  infestacao = derivar_de_sit_talhao(sit_talhao)
              ("Fechado" → alta | "Cana Soca" → média | demais → baixa)

  dose_l_ha  = DOSES_BASE[infestacao] × FATOR_ESTAGIO[estagio]
  dose_kg_ha = dose_l_ha × 0.48
```

---

## Implementação

### Arquivo `src/rules/insumos.py`

```python
def calcular_dose_fosfatagem(p_disponivel, textura_solo, tchan_estimado) -> dict:
    """
    Dose de P₂O₅ ajustada por textura e produtividade estimada.
    Fórmula: dose = dose_base × fator_textura + (tchan - 80) × 0.40
    """
    ...

def calcular_dose_dessecacao(infestacao: str, estagio_soqueira: str) -> dict:
    """
    Dose de Glifosato 480 g/L para dessecação pré-reforma.
    Fórmula: dose_l_ha = DOSES_BASE[infestacao] × FATOR_ESTAGIO[estagio]
    """
    ...

def estagio_soqueira_de_no_corte(no_corte) -> str:
    """Converte no_corte → 'jovem' / 'maduro' / 'velho'."""
    ...

def infestacao_de_sit_talhao(sit_talhao) -> str:
    """Deriva infestação proxy a partir de sit_talhao."""
    ...
```

Todas as funções seguem o padrão dos módulos da Sprint 2: dados ausentes ou inválidos retornam `{"orientacao": "SEM_DADO", ...}` sem lançar exceção.

### Atualização do `pipeline_gold.py`

A função `_calcular_insumos(talhao, erradicacao_result)` monta um dicionário plano que é adicionado diretamente à linha do Gold:

```python
row.update(insumos)  # insere fosfato_* e dessecacao_* na mesma linha
```

A dessecação é calculada **somente** quando `erradicacao_result["detalhes"]["reforma_recomendada"] == True`.

---

## Colunas adicionadas ao Gold

| Coluna | Tipo | Descrição |
|---|---|---|
| `fosfato_insumo` | string | Nome do insumo (`"P₂O₅"`) ou `null` |
| `fosfato_dose_kg_ha` | float | Dose calculada (kg/ha) |
| `fosfato_quantidade_total_kg` | float | `dose_kg_ha × area_ha` |
| `fosfato_orientacao` | string | Texto descritivo com raciocínio da dose |
| `fosfato_regra` | string | Identificador da regra acionada |
| `dessecacao_insumo` | string | `"Glifosato 480 g/L"` ou `null` |
| `dessecacao_dose_kg_ha` | float | Dose em kg i.a./ha |
| `dessecacao_dose_l_ha` | float | Dose em L/ha (produto comercial) |
| `dessecacao_quantidade_total_kg` | float | `dose_kg_ha × area_ha` |
| `dessecacao_orientacao` | string | Texto descritivo |
| `dessecacao_regra` | string | Identificador da regra acionada |

Colunas ficam `null` quando o insumo não se aplica ao talhão (ex: dessecação sem reforma recomendada).

---

## Amostra da Saída Gold

| id_talhao | categoria | fosfato_insumo | fosfato_dose_kg_ha | fosfato_qtd_total_kg | dessecacao_insumo | dessecacao_dose_l_ha | dessecacao_qtd_total_kg | erradicacao_regra |
|---|---|---|---|---|---|---|---|---|
| T001 | Formação | P₂O₅ | 118.0 | 2950.0 | — | — | — | categoria_formacao |
| T002 | Cana Soca | — | — | — | Glifosato 480 g/L | 3.3 | 28.51 | reforma_tch_baixo_corte_maduro |
| T003 | Cana Soca | — | — | — | Glifosato 480 g/L | 2.4 | 14.40 | reforma_longevidade_maxima |
| T004 | Formação | — | — | — | — | — | — | categoria_formacao |

- **T001**: cana planta com P muito baixo → dose de fosfato calculada; sem dessecação (não há reforma)
- **T002**: soca com TCH abaixo do limiar, 5 cortes, talhão fechado → reforma alta prioridade, dessecação indicada (infestação alta, soqueira madura)
- **T003**: soca com 9 cortes → longevidade máxima, dessecação indicada (infestação média, soqueira velha = fator 1.20)
- **T004**: cana planta sem nenhum dado de solo → todos os insumos retornam `null` (`SEM_DADO`)

---

## Variação da Dose com TCH (validação)

O mesmo talhão com p1 = 4.5, solo Argiloso:

| TCH estimado (t/ha) | Ajuste TCH (kg/ha) | Dose final (kg P₂O₅/ha) |
|---|---|---|
| 60 | −8.0 | 112.0 |
| 80 | 0.0 | 120.0 |
| 100 | +8.0 | 128.0 |

A dose varia ±6.7% a cada 20 t/ha de diferença em relação ao TCH de referência (80 t/ha).

---

## Critérios de Aceite

| Critério | Resultado |
|---|---|
| `from rules.insumos import calcular_dose_fosfatagem` importa sem erros | ✅ |
| `calcular_dose_fosfatagem(None, "Argiloso", None)["orientacao"] == "SEM_DADO"` | ✅ |
| Mesmo talhão com TCH 60 vs 100 resulta em doses diferentes | ✅ (112 vs 128 kg/ha) |
| Gold contém colunas `fosfato_dose_kg_ha` e `dessecacao_dose_l_ha` | ✅ |
| Arquivo único `inventario_gold.csv` (sem arquivo separado de insumos) | ✅ |
