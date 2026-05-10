---
title: "Dicionário de Dados"
sidebar_position: 3
---

# Dicionário de Dados — Camada Silver

**Última atualização:** 2026-05-07  
**Responsável:** Atvos G2  
**Integrantes:** Guilherme Ludovico, Haila, Guilherme, João Glauco, Gregory 
**Critério de pronto:** todas as colunas dos DataFrames Silver documentadas com faixa esperada e regra de negócio associada

---

## Dataset: Correcao_talhoes_para_unificacao_silver

**Arquivo:** `data/processed/Correcao_talhoes_para_unificacao_silver.parquet`  
**Linhas:** 23.599 | **Colunas:** 8

Este dataset registra o histórico de reorganizações do canavial: para cada talhão que foi reformado ou unificado, uma linha indica a identidade original (origem) e a identidade resultante (destino). A ausência total de nulos torna este arquivo o mais limpo da cadeia — nenhuma transformação de valores foi necessária, apenas correção de encoding.

| Coluna | Descrição | Tipo | Unidade | Faixa esperada | Regra de negócio | Fonte original |
|--------|-----------|------|---------|----------------|-----------------|----------------|
| `Safra_Origem` | Safra do talhão de origem | int64 | — | Ex: 22324 | Formato AASSSS (ano início + ano fim) | Correcao_talhoes_para_unificacao.xlsx |
| `Faz_Origem` | Código numérico da fazenda de origem | int64 | — | Ex: 110001 | Deve existir no inventário como `NUM` | Correcao_talhoes_para_unificacao.xlsx |
| `Setor_Origem` | Setor da fazenda de origem | int64 | — | >= 1 | Deve existir no inventário como `SETOR` | Correcao_talhoes_para_unificacao.xlsx |
| `Talhao_Origem` | Número do talhão de origem | int64 | — | >= 1 | Deve existir no inventário como `TALHAO` | Correcao_talhoes_para_unificacao.xlsx |
| `Faz_Destino` | Código numérico da fazenda de destino | int64 | — | Ex: 117001 | Talhão unificado ou reformado destino | Correcao_talhoes_para_unificacao.xlsx |
| `Setor_Destino` | Setor da fazenda de destino | int64 | — | >= 1 | Par com Faz_Destino | Correcao_talhoes_para_unificacao.xlsx |
| `Talhao_Destino` | Número do talhão de destino | int64 | — | >= 1 | Par com Faz_Destino + Setor_Destino | Correcao_talhoes_para_unificacao.xlsx |
| `Motivo` | Motivo da correção de talhão | str | — | "1-Reforma", "2-Unificação" | Classificação operacional da Atvos | Correcao_talhoes_para_unificacao.xlsx |

---

## Dataset: Inventario_atvos_silver (parts 1, 2, 3 e 4 — estrutura idêntica)

**Arquivos:**
- `data/processed/Inventario_atvos_21_27_part_1_silver.parquet` — 50.000 linhas, 75 colunas
- `data/processed/Inventario_atvos_21_27_part_2_silver.parquet` — 50.000 linhas, 75 colunas
- `data/processed/Inventario_atvos_21_27_part_3_silver.parquet` — 50.000 linhas, 75 colunas
- `data/processed/Inventario_atvos_21_27_part_4_silver.parquet` — 17.426 linhas, 75 colunas

As quatro partes compartilham schema idêntico. A documentação a seguir organiza as colunas por domínio temático, refletindo a estrutura lógica do negócio canavieiro: primeiro a identidade do registro, depois sua localização física e contratual, depois as características culturais e de manejo, e por fim os dados de produção e encerramento do ciclo.

---

### Identificadores e Chaves

Colunas que definem a identidade única de cada registro e as relações com outras tabelas. `CHAVESIG` é a chave primária; `NUM`, `SETOR` e `TALHAO` formam a chave composta de junção com o arquivo de correções.

