---
title: "Motor de Regras — Camada Gold"
sidebar_position: 3
---

# Motor de Regras Agronômicas — Camada Gold

**Versão:** 2.0  
**Última atualização:** 2026-05-22  
**Responsável:** Atvos G2  
**Relacionado à:** Task 2.5 — Mapa Lógico de Regras

> Losangos = decisões | Retângulos = ações | Círculos arredondados = entradas e saídas.  
> Todos os fluxos recebem um único talhão como entrada e retornam uma **orientação**, um **valor calculado** (quando aplicável) e um **identificador de regra**.

---

## Visão Geral — Pipeline Gold

Para cada talhão do inventário Silver, o pipeline executa os 4 módulos corretivos em sequência. A Janela de Plantio é calculada separadamente e adicionada como colunas ao resultado final.

```mermaid
flowchart LR
    A([inventario_silver.csv]) --> B[Para cada talhão]
    B --> C[Calagem]
    B --> D[Gessagem]
    B --> E[Fosfatagem]
    B --> F[Erradicação]
    B --> G[Janela de Plantio]
    C & D & E & F --> H{Algum processo\nnecessário?}
    H -- Sim --> I[Manter apenas linhas\ncom ação necessária]
    H -- Não --> J[1 linha: nenhum processo]
    G --> K[Colunas janela_orientacao\ne janela_regra]
    I & J & K --> L([orientacoes_YYYY-MM-DD\n.parquet + .csv])
```

---

## Schema do Output

O arquivo gerado está em **formato longo**: cada talhão gera entre 1 e 4 linhas, uma por processo com ação necessária.

| Coluna | Tipo | Descrição |
|---|---|---|
| `id_talhao` | string | Identificador único do talhão |
| `unidade` | string | Código da unidade industrial |
| `janela_orientacao` | string | Texto da janela de plantio recomendada |
| `janela_regra` | string | Identificador da regra de janela disparada |
| `data_geracao` | string | Data de geração no formato `YYYY-MM-DD` |
| `processo` | string | `calagem`, `gessagem`, `fosfatagem`, `erradicacao` ou `nenhum processo` |
| `orientacao` | string | Texto da recomendação agronômica |
| `valor_calculado` | float / null | Dose numérica (t/ha ou kg/ha) — apenas calagem e gessagem |
| `regra_acionada` | string | Identificador da regra disparada |

> Linhas com resultado `sem_necessidade_*` ou `nao_aplicavel_*` são suprimidas quando outros processos do mesmo talhão exigem ação. Talhões onde nenhum processo é necessário geram uma única linha com `processo = "nenhum processo"` e `regra_acionada = "sem_necessidade_todos"`.

---

## Processo 1 — Calagem

**Objetivo:** definir a dose e o tipo de calcário para elevar a saturação por bases (V%) do solo a 60%, garantindo disponibilidade de nutrientes para a cana.

**Fórmula:** `NC (t/ha) = CTC × (V_alvo − V_atual) / (PRNT × 10)`

```mermaid
flowchart TD

    A([Talhão recebido]) --> B{V1, CTC1 ou mg1\nsão nulos ou NaN?}

    B -- Sim --> Z1([orientacao: dado ausente ou inválido\nregra: dado_ausente_V1\nou dado_ausente_CTC1\nou dado_ausente_mg1])

    B -- Não --> C[Extrair V1, CTC1, mg1\nda análise de solo]

    C --> D{V_atual menor\nque 60%?}

    D -- Não --> Z2([NC = 0\nCalagem não necessária\nregra: sem_necessidade_calagem])

    D -- Sim --> E[Calcular NC pela\nfórmula IAC/Embrapa\nNC = CTC × 60 - V / 1000\nLimitar a 4 t/ha]

    E --> F{mg trocável\nmenor que 5 mmolc/dm³?}

    F -- Sim --> G[Calcário DOLOMÍTICO\nobrigatório\nNC mínimo = 1 t/ha]

    F -- Não --> H[Calcário calcítico\nou dolomítico]

    G & H --> I{Categoria\ndo talhão?}

    I -- Formação\ncana planta --> J([Aplicação INCORPORADA\n60 a 90 dias antes do plantio\nregra: calagem_incorporada_dolomitico\nou calagem_incorporada_calcitico])

    I -- Cana Soca\nou outro --> K([NC = NC × 0,5\nAplicação SUPERFICIAL\ninício do período chuvoso\nregra: calagem_superficial_dolomitico\nou calagem_superficial_calcitico])
```

