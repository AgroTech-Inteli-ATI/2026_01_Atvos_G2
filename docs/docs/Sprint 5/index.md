---
sidebar_position: 6
title: Sprint 5
---

# Sprint 5 — Modularização da Pipeline

## Objetivo da Sprint

Reorganizar a pipeline de dados para que cada camada do padrão *medallion*
(`raw → bronze → silver → gold`) seja uma **classe independente**, em arquivo
próprio, e permitir que a execução comece em **qualquer camada** conforme o estado
da planilha recebida — sempre rodando até o Gold.

---

## Entregáveis da Sprint 5

| # | Entregável | Tipo | Status |
|---|---|---|---|
| [5.1](./modularizacao_pipeline) | Modularização da pipeline em POO + execução por ponto de partida | Backend + Front | ✅ Concluído |
| [5.2](./testes_valores_exorbitantes) | Testes de valores exorbitantes e fronteiras agronômicas | QA/Testes | ✅ Concluído |
| [5.3](./suite_testes_completa) | Documentacao da suite completa de testes | QA/Testes | ✅ Concluido |

---

## Resultado Final

```
pytest tests/ -v
92 passed, 1 xfailed, 3 warnings
```

A pipeline agora é composta por `BronzePipeline`, `SilverPipeline`, `GoldPipeline`
e a orquestradora `Pipeline`, e o frontend permite escolher o ponto de partida no
modal de importação. Detalhes completos em
**[Modularização da Pipeline](./modularizacao_pipeline)**.

A suite de testes tambem foi ampliada com cenarios de valores extremos, fronteiras numericas e entradas invalidas extraidas do manual tecnico. Detalhes completos em **[Testes de Valores Exorbitantes](./testes_valores_exorbitantes)**.

A visao consolidada de todos os arquivos da pasta `tests/` esta em **[Suite Completa de Testes](./suite_testes_completa)**.