| Coluna | Descrição | Tipo | Unidade | Faixa esperada | Regra de negócio | Fonte original |
|--------|-----------|------|---------|----------------|-----------------|----------------|
| `CHAVESIG` | Identificador único do talhão no SIG | int64 | — | Único por linha | PK — nunca deve se repetir dentro de uma parte | Inventario_atvos_21_27_part_*.xlsx |
| `CHAVE` | Chave legível (NUM-SETOR-TALHAO) | str | — | Ex: "410149-1-8" | Derivada; usada para leitura humana | Inventario_atvos_21_27_part_*.xlsx |
| `SAFRA` | Código da safra agrícola | int64 | — | Ex: 22122, 22223 | Formato AASSSS; incrementa a cada ano-safra | Inventario_atvos_21_27_part_*.xlsx |
| `EMPRESA` | Código numérico da unidade industrial | int64 | — | Ex: 21, 31, 41 | Igual a `UNID_IND` — duas representações da mesma FK | Inventario_atvos_21_27_part_*.xlsx |
| `DESC_EMPRESA` | Sigla da unidade industrial | str | — | Ex: "UMV", "URC", "UEL" | Texto controlado pela Atvos | Inventario_atvos_21_27_part_*.xlsx |
| `UndGerencial` | Unidade gerencial (igual a DESC_EMPRESA) | str | — | Ex: "UMV" | Redundante com DESC_EMPRESA; manter para compatibilidade | Inventario_atvos_21_27_part_*.xlsx |
| `NUM` | Código numérico da fazenda | int64 | — | Ex: 410149 | FK para Correcao_talhoes via `Faz_Origem` | Inventario_atvos_21_27_part_*.xlsx |
| `SETOR` | Número do setor dentro da fazenda | int64 | — | >= 1 | FK composta com NUM e TALHAO | Inventario_atvos_21_27_part_*.xlsx |
| `TALHAO` | Número do talhão dentro do setor | int64 | — | >= 1 | FK composta com NUM e SETOR | Inventario_atvos_21_27_part_*.xlsx |
| `UNID_IND` | Código da unidade industrial (igual a EMPRESA) | int64 | — | Ex: 21, 31, 41 | Usado como agrupador na imputação por mediana | Inventario_atvos_21_27_part_*.xlsx |
| `CD_FORNEC` | Código do fornecedor | int64 | — | Ex: 1031551 | FK para cadastro de fornecedores (externo) | Inventario_atvos_21_27_part_*.xlsx |

---

### Localização e Arranjo Contratual

Colunas que descrevem onde o talhão está situado, sob que tipo de propriedade opera e com quem a usina mantém relação contratual.

| Coluna | Descrição | Tipo | Unidade | Faixa esperada | Regra de negócio | Fonte original |
|--------|-----------|------|---------|----------------|-----------------|----------------|
| `FAZENDA` | Nome da fazenda | str | — | Texto livre | Deve ser consistente com `NUM` | Inventario_atvos_21_27_part_*.xlsx |
| `TIPO_PROP` | Tipo de propriedade | str | — | PARC, FORNSUPAR, etc. | Afeta modelo contratual da usina com o produtor | Inventario_atvos_21_27_part_*.xlsx |
| `TIPO_CONTRATO` | Tipo de contrato com fornecedor | str | — | PARCERIA, SPOT, etc. | Null (~0,1%) = sem contrato formalizado | Inventario_atvos_21_27_part_*.xlsx |
| `ADMIN` | Administração (própria ou fornecedor) | str | — | "CANA PROPRIA", "FORNECEDOR" | Determina responsabilidade operacional do talhão | Inventario_atvos_21_27_part_*.xlsx |
| `FORNEC` | Nome do fornecedor | str | — | Texto livre | Null quando `ADMIN = "CANA PROPRIA"` | Inventario_atvos_21_27_part_*.xlsx |

---

### Características Físicas do Talhão

Colunas que descrevem as propriedades físicas, edáficas e geográficas do talhão. Aproximadamente 18–36% dos atributos geográficos estão ausentes por falta de levantamento no SIG; o enriquecimento está previsto para a Sprint 2.

