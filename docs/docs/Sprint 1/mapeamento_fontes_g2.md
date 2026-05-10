---
title: "Mapeamento de Fontes"
sidebar_position: 1
---

# Mapeamento de Fontes de Dados — Sprint 1

**Última atualização:** 2026-05-07  
**Responsável:** Atvos G2  
**Integrantes:** Guilherme Ludovico, Haila, Guilherme, João Glauco, Gregory

> **Nota de infraestrutura:** este projeto opera inteiramente sem Google Cloud Platform.
> As alternativas locais adotadas estão descritas na seção final deste documento.

---

## Visão Geral das Fontes

O inventário agrícola da Atvos para o período 2021–2027 está distribuído em cinco arquivos distintos, cada um com papel bem definido dentro da arquitetura de dados da Sprint 1. A separação entre um arquivo de correção de talhões e quatro partes do inventário principal não é arbitrária: reflete tanto os limites operacionais de exportação quanto a natureza diferente dos dados — um conjunto descreve transformações históricas na identidade dos talhões; os demais registram o estado produtivo de cada talhão em cada safra.

Todas as fontes estão no formato Excel (.xlsx), foram lidas a partir do diretório `data/raw/` e persistidas como Parquet em `data/processed/` após o processamento Silver.

---

## Fonte 1 — Correção Talhões para Unificação

| Atributo | Valor |
|----------|-------|
| **Arquivo** | `data/raw/Correcao_talhoes_para_unificacao.xlsx` |
| **Silver** | `data/processed/Correcao_talhoes_para_unificacao_silver.parquet` |
| **Formato** | Excel (.xlsx) |
| **Linhas** | 23.599 |
| **Colunas** | 8 |
| **Granularidade** | 1 linha = 1 par (talhão origem → talhão destino) |
| **Chave de junção** | `Faz_Origem` + `Setor_Origem` + `Talhao_Origem` |
| **Frequência de atualização** | Snapshot manual (atualização por demanda) |
| **Nulos** | Nenhum |
| **Encoding detectado** | latin-1 (corrigido para UTF-8 na Silver) |

Este arquivo funciona como um dicionário de rastreabilidade: para cada talhão que sofreu reforma ou unificação, registra de onde veio e para onde foi. Sem ele, análises históricas de produtividade por talhão incorreriam em dupla contagem ou perda de continuidade do ciclo.

**Estrutura de colunas:**

| Coluna | Tipo | Descrição | Chave? |
|--------|------|-----------|--------|
| `Safra_Origem` | int | Safra do talhão de origem (formato AASSSS) | Parte da chave |
| `Faz_Origem` | int | Código da fazenda de origem | Parte da chave |
| `Setor_Origem` | int | Setor da fazenda de origem | Parte da chave |
| `Talhao_Origem` | int | Número do talhão de origem | Parte da chave |
| `Faz_Destino` | int | Código da fazenda de destino | — |
| `Setor_Destino` | int | Setor da fazenda de destino | — |
| `Talhao_Destino` | int | Número do talhão de destino | — |
| `Motivo` | str | Motivo da correção (ex: "1-Reforma", "2-Unificação") | — |

---

## Fonte 2 — Inventário Atvos 2021-2027 (Parte 1)

| Atributo | Valor |
|----------|-------|
| **Arquivo** | `data/raw/Inventario_atvos_21_27_part_1.xlsx` |
| **Silver** | `data/processed/Inventario_atvos_21_27_part_1_silver.parquet` |
| **Formato** | Excel (.xlsx) |
| **Linhas (raw)** | 50.000 |
| **Colunas (raw)** | 74 |
| **Colunas (silver)** | 75 (67 originais mantidas + 8 flags de negócio) |
| **Granularidade** | 1 linha = 1 talhão × 1 safra |
| **Chave primária** | `CHAVESIG` (inteiro único) |
| **Chave de junção** | `NUM` + `SETOR` + `TALHAO` |
| **Safras cobertas** | 2020/21 a 2026/27 |
| **Data de geração** | 2026-04-23 |
| **Tamanho estimado (parquet)** | ~18 MB comprimido |

---

## Fonte 3 — Inventário Atvos 2021-2027 (Parte 2)

