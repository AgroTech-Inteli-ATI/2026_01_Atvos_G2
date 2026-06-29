---
sidebar_position: 2
title: "5.1 — Modularização da Pipeline"
---

# Tarefa 5.1 — Modularização da Pipeline

## Objetivo

Transformar a pipeline de dados em uma estrutura **modular e orientada a objetos**,
onde cada camada do padrão *medallion* é uma classe em arquivo próprio, e permitir
que a execução **comece em qualquer camada** (`raw`, `bronze` ou `silver`) conforme
o estado da planilha que o usuário tem em mãos. A pipeline **sempre roda até o Gold**.

---

## Contexto: por que mudar

Até a Sprint 4 a pipeline rodava **inteira de uma só vez**: o endpoint `/api/run`
recebia um arquivo e executava limpeza + regras em sequência, com auto-detecção de
formato. Conversando com o parceiro de projeto, surgiram dois pedidos:

1. **As planilhas chegam em estados diferentes de tratamento.** Nem sempre faz
   sentido rodar a limpeza se a base já vem pronta — às vezes queremos rodar só as
   regras (Gold), às vezes o fluxo completo desde o dado bruto.
2. **Preferência por POO.** O parceiro gosta de uma estrutura de classes, com cada
   pipeline isolada e reutilizável ao longo do código.

A solução foi (a) separar a antiga `limpeza.py` em camadas **Bronze** e **Silver**,
(b) modelar cada camada como uma **classe** em seu próprio arquivo e (c) criar uma
**orquestradora** que monta o fluxo a partir da camada de entrada escolhida.

---

## O padrão Medallion

```
RAW            BRONZE              SILVER                       GOLD
planilha   →   colunas         →   base limpa              →   recomendações
bruta          padronizadas        (qualidade + solo)           agronômicas
(.xlsx)        (sem limpeza)        (pronta p/ regras)           (1 linha/talhão)
```

| Camada | Responsabilidade | Classe |
|---|---|---|
| **Bronze** | Selecionar/renomear colunas do export ATVOS e normalizar encoding. Não descarta linhas. | `BronzePipeline` |
| **Silver** | Regras de qualidade: descartes, imputações, sinalizações, deduplicação + join com a análise de solo. | `SilverPipeline` |
| **Gold** | Aplicar as regras agronômicas (calagem, gessagem, fosfatagem, erradicação, janela, insumos). | `GoldPipeline` |

> A camada **Gold** é sempre o destino final — não é um ponto de partida.

---

## Estrutura de arquivos

Cada pipeline é uma classe em seu próprio arquivo, dentro do pacote `src/pipelines/`:

```
src/
├── pipelines/                  ← NOVO Sprint 5
│   ├── __init__.py             # exporta as classes e CAMADAS_INICIAIS
│   ├── io_utils.py             # leitura/gravação de CSV + caminhos base
│   ├── bronze_pipeline.py      # class BronzePipeline
│   ├── silver_pipeline.py      # class SilverPipeline + QualityReport
│   ├── gold_pipeline.py        # class GoldPipeline
│   └── pipeline.py             # class Pipeline (orquestradora) + CAMADAS_INICIAIS
└── rules/                      # regras agronômicas (funções puras, inalteradas)
    ├── calagem.py
    ├── gessagem.py
    ├── fosfatagem.py
    ├── erradicacao.py
    ├── insumos.py
    └── janela_plantio.py
```

Arquivos removidos nesta refatoração (substituídos pelas classes acima):
`src/processing/limpeza.py`, `src/pipeline_gold.py` e `src/pipeline.py`.

---

## As classes

Todas as classes seguem a mesma convenção:

- **Processos da camada** → métodos individuais (ex.: `selecionar_e_renomear`,
  `tratar_data_plantio`, `processar_talhao`), facilitando reuso e teste isolado.
- **`processar(df)`** → executa a camada **em memória** (DataFrame → DataFrame).
- **`executar(input_path, output_path)`** → versão baseada em **arquivo** (lê um CSV,
  processa e grava o CSV da camada).

### BronzePipeline (`bronze_pipeline.py`)

Padronização estrutural. Mantém o mapa `COLUNAS_RENAME` (Excel → nomes internos).

```python
from pipelines import BronzePipeline

bronze = BronzePipeline()
df_bronze = bronze.processar(df_raw)          # em memória
# ou a partir de arquivo:
df_bronze = bronze.executar("inventario.xlsx", "inventario_bronze.csv")
```

Métodos: `selecionar_e_renomear`, `padronizar_encoding`, `processar`, `executar`.

### SilverPipeline (`silver_pipeline.py`)

Regras de qualidade + enriquecimento com solo. Registra todas as transformações em
um `QualityReport` (descartes, imputações, sinalizações) acessível via `self.report`.
Os limiares (`area_range`, `tch_range`, `max_idade_plantio_anos`, `unidades_oficiais`,
`solo_path`) são parametrizáveis no construtor.

```python
from pipelines import SilverPipeline

silver = SilverPipeline()
df_silver, report = silver.processar(df_bronze)   # só qualidade
df_silver = silver.juntar_solo(df_silver)         # join com solo
report.imprimir()
```