| Coluna | Descrição | Tipo | Unidade | Faixa esperada | Regra de negócio | Fonte original |
|--------|-----------|------|---------|----------------|-----------------|----------------|
| `AREA_HA` | Área total do talhão | float64 | ha | > 0 | Nunca deve ser zero ou negativo | Inventario_atvos_21_27_part_*.xlsx |
| `AREA_DANO` | Área danificada | float64 | ha | `>= 0, <= AREA_HA` | Zero é valor válido (sem dano) | Inventario_atvos_21_27_part_*.xlsx |
| `DE_OCUP` | Descrição da ocupação | str | — | "Cana de Açúcar" | Valor praticamente constante no dataset | Inventario_atvos_21_27_part_*.xlsx |
| `DE_TP_SOLO` | Tipo de solo | str | — | Texto livre, ex: "Latossolo..." | Classificação pedológica da área | Inventario_atvos_21_27_part_*.xlsx |
| `AMBIENTE` | Código do ambiente de produção | str | — | Letra única: A–G | Classificação interna da Atvos por aptidão agrícola | Inventario_atvos_21_27_part_*.xlsx |
| `DESC_AMBIENTE` | Descrição do ambiente (textura do solo) | str | — | "Arenoso", "Argiloso", etc. | ~36% nulo — depende de levantamento de solo (Sprint 2) | Inventario_atvos_21_27_part_*.xlsx |
| `ESPAC` | Espaçamento de plantio | str | — | Ex: "1,5 Mts", "0,90x1,50m" | Formato não padronizado — normalizar em Sprint 2 | Inventario_atvos_21_27_part_*.xlsx |
| `LATITUDE` | Latitude do centróide do talhão | str | graus decimais | -33 a +5 (Brasil) | ~18,5% nulo — sem GPS cadastrado no SIG | Inventario_atvos_21_27_part_*.xlsx |
| `LONGITUDE` | Longitude do centróide do talhão | str | graus decimais | -74 a -32 (Brasil) | Par com LATITUDE | Inventario_atvos_21_27_part_*.xlsx |
| `BLOCO` | Bloco de colheita | float64 | — | >= 1 (inteiros) | Null quando `flag_bloco_ausente = True` | Inventario_atvos_21_27_part_*.xlsx |
| `ZONA_AGRO_ECOLOGICA` | Código da zona agroecológica | float64 | — | Ex: 1.0, 2.0, 99.0 | ~18% nulo — sem cobertura de zoneamento | Inventario_atvos_21_27_part_*.xlsx |
| `DESC_ZONA` | Descrição da zona agroecológica | str | — | Ex: "Bonsucro - NAO" | Par com ZONA_AGRO_ECOLOGICA | Inventario_atvos_21_27_part_*.xlsx |
| `DIST_TERRA` | Distância do talhão à usina por estrada de terra | float64 | km | >= 0 | Componente do custo logístico de transporte | Inventario_atvos_21_27_part_*.xlsx |
| `DIST_ASFALTO` | Distância do talhão à usina por asfalto | float64 | km | >= 0 | Componente do custo logístico de transporte | Inventario_atvos_21_27_part_*.xlsx |
| `DIST_HIDR` | Distância hidroviária | int64 | km | >= 0 | 0 para talhões sem acesso hidroviário | Inventario_atvos_21_27_part_*.xlsx |

---

### Cultura e Manejo

Colunas que descrevem a variedade plantada, o estágio do ciclo e as práticas de manejo adotadas. São informações centrais para modelagem de produtividade e planejamento de colheita.