---

## Processo 2 — Gessagem

**Objetivo:** corrigir a subsuperfície do solo (25–50 cm) com gesso agrícola, reduzindo toxidez por alumínio e aumentando cálcio em profundidade.

**Fórmula:** `dose_gesso (kg/ha) = argila (g/kg) × 5`

```mermaid
flowchart TD

    A([Talhão recebido]) --> B{Categoria é\nFormação?\ncana planta}

    B -- Não --> Z1([Gessagem aplicável\napenas na cana planta\nregra: nao_aplicavel_categoria])

    B -- Sim --> C{ca2, al2 ou sb2\nsão nulos ou NaN?}

    C -- Sim --> Z2([orientacao: dado ausente ou inválido\nregra: dado_ausente_ca2\nou dado_ausente_al2\nou dado_ausente_sb2])

    C -- Não --> D[Extrair ca2, al2, sb2\ncamada 25 a 50 cm]

    D --> E[Calcular saturação de Al\nsat_al = al2 / sb2+al2 × 100]

    E --> F{ca2 menor que 4\nou sat_al maior que 40%?}

    F -- Não --> Z3([Gesso não necessário\nCa e Al dentro dos limites\nregra: sem_necessidade_gessagem])

    F -- Sim --> G{Qual o gatilho?}

    G -- ca2 baixo\nE sat_al alto --> H1([regra: gessagem_ca_baixo_e_al_alto])
    G -- apenas ca2\nbaixo --> H2([regra: gessagem_ca_subsuperficial_baixo])
    G -- apenas sat_al\nalto --> H3([regra: gessagem_saturacao_al_alta])

    H1 & H2 & H3 --> I{tipo_solo\nidentificado?}

    I -- Muito Argiloso --> J1[argila = 550 g/kg\ndose = 2750 kg/ha]
    I -- Argiloso --> J2[argila = 420 g/kg\ndose = 2100 kg/ha]
    I -- Médio --> J3[argila = 250 g/kg\ndose = 1250 kg/ha]
    I -- Arenoso --> J4[argila = 150 g/kg\ndose = 750 kg/ha]
    I -- A Definir --> J5[argila = 300 g/kg\ndose = 1500 kg/ha]

    J1 & J2 & J3 & J4 & J5 --> K([Aplicar dose calculada\nna grade niveladora\nantes do plantio])
```

---

## Processo 3 — Fosfatagem

**Objetivo:** garantir fósforo disponível para a cana planta na fase de enraizamento. Como o fósforo é imóvel no solo, deve ser aplicado diretamente no sulco de plantio.

```mermaid
flowchart TD

    A([Talhão recebido]) --> B{Categoria é\nFormação?\ncana planta}

    B -- Não --> Z1([Fosfatagem aplicável\napenas na cana planta\nregra: nao_aplicavel_categoria])

    B -- Sim --> C{p1 é nulo ou NaN?\nDados de solo ausentes}

    C -- Sim --> Z2([orientacao: dado ausente ou inválido\nregra: dado_ausente_p1])

    C -- Não --> D[Extrair p1\nfósforo disponível\ncamada 0 a 25 cm]

    D --> E{p1 menor\nque 6 mg/dm³?}

    E -- Sim --> F([Nível MUITO BAIXO\n120 kg P₂O₅/ha\nPrioridade ALTA\nregra: fosfatagem_muito_baixo])

    E -- Não --> G{p1 entre 6\ne 12 mg/dm³?}

    G -- Sim --> H([Nível BAIXO\n80 kg P₂O₅/ha\nPrioridade MÉDIA\nregra: fosfatagem_baixo])

    G -- Não --> I{p1 entre 12\ne 25 mg/dm³?}

    I -- Sim --> J([Nível MÉDIO\n40 kg P₂O₅/ha\nPrioridade BAIXA\nregra: fosfatagem_medio])

    I -- Não --> K([P SUFICIENTE\n0 kg/ha\nSem aplicação necessária\nregra: sem_necessidade_fosfatagem])
```

**Momento de aplicação:** no sulco de plantio (100% da dose) ou pré-plantio incorporado.

---

## Processo 4 — Erradicação de Soqueira

**Objetivo:** identificar talhões de cana soca que devem ser encerrados e reformados, com base na produtividade (TCH) e na longevidade (número de cortes).

