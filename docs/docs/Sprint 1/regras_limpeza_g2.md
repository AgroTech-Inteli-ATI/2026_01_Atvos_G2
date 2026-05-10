---
title: "Regras de Limpeza"
sidebar_position: 2
---

# Regras de Limpeza — Camada Silver

**Data de aprovação:** 07/05/2026  
**Responsável:** Atvos G2  
**Equipe:** Guilherme Ludovico, Haila, Guilherme, João Glauco e Gregory
**Relacionado à:** Task 1.5 — Script de limpeza

---

## 1. Princípios Orientadores

O ponto de partida desta etapa foi uma constatação simples: nem todo valor ausente é um problema a resolver. Alguns nulos refletem ausências legítimas do ponto de vista agronômico; outros indicam falhas reais de preenchimento; outros ainda são resquícios de colunas que nunca chegaram a ser utilizadas operacionalmente. Tratar todas essas situações da mesma forma seria tão equivocado quanto ignorá-las.

A partir dessa distinção, o trabalho de limpeza foi organizado em torno de seis critérios, cada um com seu tratamento específico:

| Situação | Critério adotado | Tratamento |
|---|---|---|
| Coluna totalmente nula | 100% dos valores vazios | Remover a coluna |
| Nulo com significado de negócio | Ausência do valor é esperada | Criar `flag_*` e manter os nulos |
| Nulo indicando dado faltante | Informação deveria existir | Imputação usando mediana por `UNID_IND` |
| Nulo geográfico | Falta de cobertura/mapeamento | Manter para enriquecimento posterior |
| Baixa quantidade de nulos | Menos de ~6% e sem impacto claro | Manter sem alteração |
| Problema de encoding | Texto mal codificado | Corrigir encoding latin-1/UTF-8 |

> A regra de correção de encoding emergiu durante a análise manual do arquivo `Correcao_talhoes_para_unificacao.xlsx`, onde sequências como `Ã§Ã£o` apareceram no lugar de `ção` — sinal clássico de double-encoding entre latin-1 e UTF-8.

---

## 2. Eliminação de Colunas

### 2.1 Índices Gerados Automaticamente na Exportação

Colunas criadas pelo processo de exportação anterior sem nenhum conteúdo analítico.

| Coluna | Arquivo | Motivo |
|---|---|---|
| `Unnamed: 0` | Inventário parts 2 e 4 | Índice criado automaticamente pelo pandas |

### 2.2 Colunas Reservadas sem Uso (100% Nulas)

Seis colunas foram identificadas como completamente vazias — todas variantes de campos de reestimativa nunca preenchidos nos arquivos analisados.

| Coluna | Arquivo | Motivo |
|---|---|---|
| `AREA_REEST2` | Inventário parts 2 e 4 | Coluna reservada sem uso |
| `TCH_REEST2` | Inventário parts 2 e 4 | Coluna reservada sem uso |
| `TON_REEST2` | Inventário parts 2 e 4 | Coluna reservada sem uso |
| `AREA_REEST3` | Inventário parts 2 e 4 | Coluna reservada sem uso |
| `TCH_REEST3` | Inventário parts 2 e 4 | Coluna reservada sem uso |
| `TON_REEST3` | Inventário parts 2 e 4 | Coluna reservada sem uso |

> A detecção é feita programaticamente via `df.columns[df.isna().all()]`, garantindo que arquivos futuros com novas colunas igualmente vazias sejam tratados de forma automática e consistente.

---

## 3. Flags de Negócio: Preservando o Significado dos Nulos

Determinadas ausências não são falhas — são informação. Quando um talhão não passou por reforma, o campo `TP_REFORMA` naturalmente ficará vazio; forçar um preenchimento artificial distorceria a leitura operacional dos dados. A solução adotada foi criar flags booleanas que tornam essa condição explícita e consultável, sem tocar nos valores originais.

A lógica é uniforme: a flag assume `True` quando todas as colunas do grupo analisado estão simultaneamente nulas.