| Coluna | Descrição | Tipo | Unidade | Faixa esperada | Regra de negócio | Fonte original |
|--------|-----------|------|---------|----------------|-----------------|----------------|
| `VARIED` | Variedade de cana plantada | str | — | Ex: "RB867515", "RB92579" | Código de variedade registrado na Ridesa/CTC | Inventario_atvos_21_27_part_*.xlsx |
| `CATEGORIA` | Categoria do talhão | str | — | "Cana Soca", "Formação", "Muda" | Determina ciclo de vida e regras de colheita | Inventario_atvos_21_27_part_*.xlsx |
| `ESTAGIO` | Estágio do ciclo da cana | str | — | Ex: "3º Corte", "Formação 18m" | Número do corte ou fase de formação | Inventario_atvos_21_27_part_*.xlsx |
| `NO_CORTE` | Número do corte | int64 | — | 0 (formação) a ~8 | 0 = plantio/formação; >=1 = soca | Inventario_atvos_21_27_part_*.xlsx |
| `DATA_PLANTIO` | Data do plantio da cana | datetime64 | — | >= 2010 | ~10,3% nulo em talhões em processo de reforma | Inventario_atvos_21_27_part_*.xlsx |
| `MAN_HIPOT` | Manejo hipotético de maturação | str | — | "Precoce", "Média", "Tardia", "A Definir" | Determina janela de corte planejada | Inventario_atvos_21_27_part_*.xlsx |
| `SIST_PLANT` | Sistema de plantio | str | — | "Mecanizado", "Plan.Meiosi Viv.Sec." | Define mecanização e custo de implantação | Inventario_atvos_21_27_part_*.xlsx |
| `TP_IRRIGA` | Tipo de irrigação | str | — | "S/Info", "Hidroroll", etc. | "S/Info" = sem informação, não é ausência de irrigação | Inventario_atvos_21_27_part_*.xlsx |
| `Vinhaca_E` | Aplicação de vinhaça (S/N) | str | — | "S", "N" | Subproduto do processo industrial; impacta solo | Inventario_atvos_21_27_part_*.xlsx |
| `TORTA` | Aplicação de torta de filtro (S/N) | str | — | "S", "N" | Biofertilizante sólido da usina | Inventario_atvos_21_27_part_*.xlsx |
| `SISTEMA_COL` | Código do sistema de colheita | float64 | — | Ex: 4.0 | Mapeamento de código para descrição necessário em Sprint 2 | Inventario_atvos_21_27_part_*.xlsx |
| `FRENTE` | Código da frente de colheita | int64 | — | >= 1; 99 = sem frente | Agrupa talhões sob mesma equipe de colheita | Inventario_atvos_21_27_part_*.xlsx |

---

### Reforma

Colunas que sinalizam mudanças estruturais no talhão — expansões, devoluções e replantios. A coluna `TP_REFORMA` é nula em ~69% dos registros, o que é esperado: a maioria dos talhões está em produção normal, sem reforma em curso.

| Coluna | Descrição | Tipo | Unidade | Faixa esperada | Regra de negócio | Fonte original |
|--------|-----------|------|---------|----------------|-----------------|----------------|
| `Expansao` | Flag de expansão de área | str | — | "S", "N" | S = área nova incorporada ao canavial | Inventario_atvos_21_27_part_*.xlsx |
| `Devolucao` | Flag de devolução de área | str | — | "S", "N" | S = área retirada do canavial (arrendamento encerrado etc.) | Inventario_atvos_21_27_part_*.xlsx |
| `Reforma` | Flag de reforma do talhão | str | — | "S", "N" | S = replantio previsto ou em execução | Inventario_atvos_21_27_part_*.xlsx |
| `TP_REFORMA` | Tipo de reforma | str | — | "Convencional", "Inverno", "18 Meses" | Null quando `Reforma = 'N'`; sinalizado por `flag_tp_reforma_ausente` | Inventario_atvos_21_27_part_*.xlsx |

---

### Produção Estimada

Estas três colunas formam o núcleo quantitativo do planejamento de safra. Foram as únicas do inventário para as quais se decidiu pela imputação por mediana — por serem dados estruturalmente obrigatórios em talhões ativos, e não ausências esperadas de negócio.