```mermaid
flowchart TD

    A([Talhão recebido]) --> B{Categoria é\nFormação?\ncana planta}

    B -- Sim --> Z1([Erradicação não aplicável\na talhões em formação\nregra: nao_aplicavel_formacao])

    B -- Não --> C{tch_prod ou no_corte\nsão nulos ou NaN?}

    C -- Sim --> Z2([orientacao: dado ausente ou inválido\nregra: dado_ausente_tch_prod\nou dado_ausente_no_corte])

    C -- Não --> D{no_corte\nmaior ou igual a 8?}

    D -- Sim --> E([REFORMA OBRIGATÓRIA\nLongevidade máxima atingida\nPrioridade ALTA\nregra: reforma_longevidade_maxima])

    D -- Não --> F{TCH menor que 55\ne no_corte maior ou igual a 3?}

    F -- Sim --> G([REFORMA RECOMENDADA\nProdutividade abaixo do limiar\nPrioridade ALTA\nregra: reforma_tch_baixo_maduro])

    F -- Não --> H{TCH menor que 55\ne no_corte menor que 3?}

    H -- Sim --> I([REFORMA RECOMENDADA\nBaixa produtividade em corte inicial\nInvestigar estabelecimento\nPrioridade MÉDIA\nregra: reforma_tch_baixo_jovem])

    H -- Não --> J{TCH maior ou igual a 55\ne no_corte maior ou igual a 6?}

    J -- Sim --> K([REFORMA PREVENTIVA\nLongevidade elevada\nProgramar reforma futura\nPrioridade BAIXA\nregra: reforma_preventiva])

    J -- Não --> L([CONTINUAR CICLO\nTalhão dentro dos critérios\nregra: sem_necessidade_reforma])

    E & G & I & K --> M{sit_talhao é\nFechado ou Cana Soca?}

    M -- Sim --> N([Dessecação INDICADA\nHerbicida pós-colheita\naté 30 dias após o último corte])

    M -- Não --> O([Verificar situação atual\ncom equipe de campo])
```

---

## Processo 5 — Janela de Plantio *(coluna, não linha)*

**Objetivo:** sugerir o período ideal de plantio (ou replantio em reforma) com base no perfil de maturação da variedade (MAN_HIPOT), visando sincronizar a colheita com os períodos de maior eficiência industrial.

> ⚠️ Este processo **não gera linhas** no output. Seu resultado é adicionado como duas colunas (`janela_orientacao` e `janela_regra`) em todas as linhas do talhão, sejam elas de processos corretivos ou `nenhum processo`.

> ⚠️ **Pendente de validação com PO ATVOS:** os meses sugeridos são baseados no calendário sucroalcooleiro do Centro-Sul do Brasil. Unidades em outras regiões podem ter janelas distintas.

```mermaid
flowchart TD

    A([Talhão recebido]) --> B{Categoria\né Muda?}

    B -- Sim --> Z1([Não aplicável\nTalhão de viveiro\nregra: janela_muda])

    B -- Não --> C{MAN_HIPOT\nestá preenchido?}

    C -- Não --> Z2([Janela indeterminada\nSem perfil de maturação\nregra: sem_dado_man_hipot])

    C -- Sim --> D{Qual o perfil\nde maturação?}

    D -- Precoce --> E[Janela: outubro a dezembro\nCiclo estimado: 12 a 14 meses]
    D -- Média --> F[Janela: janeiro a março\nCiclo estimado: 14 a 16 meses]
    D -- Tardia --> G[Janela: março a maio\nCiclo estimado: 16 a 18 meses]
    D -- A Definir --> H[Janela ampla: outubro a maio\nCiclo estimado: 12 a 18 meses\nValidar com agrônomo]

    E & F & G & H --> I{Categoria é\nFormação?\ncana planta}

    I -- Sim --> J([Estimar faixa de colheita\na partir da DATA_PLANTIO\nconfirmar calendário com equipe\nregra: janela_precoce / media / tardia])

    I -- Não --> K([Orientação para reforma futura\nPlantar no período indicado\nquando reforma for executada\nregra: janela_soca_reforma])
```

**Tabela-resumo das janelas por perfil:**

| Perfil (MAN_HIPOT) | Janela de Plantio | Ciclo Estimado | Regra |
|---|---|---|---|
| Precoce | Outubro a dezembro | 12–14 meses | `janela_precoce` |
| Média | Janeiro a março | 14–16 meses | `janela_media` |
| Tardia | Março a maio | 16–18 meses | `janela_tardia` |
| A Definir | Outubro a maio (ampla) | 12–18 meses | `janela_a_definir` |