| Flag | Colunas analisadas | % True (part 2) | % True (part 4) | Interpretação |
|---|---|---|---|---|
| `flag_bloco_ausente` | `BLOCO` | 23,5% | 23,5% | Talhão sem bloco definido |
| `flag_caract_ausente` | `DT_CARACT`, `CARACT` | 99,8% | 99,8% | Sem registro de caracterização |
| `flag_cana_ent_ausente` | `CANA_ENT` | 98,9% | 98,9% | Sem entrega de cana na safra |
| `flag_tp_reforma_ausente` | `TP_REFORMA` | 69,3% | 69,6% | Talhão sem reforma |
| `flag_reestimativa_ausente` | `AREA_REEST`, `TCH_REEST`, `TON_REEST` | 56,2% | 55,5% | Sem reestimativa registrada |
| `flag_muda_ausente` | `AREA_MUDA`, `TCH_MUDA`, `TON_MUDA` | 94,0% | 94,4% | Não destinado à muda |
| `flag_colheita_ausente` | `AREA_COLHIDA` | 38,6% | 38,2% | Talhão ainda não colhido |
| `flag_talhao_aberto` | `DATA_FECHA` | 35,5% | 35,1% | Ciclo ainda aberto |

### Implementação

```python
def criar_flags_negocio(df: pd.DataFrame) -> pd.DataFrame:
    grupos = {
        "flag_bloco_ausente":          ["BLOCO"],
        "flag_caract_ausente":         ["DT_CARACT", "CARACT"],
        "flag_cana_ent_ausente":       ["CANA_ENT"],
        "flag_tp_reforma_ausente":     ["TP_REFORMA"],
        "flag_reestimativa_ausente":   ["AREA_REEST", "TCH_REEST", "TON_REEST"],
        "flag_muda_ausente":           ["AREA_MUDA", "TCH_MUDA", "TON_MUDA"],
        "flag_colheita_ausente":       ["AREA_COLHIDA"],
        "flag_talhao_aberto":          ["DATA_FECHA"],
    }

    for flag, cols in grupos.items():
        df[flag] = df[cols].isna().all(axis=1)

    return df
```

---

## 4. Imputação por Mediana para Dados Realmente Faltantes

Quando a ausência não é esperada — quando um campo deveria estar preenchido mas não está —, a estratégia é imputar. Três colunas se enquadram nessa categoria: `AREA_PROD`, `TCH_PROD` e `TON_ESTIM`. Todo talhão ativo deveria ter área de produção e produtividade estimada; a ausência aqui é falha de preenchimento, não condição operacional.

A imputação é feita pela mediana calculada dentro de cada grupo `UNID_IND` (unidade industrial), e não pela mediana global do dataset. O motivo é direto: valores de produção diferem substancialmente entre unidades industriais, e usar uma mediana única introduziria viés sistemático para unidades com perfis muito acima ou abaixo da média agregada.

| Coluna | Part 2: nulos imputados | Part 4: nulos imputados | Justificativa |
|--------|------------------------|------------------------|---------------|
| `AREA_PROD` | 14.210 | 4.900 | Todo talhão ativo deveria ter área de produção |
| `TCH_PROD` | 14.210 | 4.900 | Todo talhão ativo deveria ter TCH estimado |
| `TON_ESTIM` | 14.210 | 4.900 | Derivado de AREA_PROD x TCH_PROD |

```python
def imputar_mediana_por_unidade(df: pd.DataFrame, colunas: list) -> pd.DataFrame:
    for col in colunas:
        mediana_por_unidade = df.groupby("UNID_IND")[col].transform("median")
        df[col] = df[col].fillna(mediana_por_unidade)
    return df
```

> **Fallback:** no caso extremo em que uma `UNID_IND` inteira não possua nenhum valor para determinada coluna, a mediana global do dataset é usada como segundo nível de imputação.

---

## 5. Colunas Geográficas: Nulos a Preservar