| Coluna | Descrição | Tipo | Unidade | Faixa esperada | Regra de negócio | Fonte original |
|--------|-----------|------|---------|----------------|-----------------|----------------|
| `AREA_PROD` | Área de produção estimada | float64 | ha | `> 0, <= AREA_HA` | Imputada por mediana de `UNID_IND`; 0% nulo na Silver | Inventario_atvos_21_27_part_*.xlsx |
| `TCH_PROD` | Toneladas de cana por hectare estimadas | float64 | t/ha | 20 – 150 | Imputada por mediana de `UNID_IND`; 0% nulo na Silver | Inventario_atvos_21_27_part_*.xlsx |
| `TON_ESTIM` | Toneladas totais estimadas (AREA_PROD × TCH_PROD) | float64 | t | > 0 | Imputada por mediana de `UNID_IND`; 0% nulo na Silver | Inventario_atvos_21_27_part_*.xlsx |

---

### Reestimativa de Produção

Campos preenchidos apenas quando ocorre uma revisão formal da estimativa de safra — evento que afeta aproximadamente 44–45% dos registros.

| Coluna | Descrição | Tipo | Unidade | Faixa esperada | Regra de negócio | Fonte original |
|--------|-----------|------|---------|----------------|-----------------|----------------|
| `AREA_REEST` | Área na reestimativa de produção | float64 | ha | > 0 | ~56% nulo = sem reestimativa; sinalizado por `flag_reestimativa_ausente` | Inventario_atvos_21_27_part_*.xlsx |
| `TCH_REEST` | TCH reestimado | float64 | t/ha | 20 – 150 | Par com AREA_REEST | Inventario_atvos_21_27_part_*.xlsx |
| `TON_REEST` | Toneladas reestimadas | float64 | t | > 0 | Par com AREA_REEST; coerência: TON_REEST ≈ AREA_REEST × TCH_REEST | Inventario_atvos_21_27_part_*.xlsx |

---

### Muda e Formação

Colunas preenchidas exclusivamente em talhões destinados à produção de mudas — minoria expressiva: aproximadamente 94% dos registros não se enquadram nessa categoria.

| Coluna | Descrição | Tipo | Unidade | Faixa esperada | Regra de negócio | Fonte original |
|--------|-----------|------|---------|----------------|-----------------|----------------|
| `AREA_MUDA` | Área destinada a muda | float64 | ha | > 0 | ~94% nulo = talhão não é viveiro; sinalizado por `flag_muda_ausente` | Inventario_atvos_21_27_part_*.xlsx |
| `TCH_MUDA` | TCH de muda | float64 | t/ha | 20 – 100 | Par com AREA_MUDA | Inventario_atvos_21_27_part_*.xlsx |
| `TON_MUDA` | Toneladas de muda | float64 | t | > 0 | Par com AREA_MUDA | Inventario_atvos_21_27_part_*.xlsx |

---

### Colheita e Encerramento do Ciclo

Colunas que registram o desfecho operacional do talhão na safra: o quanto foi efetivamente colhido, quando o ciclo foi encerrado e quanto foi entregue à usina. A alta proporção de nulos em `CANA_ENT` (~99%) é esperada: entrega física à usina é evento raro na granularidade por talhão.

| Coluna | Descrição | Tipo | Unidade | Faixa esperada | Regra de negócio | Fonte original |
|--------|-----------|------|---------|----------------|-----------------|----------------|
| `AREA_COLHIDA` | Área efetivamente colhida | float64 | ha | `> 0, <= AREA_HA` | ~38% nulo = talhão ainda não colhido; sinalizado por `flag_colheita_ausente` | Inventario_atvos_21_27_part_*.xlsx |
| `OBJETIVO` | Objetivo do talhão na safra | str | — | "Safra", "Muda", "Sem Objetivo" | Define destinação da produção | Inventario_atvos_21_27_part_*.xlsx |
| `SIT_TALHAO` | Situação atual do talhão | str | — | "Fechado", "Cana Planta", etc. | Estado operacional no momento da extração | Inventario_atvos_21_27_part_*.xlsx |
| `DATA_FECHA` | Data de fechamento do ciclo | datetime64 | — | >= 2018 | ~35% nulo = ciclo ainda aberto; sinalizado por `flag_talhao_aberto` | Inventario_atvos_21_27_part_*.xlsx |
| `CANA_ENT` | Cana entregue na usina | float64 | t | > 0 | ~99% nulo = talhão não entregou cana; sinalizado por `flag_cana_ent_ausente` | Inventario_atvos_21_27_part_*.xlsx |
| `ULT_CORTE` | Data do último corte registrado | datetime64 | — | >= 2010 | ~5,5% nulo = sem corte anterior (plantio novo) | Inventario_atvos_21_27_part_*.xlsx |

