---
sidebar_position: 5
title: Sprint 4
---

# Sprint 4 — Testes e Resiliência do Pipeline

## Objetivo da Sprint

Estruturar uma suite de testes automatizados com pytest, corrigir os módulos de regras que estavam como stubs, e garantir que o pipeline Gold seja resiliente a dados inválidos — logando erros sem interromper o processamento.

---

## Contexto: O que foi construído até aqui

Ao final da Sprint 3, o grupo possuía:

| Entregável | Localização | Status |
|---|---|---|
| Pipeline completo Silver → Gold | `src/pipeline_gold.py` | ✅ |
| Módulos de regras agronômicas | `src/rules/` | ✅ |
| Módulo de insumos e doses dinâmicas | `src/rules/insumos.py` | ✅ |
| Gold CSV único com insumos pivotados | `DATA/inventario_gold.csv` | ✅ |

A Sprint 4 **valida e robustece** o que foi construído, garantindo que o sistema seja confiável diante de dados ausentes, tipos errados e arquivos inexistentes.

---

## Entregáveis da Sprint 4

| # | Entregável | Tipo | Status |
|---|---|---|---|
| [4.1](./4-1-suite-de-testes) | Suite pytest com fixtures | Infra/Testes | ✅ Concluído |
| [4.2](./4-2-resiliencia-pipeline) | Pipeline resiliente a dados inválidos | Backend | ✅ Concluído |
| [4.3](./4-3-integracao-api) | Integração frontend + backend via API | Full-stack | ✅ Concluído |

---

## Estrutura de Arquivos ao Final da Sprint

```
tests/                       ← NOVO Sprint 4.1
├── conftest.py              # 13 fixtures compartilhadas
├── test_calagem.py
├── test_gessagem.py
├── test_insumos.py
└── test_pipeline_gold.py

src/
├── rules/
│   ├── calagem.py           ← corrigido Sprint 4.2 (era stub quebrado)
│   ├── gessagem.py          ← corrigido Sprint 4.2 (era PENDENTE)
│   ├── fosfatagem.py        ← corrigido Sprint 4.2 (era PENDENTE)
│   └── erradicacao.py       ← corrigido Sprint 4.2 (era PENDENTE)
└── pipeline_gold.py         ← tratamento de erros adicionado Sprint 4.2

api/                         ← NOVO Sprint 4.3
├── main.py                  # FastAPI — POST /api/run, GET /api/historico
├── historico.json           # histórico de importações (gerado em runtime)
└── temp/                    # arquivos temporários (gerado em runtime)

views/
├── vite.config.js           ← proxy /api → localhost:8000
└── src/
    ├── context/
    │   └── PipelineContext.jsx  ← NOVO — estado global da pipeline
    ├── components/
    │   ├── ImportModal.jsx  ← atualizado — upload real para a API
    │   └── FilterBar.jsx    ← atualizado — opções derivadas dos dados reais
    └── pages/
        ├── Dashboard.jsx    ← atualizado — dados do contexto
        ├── Resultados.jsx   ← atualizado — dados do contexto
        └── Historico.jsx    ← atualizado — dados do contexto
```

---

## Resultado Final

```
pytest tests/ -v
18 passed in 0.31s
```