| Atributo | Valor |
|----------|-------|
| **Arquivo** | `data/raw/Inventario_atvos_21_27_part_2.xlsx` |
| **Silver** | `data/processed/Inventario_atvos_21_27_part_2_silver.parquet` |
| **Formato** | Excel (.xlsx) |
| **Linhas (raw)** | 50.000 |
| **Colunas (raw)** | 74 |
| **Colunas (silver)** | 75 (67 originais mantidas + 8 flags de negócio) |
| **Granularidade** | 1 linha = 1 talhão × 1 safra |
| **Chave primária** | `CHAVESIG` (inteiro único) |
| **Chave de junção** | `NUM` + `SETOR` + `TALHAO` |
| **Safras cobertas** | 2020/21 a 2026/27 |
| **Data de geração** | 2026-04-23 |
| **Tamanho estimado (parquet)** | ~18 MB comprimido |

---

## Fonte 4 — Inventário Atvos 2021-2027 (Parte 3)

| Atributo | Valor |
|----------|-------|
| **Arquivo** | `data/raw/Inventario_atvos_21_27_part_3.xlsx` |
| **Silver** | `data/processed/Inventario_atvos_21_27_part_3_silver.parquet` |
| **Formato** | Excel (.xlsx) |
| **Linhas (raw)** | 50.000 |
| **Colunas (raw)** | 74 |
| **Colunas (silver)** | 75 (67 originais mantidas + 8 flags de negócio) |
| **Granularidade** | 1 linha = 1 talhão × 1 safra |
| **Chave primária** | `CHAVESIG` (inteiro único) |
| **Chave de junção** | `NUM` + `SETOR` + `TALHAO` |
| **Safras cobertas** | 2020/21 a 2026/27 |
| **Data de geração** | 2026-04-23 |
| **Tamanho estimado (parquet)** | ~18 MB comprimido |

---

## Fonte 5 — Inventário Atvos 2021-2027 (Parte 4)

| Atributo | Valor |
|----------|-------|
| **Arquivo** | `data/raw/Inventario_atvos_21_27_part_4.xlsx` |
| **Silver** | `data/processed/Inventario_atvos_21_27_part_4_silver.parquet` |
| **Formato** | Excel (.xlsx) |
| **Linhas (raw)** | 17.426 |
| **Colunas (raw)** | 74 |
| **Colunas (silver)** | 75 (67 originais mantidas + 8 flags de negócio) |
| **Granularidade** | 1 linha = 1 talhão × 1 safra |
| **Chave primária** | `CHAVESIG` (inteiro único) |
| **Chave de junção** | `NUM` + `SETOR` + `TALHAO` |
| **Safras cobertas** | 2020/21 a 2026/27 |
| **Data de geração** | 2026-04-23 |
| **Tamanho estimado (parquet)** | ~7 MB comprimido |

---

## Estrutura de Colunas do Inventário (Partes 1 a 4 — estrutura idêntica)

As quatro partes do inventário compartilham exatamente o mesmo schema de 74 colunas no raw. Na camada Silver, esse número sobe para 75: sete colunas são removidas (seis 100% nulas e um índice automático do pandas) e oito flags de negócio são acrescentadas, resultando em saldo líquido de +1 coluna.