---

## Tabela de Regras — Resumo Geral

| Processo | Regra disparada | Condição | Valor calculado |
|---|---|---|---|
| Calagem | `dado_ausente_V1` | V1 nulo ou NaN | — |
| Calagem | `dado_ausente_CTC1` | CTC1 nulo ou NaN | — |
| Calagem | `dado_ausente_mg1` | mg1 nulo ou NaN | — |
| Calagem | `calagem_incorporada_dolomitico` | V% < 60, cana planta, mg < 5 | NC em t/ha |
| Calagem | `calagem_incorporada_calcitico` | V% < 60, cana planta, mg ≥ 5 | NC em t/ha |
| Calagem | `calagem_superficial_dolomitico` | V% < 60, cana soca, mg < 5 | NC × 0,5 em t/ha |
| Calagem | `calagem_superficial_calcitico` | V% < 60, cana soca, mg ≥ 5 | NC × 0,5 em t/ha |
| Calagem | `sem_necessidade_calagem` | V% ≥ 60 | 0 t/ha |
| Gessagem | `nao_aplicavel_categoria` | Não é Formação | — |
| Gessagem | `dado_ausente_ca2` | ca2 nulo ou NaN | — |
| Gessagem | `dado_ausente_al2` | al2 nulo ou NaN | — |
| Gessagem | `dado_ausente_sb2` | sb2 nulo ou NaN | — |
| Gessagem | `gessagem_ca_baixo_e_al_alto` | Ca < 4 **e** sat Al > 40% | Dose em kg/ha |
| Gessagem | `gessagem_ca_subsuperficial_baixo` | apenas Ca < 4 | Dose em kg/ha |
| Gessagem | `gessagem_saturacao_al_alta` | apenas sat Al > 40% | Dose em kg/ha |
| Gessagem | `sem_necessidade_gessagem` | Ca e Al adequados | 0 kg/ha |
| Fosfatagem | `nao_aplicavel_categoria` | Não é Formação | — |
| Fosfatagem | `dado_ausente_p1` | p1 nulo ou NaN | — |
| Fosfatagem | `fosfatagem_muito_baixo` | P < 6 mg/dm³ | 120 kg P₂O₅/ha |
| Fosfatagem | `fosfatagem_baixo` | 6 ≤ P < 12 mg/dm³ | 80 kg P₂O₅/ha |
| Fosfatagem | `fosfatagem_medio` | 12 ≤ P < 25 mg/dm³ | 40 kg P₂O₅/ha |
| Fosfatagem | `sem_necessidade_fosfatagem` | P ≥ 25 mg/dm³ | 0 kg P₂O₅/ha |
| Erradicação | `nao_aplicavel_formacao` | Categoria = Formação | — |
| Erradicação | `dado_ausente_tch_prod` | tch_prod nulo ou NaN | — |
| Erradicação | `dado_ausente_no_corte` | no_corte nulo ou NaN | — |
| Erradicação | `reforma_longevidade_maxima` | no_corte ≥ 8 | TCH atual |
| Erradicação | `reforma_tch_baixo_maduro` | TCH < 55 e corte ≥ 3 | TCH atual |
| Erradicação | `reforma_tch_baixo_jovem` | TCH < 55 e corte < 3 | TCH atual |
| Erradicação | `reforma_preventiva` | TCH ≥ 55 e corte ≥ 6 | TCH atual |
| Erradicação | `sem_necessidade_reforma` | Dentro dos critérios | TCH atual |
| Janela plantio | `janela_muda` | Categoria = Muda | — |
| Janela plantio | `sem_dado_man_hipot` | MAN_HIPOT nulo | — |
| Janela plantio | `janela_precoce` | MAN_HIPOT = Precoce | — |
| Janela plantio | `janela_media` | MAN_HIPOT = Média | — |
| Janela plantio | `janela_tardia` | MAN_HIPOT = Tardia | — |
| Janela plantio | `janela_a_definir` | MAN_HIPOT = A Definir | — |
| Janela plantio | `janela_soca_reforma` | Cana Soca com perfil válido | — |
| *(consolidado)* | `sem_necessidade_todos` | Todos os 4 processos sem ação necessária | — |