---

### Ocorrências e Caracterizações

Colunas de registro de eventos pontuais. `DT_CARACT` e `CARACT` apresentam o maior percentual de nulos de todo o dataset (~99,8%) — o que reflete a raridade do evento de caracterização formal, não falha de preenchimento.

| Coluna | Descrição | Tipo | Unidade | Faixa esperada | Regra de negócio | Fonte original |
|--------|-----------|------|---------|----------------|-----------------|----------------|
| `FG_OCORREN` | Flag de ocorrência (S=sim, F=fim) | str | — | "S", "F" | "F" = evento de ocorrência encerrado | Inventario_atvos_21_27_part_*.xlsx |
| `DT_OCORREN` | Data da ocorrência registrada | datetime64 | — | >= 2020 | Par com FG_OCORREN | Inventario_atvos_21_27_part_*.xlsx |
| `DT_CARACT` | Data do evento de caracterização | datetime64 | — | >= 2025 | ~99,8% nulo = sem evento registrado; sinalizado por `flag_caract_ausente` | Inventario_atvos_21_27_part_*.xlsx |
| `CARACT` | Tipo de caracterização | str | — | "TRANSF. AREA FORNECEDOR", etc. | Par com DT_CARACT | Inventario_atvos_21_27_part_*.xlsx |
| `Data_Geracao_Planilha` | Timestamp de geração do arquivo | datetime64 | — | 2026-04-23 | Constante em todo o dataset — snapshot único | Inventario_atvos_21_27_part_*.xlsx |

---

### Flags de Negócio (derivadas na Silver)

Estas oito colunas não existem no raw. São criadas durante o processamento Silver para tornar explícito o significado operacional das ausências identificadas — permitindo que análises downstream filtrem ou segmentem os dados sem precisar reescrever as condições de nulidade toda vez.

| Coluna | Descrição | Tipo | Unidade | Faixa esperada | Regra de negócio | Fonte original |
|--------|-----------|------|---------|----------------|-----------------|----------------|
| `flag_bloco_ausente` | True quando BLOCO é nulo (talhão sem bloco de colheita) | bool | — | True/False | ~23,5% True — talhões em formação ou sem programação de corte | Derivada |
| `flag_caract_ausente` | True quando DT_CARACT e CARACT são nulos | bool | — | True/False | ~99,8% True — evento raro na base | Derivada |
| `flag_cana_ent_ausente` | True quando CANA_ENT é nulo (sem entrega registrada) | bool | — | True/False | ~98,9% True — coluna registra entrega física à usina | Derivada |
| `flag_tp_reforma_ausente` | True quando TP_REFORMA é nulo (sem reforma) | bool | — | True/False | ~69% True — a maioria dos talhões não está em reforma | Derivada |
| `flag_reestimativa_ausente` | True quando AREA_REEST, TCH_REEST e TON_REEST são nulos | bool | — | True/False | ~56% True — reestimativa ocorre apenas em momentos específicos do ciclo | Derivada |
| `flag_muda_ausente` | True quando AREA_MUDA, TCH_MUDA e TON_MUDA são nulos | bool | — | True/False | ~94% True — minoria dos talhões é destinada a viveiro | Derivada |
| `flag_colheita_ausente` | True quando AREA_COLHIDA é nulo | bool | — | True/False | ~38% True — talhões com colheita futura ou cancelada | Derivada |
| `flag_talhao_aberto` | True quando DATA_FECHA é nulo (ciclo não encerrado) | bool | — | True/False | ~35% True — safra ainda em andamento no momento da extração | Derivada |