| Coluna | Tipo | Descrição | Chave? | Nulos |
|--------|------|-----------|--------|-------|
| `CHAVESIG` | int | Identificador único do talhão no SIG | PK | 0% |
| `CHAVE` | str | Chave legível (formato: NUM-SETOR-TALHAO) | — | 0% |
| `SAFRA` | int | Código da safra (formato AASSSS) | — | 0% |
| `EMPRESA` | int | Código numérico da empresa/unidade | FK | 0% |
| `DESC_EMPRESA` | str | Sigla da unidade industrial | — | 0% |
| `UndGerencial` | str | Unidade gerencial (igual DESC_EMPRESA) | — | 0% |
| `BLOCO` | float | Bloco de colheita | — | 23,5% |
| `NUM` | int | Código numérico da fazenda | FK | 0% |
| `FAZENDA` | str | Nome da fazenda | — | 0% |
| `SETOR` | int | Número do setor dentro da fazenda | FK | 0% |
| `TALHAO` | int | Número do talhão dentro do setor | FK | 0% |
| `DE_OCUP` | str | Descrição da ocupação (ex: "Cana de Açúcar") | — | 0% |
| `FG_OCORREN` | str | Flag de ocorrência (S/F) | — | 0% |
| `DT_OCORREN` | datetime | Data da ocorrência | — | 0% |
| `AREA_HA` | float | Área total do talhão em hectares | — | 0% |
| `AREA_DANO` | float | Área danificada em hectares | — | ~0,1% |
| `VARIED` | str | Variedade de cana plantada | — | 0% |
| `MAN_HIPOT` | str | Manejo hipotético (Precoce/Média/Tardia) | — | ~2,8% |
| `TIPO_PROP` | str | Tipo de propriedade (PARC, FORNSUPAR etc.) | — | 0% |
| `TIPO_CONTRATO` | str | Tipo de contrato com o fornecedor | — | ~0,1% |
| `ESTAGIO` | str | Estágio da cana (ex: "3º Corte", "Formação 18m") | — | 0% |
| `NO_CORTE` | int | Número do corte | — | 0% |
| `CATEGORIA` | str | Categoria (Cana Soca, Formação, Muda) | — | 0% |
| `DATA_PLANTIO` | datetime | Data do plantio | — | ~10,3% |
| `FRENTE` | int | Código da frente de colheita | — | 0% |
| `ZONA_AGRO_ECOLOGICA` | float | Código da zona agroecológica | — | ~18% (geo) |
| `DESC_ZONA` | str | Descrição da zona agroecológica | — | ~18% (geo) |
| `DT_CARACT` | datetime | Data do evento de caracterização | — | ~99,8% (negócio) |
| `CARACT` | str | Tipo de caracterização | — | ~99,8% (negócio) |
| `EXPANSAO` | str | Flag de expansão (S/N) | — | 0% |
| `Devolucao` | str | Flag de devolução (S/N) | — | 0% |
| `Reforma` | str | Flag de reforma (S/N) | — | 0% |
| `TP_REFORMA` | str | Tipo de reforma | — | ~69% (negócio) |
| `SIST_PLANT` | str | Sistema de plantio | — | ~2,8% |
| `TP_IRRIGA` | str | Tipo de irrigação | — | 0% |
| `Vinhaca_E` | str | Aplicação de vinhaça (S/N) | — | 0% |
| `TORTA` | str | Aplicação de torta de filtro (S/N) | — | 0% |
| `SISTEMA_COL` | float | Sistema de colheita | — | ~0,6% |
| `DIST_TERRA` | float | Distância por estrada de terra (km) | — | 0% |
| `DIST_ASFALTO` | float | Distância por asfalto (km) | — | 0% |
| `DIST_HIDR` | int | Distância hidroviária (km) | — | 0% |
| `UNID_IND` | int | Código da unidade industrial | FK | 0% |
| `AMBIENTE` | str | Código do ambiente de produção | — | 0% |
| `DESC_AMBIENTE` | str | Descrição do ambiente (tipo de solo) | — | ~36% (geo) |
| `DE_TP_SOLO` | str | Descrição do tipo de solo | — | 0% |
| `ESPAC` | str | Espaçamento de plantio | — | 0% |
| `AREA_PROD` | float | Área de produção (ha) — **imputada** | — | 0% após silver |
| `TCH_PROD` | float | Toneladas de cana por hectare estimadas — **imputada** | — | 0% após silver |
| `TON_ESTIM` | float | Toneladas estimadas de produção — **imputada** | — | 0% após silver |
| `AREA_REEST` | float | Área de reestimativa (ha) | — | ~56% (negócio) |
| `TCH_REEST` | float | TCH reestimado | — | ~56% (negócio) |
| `TON_REEST` | float | Toneladas reestimadas | — | ~56% (negócio) |
| `AREA_MUDA` | float | Área de muda (ha) | — | ~94% (negócio) |
| `TCH_MUDA` | float | TCH de muda | — | ~94% (negócio) |
| `TON_MUDA` | float | Toneladas de muda | — | ~94% (negócio) |
| `AREA_COLHIDA` | float | Área efetivamente colhida (ha) | — | ~38% (negócio) |
| `OBJETIVO` | str | Objetivo do talhão (Safra, Muda) | — | ~0,5% |
| `SIT_TALHAO` | str | Situação atual do talhão | — | 0% |
| `DATA_FECHA` | datetime | Data de fechamento do ciclo | — | ~35% (negócio) |
| `CANA_ENT` | float | Cana entregue na usina (ton) | — | ~99% (negócio) |
| `ADMIN` | str | Tipo de administração (CANA PROPRIA, FORNECEDOR) | — | 0% |
| `CD_FORNEC` | int | Código do fornecedor | FK | 0% |
| `FORNEC` | str | Nome do fornecedor | — | ~0,1% |
| `ULT_CORTE` | datetime | Data do último corte | — | ~5,5% |
| `LATITUDE` | str | Latitude do centróide do talhão | — | ~18,5% (geo) |
| `LONGITUDE` | str | Longitude do centróide do talhão | — | ~18,5% (geo) |
| `Data_Geracao_Planilha` | datetime | Timestamp de geração do arquivo | — | 0% |

