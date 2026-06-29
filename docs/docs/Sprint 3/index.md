---
sidebar_position: 4
title: Sprint 3
---

# Sprint 3 — Módulo de Insumos e Doses

## Objetivo da Sprint

Implementar o módulo de gestão de insumos e doses dinâmicas, integrando o cálculo de P₂O₅ e dessecante ao pipeline Gold com base na produtividade estimada (`tch_prod`) e nas características de solo de cada talhão.

---

## Contexto: O que foi construído até aqui

Ao final da Sprint 2, o grupo possuía:

| Entregável | Localização | Status |
|---|---|---|
| Limpeza e padronização Silver | `src/processing/limpeza.py` | ✅ |
| Dicionário de dados Silver (75 colunas) | `docs/Sprint 1/dicionario_dados_g2.md` | ✅ |
| Regras de limpeza documentadas | `docs/Sprint 1/regras_limpeza_g2.md` | ✅ |
| Módulos de regras agronômicas | `src/rules/` (calagem, gessagem, fosfatagem, erradicação, janela_plantio) | ✅ |
| Pipeline Gold com orientações por talhão | `src/pipeline_gold.py` | ✅ |
| Mapa lógico de regras e pseudocódigo | `docs/Sprint 2/` | ✅ |

A Sprint 3 **expande** o pipeline com o módulo de dosagem dinâmica de insumos, diferenciando a dose recomendada por produtividade esperada e textura de solo.

---

## Entregáveis da Sprint 3

| # | Entregável | Tipo | Status |
|---|---|---|---|
| [3.3](./3-3-insumos) | Módulo de insumos e doses | Backend | ✅ Concluído |

---

## Estrutura de Arquivos ao Final da Sprint

```
src/
├── rules/
│   ├── calagem.py
│   ├── gessagem.py
│   ├── fosfatagem.py
│   ├── erradicacao.py
│   ├── janela_plantio.py
│   ├── insumos.py          ← NOVO Sprint 3
│   ├── utils.py
│   └── __init__.py
└── pipeline_gold.py        ← atualizado Sprint 3

DATA/
└── inventario_gold.csv     ← agora inclui colunas fosfato_* e dessecacao_*
```
