---
sidebar_position: 1
title: Visão Geral da Sprint 5
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

---

## Resultado Final

```
pytest tests/ -v
25 passed
```

A pipeline agora é composta por `BronzePipeline`, `SilverPipeline`, `GoldPipeline`
e a orquestradora `Pipeline`, e o frontend permite escolher o ponto de partida no
modal de importação. Detalhes completos em
**[Modularização da Pipeline](./modularizacao_pipeline)**.