Métodos principais: `bloquear_campo_obrigatorio`, `normalizar_id_talhao`,
`tratar_data_plantio`, `tratar_unidade_industrial`, `tratar_area_ha`,
`tratar_tch_prod`, `remover_duplicatas`, `carregar_solo`, `juntar_solo`,
`processar`, `executar`.

### GoldPipeline (`gold_pipeline.py`)

Aplica as regras agronômicas (que continuam em `src/rules/`) e monta a tabela Gold —
uma linha por talhão, com insumos pivotados em colunas planas (`fosfato_*`,
`dessecacao_*`).

```python
from pipelines import GoldPipeline

gold = GoldPipeline()
df_gold = gold.processar(df_silver)                       # em memória
df_gold = gold.executar("inventario_silver.csv", "inventario_gold.csv")  # arquivo
```

Métodos: `processar_talhao`, `_calcular_insumos`, `_montar_tabela_gold`,
`processar`, `executar`.

### Pipeline — orquestradora (`pipeline.py`)

Compõe as três pipelines de camada e roda **a partir da camada inicial até o Gold**,
materializando **um CSV por camada produzida**. Pode ser reinstanciada com
implementações customizadas de cada camada (injeção de dependência).

```python
from pipelines import Pipeline

pipe = Pipeline()  # usa BronzePipeline/SilverPipeline/GoldPipeline padrão
df_silver, df_gold, arquivos = pipe.executar(
    df_input=df,            # DataFrame já no estado da camada inicial
    camada_inicial="raw",   # "raw" | "bronze" | "silver"
    temp_dir="/tmp",
    run_id="abc123",
)
```

O encadeamento por ponto de partida:

| `camada_inicial` | Etapas executadas | Arquivos gerados |
|---|---|---|
| `raw` | Bronze → Silver → Gold | `bronze_*.csv`, `silver_*.csv`, `gold_*.csv` |
| `bronze` | Silver → Gold | `silver_*.csv`, `gold_*.csv` |
| `silver` | Gold | `silver_*.csv`, `gold_*.csv` |

A constante `CAMADAS_INICIAIS = ("raw", "bronze", "silver")` define as opções válidas;
uma camada fora dessa lista levanta `ValueError`.

---

## Integração com a API

O endpoint `POST /api/run` (em `api/main.py`) ganhou o campo `camada_inicial`
(default `"raw"`, mantendo compatibilidade). O fluxo:

1. Valida `camada_inicial` contra `CAMADAS_INICIAIS` (senão `400`).
2. Lê o arquivo enviado em DataFrame (xlsx/csv).
3. **Valida o formato esperado** para a camada escolhida:
   - `raw` → exige a coluna `TALHAO` (planilha bruta ATVOS); senão `422`.
   - `bronze` / `silver` → exigem a coluna `id_talhao` (base padronizada); senão `422`.
4. Delega à orquestradora: `PIPELINE.executar(df, camada_inicial, TEMP_DIR, run_id)`.
5. Transforma o Gold no formato do frontend e registra a camada usada no histórico.

A API mantém uma instância única `PIPELINE = Pipeline()` reutilizada entre requisições.

---

## Integração com o Frontend

No modal **Importar Lista** (`views/src/components/ImportModal.jsx`) foi adicionado
um seletor de **ponto de partida da pipeline**, com três opções:

| Opção | O que espera |
|---|---|
| **Raw** | Planilha bruta (export ATVOS `.xlsx`) |
| **Bronze** | Colunas já padronizadas (sem limpeza) |
| **Silver** | Base limpa, pronta para as regras |

A escolha é enviada ao backend pelo `PipelineContext`
(`runPipeline(file, nome, camadaInicial)` → `form.append("camada_inicial", ...)`).
Selecionar um ponto de partida incompatível com o arquivo retorna um erro `422`
explicativo na interface.

---

## Testes

A suíte foi atualizada para a API de classes e ampliada:

| Arquivo | Cobre |
|---|---|
| `tests/test_pipeline_gold.py` | `GoldPipeline` — resiliência a dados inválidos, id ausente, insumos pivotados |
| `tests/test_pipeline_modular.py` | Bronze não descarta linhas; Silver aplica qualidade; orquestradora a partir de `raw`/`silver`; camada inválida levanta erro |

```
pytest tests/ -v
25 passed
```

---

## Arquivos de exemplo

Para testar os três pontos de partida pela interface, há CSVs prontos em `exemplos/`:

| Arquivo | Ponto de partida | Demonstra |
|---|---|---|
| `raw_exemplo.csv` | Raw | Fluxo completo Bronze → Silver → Gold a partir das colunas brutas |
| `bronze_exemplo.csv` | Bronze | Limpeza Silver: normalização de `id_talhao`, dedupe e descarte de data futura |
| `silver_exemplo.csv` | Silver | Base com solo → todas as regras (calagem, gessagem, fosfatagem, insumos…) |

---

## Resumo

- Cada camada virou uma **classe reutilizável** em arquivo próprio.
- A **orquestradora `Pipeline`** monta o fluxo a partir da camada de entrada escolhida.
- **API** e **frontend** expõem a escolha do ponto de partida, com validação por camada.
- Comportamento de processamento **idêntico** ao anterior — a mudança é estrutural,
  coberta por 25 testes verdes.