Coordenadas e atributos de zoneamento formam uma categoria à parte. A ausência nesses campos não decorre de erro de processo, mas de lacunas no levantamento GPS cadastrado no SIG da Atvos — talhões sem georeferenciamento simplesmente não têm latitude nem longitude disponíveis. Imputar valores geográficos sem uma fonte primária confiável seria metodologicamente inaceitável.

A decisão foi manter os nulos e registrar explicitamente o cruzamento previsto para a Sprint 2, via shapefile por `NUM + SETOR + TALHAO`.

| Coluna | % Nulo (part 2) | % Nulo (part 4) | Dataset sugerido para cruzamento |
|--------|-----------------|-----------------|----------------------------------|
| `LATITUDE` | 18,8% | 18,5% | Shapefile de talhões / IBGE |
| `LONGITUDE` | 18,8% | 18,5% | Shapefile de talhões / IBGE |
| `ZONA_AGRO_ECOLOGICA` | 17,7% | 18,3% | Zoneamento agrícola MAPA |
| `DESC_ZONA` | 17,7% | 18,3% | Par com ZONA_AGRO_ECOLOGICA |
| `DESC_AMBIENTE` | 36,1% | 35,5% | Dataset de análise de solo |

---

## 6. Nulos Residuais de Baixo Impacto

Algumas colunas apresentam percentuais de nulos suficientemente baixos — ou com justificativas semânticas claras — para dispensar qualquer intervenção nesta fase.

| Coluna | % Nulo | Decisão |
|--------|---------|---------|
| `AREA_DANO` | ~0,1% | Manter |
| `TIPO_CONTRATO` | ~0,1% | Manter |
| `FORNEC` | ~0,1% | Manter |
| `OBJETIVO` | ~0,5% | Manter |
| `SISTEMA_COL` | ~0,6% | Manter |
| `MAN_HIPOT` | ~2,8% | Manter (categórica; "A Definir" é valor operacionalmente válido) |
| `SIST_PLANT` | ~2,8% | Manter |
| `ULT_CORTE` | ~5,5% | Manter (data — talhões sem corte anterior registrado) |
| `DATA_PLANTIO` | ~10,3% | Manter (data — talhões em processo de reforma podem não ter data de plantio) |

---

## 7. Transformações Complementares

Além do tratamento de nulos, três outros tipos de transformação foram aplicados sistematicamente ao dataset durante a geração da camada Silver.

| Transformação | Função | Detalhe |
|---------------|--------|---------|
| Correção de encoding | `corrigir_encoding()` | Corrige double-encoding latin-1/UTF-8 em colunas texto |
| Padronização de texto | `padronizar_texto()` | `str.strip()` em todas as colunas object |
| Padronização de datas | `padronizar_datas()` | Converte colunas com `data`/`date`/`dt_` no nome para `datetime64` |
| Formato de saída | `salvar_silver()` | Parquet em `data/processed/` |

---

## 8. Checklist de Validação Pós-Limpeza

Antes de persistir qualquer arquivo Silver em disco, o script `run_processing.py` executa um conjunto de verificações automáticas. Qualquer falha bloqueia a escrita do Parquet e gera um `WARNING` no log para revisão manual — o objetivo é garantir que nenhum dataset defeituoso avance silenciosamente no pipeline.

| Validação | Método | Resultado esperado |
|-----------|--------|--------------------|
| Nenhuma coluna 100% nula restante | `df.isna().all().sum() == 0` | `True` |
| Colunas de imputação sem nulos | `df[["AREA_PROD","TCH_PROD","TON_ESTIM"]].isna().sum() == 0` | `True` |
| Todas as flags de negócio presentes | `all(f in df.columns for f in flags)` | `True` |
| `CHAVESIG` sem duplicatas | `df["CHAVESIG"].is_unique` | `True` |
| `AREA_HA` > 0 em 100% das linhas | `(df["AREA_HA"] > 0).all()` | `True` |
| `TCH_PROD` dentro de faixa agronômica | `df["TCH_PROD"].between(5, 200).all()` | `True` (pós-imputação) |
| Datas em formato correto | `df.select_dtypes("datetime64").notna().mean() > 0.5` | `True` |