**Flags incorporadas na camada Silver (ausentes no raw):**

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| `flag_bloco_ausente` | bool | True quando BLOCO é nulo |
| `flag_caract_ausente` | bool | True quando DT_CARACT e CARACT são nulos |
| `flag_cana_ent_ausente` | bool | True quando CANA_ENT é nulo |
| `flag_tp_reforma_ausente` | bool | True quando TP_REFORMA é nulo |
| `flag_reestimativa_ausente` | bool | True quando AREA_REEST, TCH_REEST e TON_REEST são nulos |
| `flag_muda_ausente` | bool | True quando AREA_MUDA, TCH_MUDA e TON_MUDA são nulos |
| `flag_colheita_ausente` | bool | True quando AREA_COLHIDA é nulo |
| `flag_talhao_aberto` | bool | True quando DATA_FECHA é nulo |

---

## Relações entre Fontes

A integração das fontes segue uma hierarquia clara: primeiro une-se o inventário fragmentado em quatro partes usando `CHAVESIG` como chave primária; em seguida, o conjunto unificado (167.426 linhas) é cruzado com a tabela de correção de talhões para rastrear reformas e unificações. O enriquecimento geográfico está planejado para a Sprint 2 e depende de fontes externas ainda não incorporadas.

```
Inventario_part_1  ─┐
Inventario_part_2  ─┤
                    ├─ Unir por CHAVESIG → Inventario Completo (167.426 linhas)
Inventario_part_3  ─┤
Inventario_part_4  ─┘
                    │
                    └─── Cruzar com Correcao_talhoes via:
                         Faz_Origem = NUM, Setor_Origem = SETOR,
                         Talhao_Origem = TALHAO
                    │
                    └─── Enriquecimento geográfico (Sprint 2):
                         LATITUDE / LONGITUDE → Shapefile de talhões / IBGE
                         ZONA_AGRO_ECOLOGICA  → Zoneamento agrícola MAPA
                         DESC_AMBIENTE        → Dataset de análise de solo
```

---

## Balanço de Qualidade: Raw versus Silver

A tabela abaixo consolida o estado dos dados antes e depois da limpeza, tomando as partes 2 e 4 como referência por concentrarem o maior volume de transformações detectadas.

| Dimensão | Raw | Silver | Observação |
|----------|-----|--------|------------|
| Colunas totais (inventário) | 74–75 | 75 | +8 flags, -7 drops, -1 índice |
| Linhas com pelo menos 1 nulo | ~28% | ~18% | Redução via imputação de mediana |
| Colunas 100% nulas | 6 | 0 | Removidas dinamicamente |
| Encoding incorreto | Presente | Corrigido | Colunas texto latin-1/UTF-8 |
| Datas como string | Presente | Corrigido | `datetime64` padronizado |
| Espaços em colunas texto | Presente | Corrigido | `str.strip()` aplicado |
| Coordenadas ausentes | ~18,5% | ~18,5% | Mantidas — cruzamento Sprint 2 |

---

## Alternativas ao GCP (operação sem BigQuery / sem GCS)

A ausência de infraestrutura em nuvem foi tratada como restrição de projeto, não como limitação técnica. Para cada dependência originalmente prevista com o GCP, uma solução local equivalente foi adotada sem perda de capacidade analítica.

| Necessidade original | Solução adotada |
|---------------------|----------------|
| BigQuery (SQL em escala) | **DuckDB** (`pip install duckdb`) — SQL in-process sobre Parquet/DataFrames locais |
| GCS (armazenamento de arquivos) | **Sistema de arquivos local** — `data/raw/` e `data/processed/` |
| Script `extract_bigquery.py` | `src/ingestion/extract_local.py` — lê CSV/Excel/Parquet com logging |
| Script `extract_gcs.py` | Mesmo `extract_local.py` — função `extract_all_raw()` |

O DuckDB merece destaque especial por suportar wildcard em leitura de Parquet, o que permite agregar todas as partes do inventário numa única query sem necessidade de UNION explícito:

```python
import duckdb

df = duckdb.query("""
    SELECT UNID_IND, SAFRA, AVG(TCH_PROD) as tch_medio, SUM(TON_ESTIM) as ton_total
    FROM read_parquet('data/processed/Inventario_atvos_21_27_part_*.parquet')
    GROUP BY UNID_IND, SAFRA
    ORDER BY UNID_IND, SAFRA
""").df()
```

> O padrão `part_*.parquet` faz com que o DuckDB leia todos os arquivos de inventário em uma única chamada, eliminando a necessidade de concatenação manual em memória.
