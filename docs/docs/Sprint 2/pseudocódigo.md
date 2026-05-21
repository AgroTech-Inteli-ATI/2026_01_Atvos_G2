# Pseudocódigo — Motor de Regras Agronômicas ATVOS
**Projeto:** Módulo de Orientações Agrícolas Data-Driven  
**Equipe:** AgroTech Inteli  
**Parceiro:** ATVOS Agroindustrial  
**Versão:** 1.0 — pendente validação com orientador e PO ATVOS  

---

## 1. O que é Pseudocódigo?

Pseudocódigo é uma forma de descrever a lógica de um algoritmo usando linguagem humana estruturada, sem seguir a sintaxe rígida de nenhuma linguagem de programação. Em vez de escrever `if V1 < 60 and categoria == "Formação":`, escrevemos `SE V_atual < 60 E talhão é cana planta:`. O resultado é um texto que qualquer pessoa com conhecimento do domínio — agrônomo, engenheiro, analista — consegue ler, entender e validar sem precisar saber programar.

Pseudocódigo usa convenções simples:

| Palavra-chave | Significado |
|---|---|
| `SE ... ENTÃO` | condição lógica (if) |
| `SENÃO SE` | condição alternativa (elif) |
| `SENÃO` | caso padrão (else) |
| `PARA CADA` | iteração sobre registros (for) |
| `RETORNAR` | saída do processo |
| `ENCERRAR` | interrompe o processamento daquele registro |
| `DEFINIÇÕES` | bloco de constantes configuráveis |
| `VERDADEIRO / FALSO` | valores booleanos |
| `MIN(...) / MAX(...)` | funções de mínimo e máximo |

---

## 2. Contextualização no Projeto

O TAP do projeto define que o Motor de Regras Agronômicas (Camada 2 da arquitetura) deve traduzir as diretrizes do **PDA (Planejamento e Desenvolvimento Agrícola)** da ATVOS em **heurísticas condicionais do tipo SE-ENTÃO**, operando ao nível de talhão para os seguintes processos:

1. Distribuição do plano de reforma anual em meses de plantio
2. Priorização de meses para o plantio segundo a matriz de aptidão
3. **Diretrizes de corretivos para cana planta** — calagem, gessagem e fosfatagem
4. **Diretrizes de erradicação de soqueira e dessecação**
5. Gestão de insumos e doses

Este documento formaliza os **processos 3 e 4** — os mais diretamente suportados pelos dados disponíveis — em pseudocódigo revisável pelo time técnico antes de qualquer linha de Python ser escrita. Essa etapa é o que o projeto denomina Task 2.2 e é pré-requisito para a Task 2.3 (implementação).

A escolha desses dois processos não é arbitrária: os corretivos de solo (calagem, gessagem, fosfatagem) são operações de alto custo e janela de execução estreita — uma vez plantado o talhão, a oportunidade de incorporar calcário no perfil se fecha por 5 a 6 anos (conforme o manual Agroadvance). Erros nessas decisões têm impacto plurianual. Já a erradicação de soqueira envolve a descontinuação de talhões inteiros, com custo de reforma elevado — razão pela qual a formalização criteriosa dessas regras é prioritária.

### Dados Disponíveis

O motor opera sobre dois conjuntos de dados fornecidos pela ATVOS:

**Inventário de Talhões** (`Inventario_atvos_21_27_part_4.xlsx`)

| Campo | Descrição |
|---|---|
| `CHAVE` | Identificador único do talhão |
| `CATEGORIA` | `"Formação"` (cana planta) ou `"Cana Soca"` |
| `NO_CORTE` | Número do corte atual (0 = cana planta) |
| `TCH_PROD` | Produtividade em t/ha |
| `DATA_PLANTIO` | Data de plantio do talhão |
| `ZONA_AGRO_ECOLOGICA` | Código da zona agroecológica |
| `DE_TP_SOLO` | Tipo de solo textual (ex: `"Argiloso"`, `"Médio"`) |
| `Reforma` | Flag de reforma prevista (`"S"` ou `"N"`) |
| `SIT_TALHAO` | Situação do talhão (`"Cana Planta"`, `"Fechado"`, etc.) |
| `cd_upnivel1` | Código da unidade/fazenda (chave de cruzamento com solo) |

**Análise de Solo** (`Dados_analise_solo.csv`)

As colunas com sufixo `1` referem-se à **camada 0–25 cm** e com sufixo `2` à **camada 25–50 cm**.

| Campo | Descrição | Unidade |
|---|---|---|
| `FST` | Identificador do ponto de análise (upnivel1-upnivel2-upnivel3) | — |
| `ph1`, `ph2` | pH em CaCl₂ | — |
| `V1`, `V2` | Saturação por bases | % |
| `CTC1`, `CTC2` | Capacidade de troca catiônica | mmolc/dm³ |
| `ca1`, `ca2` | Cálcio trocável | mmolc/dm³ |
| `mg1`, `mg2` | Magnésio trocável | mmolc/dm³ |
| `al1`, `al2` | Alumínio trocável | mmolc/dm³ |
| `sb1`, `sb2` | Soma de bases | mmolc/dm³ |
| `p1`, `p2` | Fósforo disponível | mg/dm³ |

> **Chave de cruzamento:** O campo `FST` da análise de solo (ex: `"320110-1-11"`) corresponde à combinação `cd_upnivel1-cd_upnivel2-cd_upnivel3` do inventário. A validação do mapeamento exato deve ser confirmada com o time ATVOS antes da implementação.

---

## 3. Pseudocódigos

### PROCESSO A — DIRETRIZES DE CORRETIVOS PARA CANA PLANTA

Os três corretivos abaixo (calagem, gessagem, fosfatagem) formam um único processo agronômico executado em sequência no pré-plantio, com o objetivo de corrigir as propriedades químicas do solo para garantir o bom desenvolvimento da cana planta. Conforme o manual Agroadvance, esse preparo deve começar **60 a 90 dias antes do plantio**.

---

#### REGRA A.1 — CALAGEM

```
DEFINIÇÕES:
  V_ALVO           = 60        # saturação por bases alvo (%)
  PRNT_PADRAO      = 100       # poder relativo de neutralização total do calcário (%)
  DOSE_MAXIMA      = 4.0       # t/ha por aplicação (limite técnico recomendado)
  MG_LIMIAR        = 5.0       # mmolc/dm³ — abaixo disso, obrigatório calcário dolomítico


PARA CADA talhão NO inventário:

  OBTER análise_solo ONDE FST = talhão.cd_upnivel1 + talhão.cd_upnivel2 + talhão.cd_upnivel3

  SE análise_solo NÃO ENCONTRADA:
    resultado.observacao = "sem dados de solo — calagem indeterminada"
    ENCERRAR

  V_atual      = análise_solo.V1       # saturação por bases camada 0–25 cm
  CTC          = análise_solo.CTC1     # CTC camada 0–25 cm (mmolc/dm³)
  mg_trocavel  = análise_solo.mg1      # Mg camada 0–25 cm

  SE V_atual < V_ALVO:

    # Fórmula de necessidade de calcário pela saturação por bases (IAC)
    NC = CTC * (V_ALVO - V_atual) / (PRNT_PADRAO * 10)
    NC = MIN(NC, DOSE_MAXIMA)

    SE mg_trocavel < MG_LIMIAR:
      tipo_calcario  = "dolomítico"
      NC             = MAX(NC, 1.0)    # mínimo 1 t/ha para corrigir deficiência de Mg
    SENÃO:
      tipo_calcario = "calcítico ou dolomítico"

    SE talhão.CATEGORIA == "Formação":
      tipo_aplicacao = "incorporada"
      momento        = "60 a 90 dias antes do plantio — antes da aração"
    SENÃO:
      NC             = NC * 0.5        # aplicação superficial tem menor eficiência em cana soca
      tipo_aplicacao = "superficial"
      momento        = "início do período chuvoso"

  SENÃO:
    NC             = 0
    tipo_calcario  = "nenhum"
    tipo_aplicacao = "nenhuma"
    momento        = "não aplicável — V% já adequado"

  RETORNAR {
    chave           : talhão.CHAVE,
    dose_calcario   : NC,              # t/ha
    tipo_calcario   : tipo_calcario,
    tipo_aplicacao  : tipo_aplicacao,
    momento         : momento,
    V_atual_perc    : V_atual,
    V_alvo_perc     : V_ALVO
  }
```

---

#### REGRA A.2 — GESSAGEM

```
DEFINIÇÕES:
  CA_MINIMO        = 4.0     # mmolc/dm³ — teor mínimo de Ca em subsuperfície
  SAT_AL_MAXIMO    = 40.0    # % — saturação por Al máxima tolerada

  # Estimativa de argila (g/kg) a partir do tipo textual de solo (DE_TP_SOLO)
  TABELA_ARGILA = {
    "Muito Argiloso" : 550,
    "Argiloso"       : 420,
    "Médio"          : 250,
    "Arenoso"        : 150,
    "A Definir"      : 300    # valor conservador — deve ser validado em campo
  }


PARA CADA talhão NO inventário:

  SE talhão.CATEGORIA != "Formação":
    resultado.observacao = "gessagem de incorporação recomendada apenas para cana planta"
    ENCERRAR

  OBTER análise_solo ONDE FST = talhão.cd_upnivel1 + talhão.cd_upnivel2 + talhão.cd_upnivel3

  SE análise_solo NÃO ENCONTRADA:
    resultado.observacao = "sem dados de solo — gessagem indeterminada"
    ENCERRAR

  ca_sub  = análise_solo.ca2     # Ca camada 25–50 cm
  al_sub  = análise_solo.al2     # Al camada 25–50 cm
  sb_sub  = análise_solo.sb2     # Soma de bases camada 25–50 cm

  SE (sb_sub + al_sub) > 0:
    sat_al = al_sub / (sb_sub + al_sub) * 100
  SENÃO:
    sat_al = 0

  SE ca_sub < CA_MINIMO OU sat_al > SAT_AL_MAXIMO:

    tipo_solo = talhão.DE_TP_SOLO
    SE tipo_solo ESTÁ EM TABELA_ARGILA:
      argila_g_kg = TABELA_ARGILA[tipo_solo]
    SENÃO:
      argila_g_kg = TABELA_ARGILA["A Definir"]

    # Fórmula Agroadvance: argila (g/kg) × 5 = dose de gesso em kg/ha
    dose_gesso       = argila_g_kg * 5
    aplicar_gesso    = VERDADEIRO
    momento          = "na etapa da grade niveladora, antes do plantio"

  SENÃO:
    dose_gesso    = 0
    aplicar_gesso = FALSO
    momento       = "não aplicável — Ca e saturação de Al adequados"

  RETORNAR {
    chave          : talhão.CHAVE,
    aplicar_gesso  : aplicar_gesso,
    dose_gesso     : dose_gesso,     # kg/ha
    momento        : momento,
    ca_sub         : ca_sub,
    sat_al_perc    : sat_al
  }
```

---

#### REGRA A.3 — FOSFATAGEM

```
DEFINIÇÕES:
  # Faixas de interpretação do fósforo (Mehlich-1, mg/dm³)
  # Referência: solo de textura média a argilosa (perfil predominante ATVOS)
  P_MUITO_BAIXO     = 6.0     # < 6 mg/dm³
  P_BAIXO           = 12.0    # 6 a 12 mg/dm³
  P_MEDIO           = 25.0    # 12 a 25 mg/dm³
                               # ≥ 25 = suficiente, sem necessidade de aplicação

  DOSE_P_MUITO_BAIXO  = 120   # kg P₂O₅/ha
  DOSE_P_BAIXO        = 80    # kg P₂O₅/ha
  DOSE_P_MEDIO        = 40    # kg P₂O₅/ha
  DOSE_P_SUFICIENTE   = 0


PARA CADA talhão NO inventário:

  SE talhão.CATEGORIA != "Formação":
    resultado.observacao = "fosfatagem de sulco aplicável apenas na implantação (cana planta)"
    ENCERRAR

  OBTER análise_solo ONDE FST = talhão.cd_upnivel1 + talhão.cd_upnivel2 + talhão.cd_upnivel3

  SE análise_solo NÃO ENCONTRADA:
    resultado.observacao = "sem dados de solo — fosfatagem indeterminada"
    ENCERRAR

  p_disponivel = análise_solo.p1    # P camada 0–25 cm

  SE p_disponivel < P_MUITO_BAIXO:
    dose_fosfato = DOSE_P_MUITO_BAIXO
    nivel_p      = "muito baixo"
    prioridade   = "alta"

  SENÃO SE p_disponivel < P_BAIXO:
    dose_fosfato = DOSE_P_BAIXO
    nivel_p      = "baixo"
    prioridade   = "média"

  SENÃO SE p_disponivel < P_MEDIO:
    dose_fosfato = DOSE_P_MEDIO
    nivel_p      = "médio"
    prioridade   = "baixa"

  SENÃO:
    dose_fosfato = DOSE_P_SUFICIENTE
    nivel_p      = "suficiente"
    prioridade   = "nenhuma"

  momento = "no sulco de plantio (100% da dose) ou pré-plantio incorporado"

  RETORNAR {
    chave               : talhão.CHAVE,
    dose_fosfato        : dose_fosfato,   # kg P₂O₅/ha
    nivel_p             : nivel_p,
    prioridade          : prioridade,
    momento             : momento,
    p_disponivel        : p_disponivel
  }
```

---

### PROCESSO B — ERRADICAÇÃO DE SOQUEIRA E DESSECAÇÃO

A erradicação de soqueira é a decisão de encerrar o ciclo de um talhão de cana soca e iniciar o processo de reforma — subsolagem, correção do solo e replantio. A dessecação é a operação de aplicação de herbicidas para matar a soqueira antes da erradicação mecânica.

```
DEFINIÇÕES:
  TCH_MINIMO_ECONOMICO      = 55.0   # t/ha — abaixo disso, reforma recomendada
  CORTE_ALERTA_LONGEVIDADE  = 6      # a partir daqui, monitorar produtividade
  CORTE_REFORMA_OBRIGATORIA = 8      # acima disso, reforma independente da produtividade


PARA CADA talhão NO inventário:

  SE talhão.CATEGORIA == "Formação":
    resultado.observacao = "talhão em formação — erradicação não aplicável"
    ENCERRAR

  TCH      = talhão.TCH_PROD
  n_corte  = talhão.NO_CORTE
  situacao = talhão.SIT_TALHAO

  # --- Bloco de decisão de reforma ---

  SE n_corte >= CORTE_REFORMA_OBRIGATORIA:
    reforma_recomendada = VERDADEIRO
    motivo              = "longevidade máxima atingida — soqueira esgotada"
    prioridade          = "alta"

  SENÃO SE TCH < TCH_MINIMO_ECONOMICO E n_corte >= 3:
    reforma_recomendada = VERDADEIRO
    motivo              = "produtividade abaixo do limiar econômico (TCH < 55 t/ha)"
    prioridade          = "alta"

  SENÃO SE TCH < TCH_MINIMO_ECONOMICO E n_corte < 3:
    reforma_recomendada = VERDADEIRO
    motivo              = "baixa produtividade em corte inicial — investigar estabelecimento"
    prioridade          = "média"
    observacao          = "verificar presença de pragas (broca, cigarrinha-das-raízes) ou falhas de brotação"

  SENÃO SE TCH >= TCH_MINIMO_ECONOMICO E n_corte >= CORTE_ALERTA_LONGEVIDADE:
    reforma_recomendada = VERDADEIRO
    motivo              = "longevidade elevada — programar reforma preventiva"
    prioridade          = "baixa"

  SENÃO:
    reforma_recomendada = FALSO
    motivo              = "talhão dentro dos critérios de produtividade e longevidade"
    prioridade          = "nenhuma"

  # --- Protocolo de dessecação ---

  SE reforma_recomendada == VERDADEIRO:
    SE situacao == "Fechado" OU situacao == "Cana Soca":
      dessecacao_indicada = VERDADEIRO
      protocolo_dessecacao = "aplicar herbicida dessecante pós-colheita, antes da subsolagem"
      janela_dessecacao    = "até 30 dias após a colheita do último corte"
    SENÃO:
      dessecacao_indicada  = FALSO
      protocolo_dessecacao = "verificar situação atual do talhão com equipe de campo"
  SENÃO:
    dessecacao_indicada  = FALSO
    protocolo_dessecacao = "não aplicável"

  RETORNAR {
    chave                : talhão.CHAVE,
    n_corte              : n_corte,
    TCH                  : TCH,
    reforma_recomendada  : reforma_recomendada,
    motivo               : motivo,
    prioridade           : prioridade,
    dessecacao_indicada  : dessecacao_indicada,
    protocolo_dessecacao : protocolo_dessecacao,
    janela_dessecacao    : janela_dessecacao
  }
```

---

## 4. Explicação Detalhada

### 4.1 Regra A.1 — Calagem

**Objetivo agrônomico:** elevar a saturação por bases (V%) do solo a 60%, nível a partir do qual os principais nutrientes da cana ficam disponíveis para absorção radicular. Em solos ácidos (pH < 5,5 ou V% < 50%), o alumínio trocável se torna tóxico para as raízes e o fósforo se precipita, tornando-se indisponível.

**Variáveis envolvidas:**
- `V1` (saturação por bases atual, %) e `CTC1` (capacidade de troca catiônica, mmolc/dm³) vêm do arquivo `Dados_analise_solo.csv`.
- `CATEGORIA` vem do inventário e determina se a aplicação pode ser incorporada (cana planta) ou deve ser superficial (cana soca).
- `mg1` determina o tipo de calcário: se o magnésio trocável estiver abaixo de 5 mmolc/dm³, o calcário **dolomítico** (que contém Ca e Mg) é obrigatório.

**Fórmula utilizada — Necessidade de Calcário (IAC/Embrapa):**

```
NC (t/ha) = CTC × (V_alvo − V_atual) / (PRNT × 10)
```

Onde:
- `CTC` está em mmolc/dm³ (unidade do arquivo de análise de solo)
- `V_alvo = 60%`
- `PRNT = 100` (poder relativo de neutralização total do calcário; ajustável conforme o produto utilizado)
- O denominador `PRNT × 10` converte a unidade de mmolc/dm³ para t/ha

**Exemplo prático:** Talhão com CTC = 90 mmolc/dm³ e V% atual = 42%.
```
NC = 90 × (60 − 42) / (100 × 10) = 90 × 18 / 1000 = 1,62 t/ha
```

**Limitações e pontos para validação com ATVOS:**
- O PRNT do calcário a ser utilizado pode diferir de 100. Se o produto tiver PRNT = 80, a dose calculada deve ser dividida por 0,8 (aumenta).
- A dose máxima de 4 t/ha por aplicação é uma salvaguarda técnica — valores acima são raros e merecem revisão manual.
- O fator 0,5 aplicado em cana soca (aplicação superficial) é uma estimativa conservadora da eficiência reduzida. O valor exato deve ser validado com o PO ATVOS.

---

### 4.2 Regra A.2 — Gessagem

**Objetivo agronômico:** corrigir a subsuperfície do solo (camada 25–50 cm) onde o calcário não chega por incorporação. O gesso agrícola (CaSO₄) é móvel no perfil — desce com a água de chuva — corrigindo a toxidez por alumínio e aumentando o teor de cálcio em profundidade, o que estimula o crescimento radicular em camadas mais fundas e aumenta a resistência da planta ao estresse hídrico.

**Variáveis envolvidas:**
- `ca2` e `al2` são da camada 25–50 cm do arquivo de análise de solo — exatamente a faixa onde o gesso atua.
- `sb2` (soma de bases subsuperfície) é usado para calcular a saturação por alumínio: `sat_Al = al2 / (sb2 + al2) × 100`.
- `DE_TP_SOLO` do inventário é usado para estimar o teor de argila, necessário para calcular a dose de gesso.

**Fórmula utilizada (Agroadvance / Embrapa):**

```
dose_gesso (kg/ha) = argila (g/kg) × 5
```

**Mapeamento DE_TP_SOLO → argila:**

| Classificação textual | Argila estimada (g/kg) | Dose de gesso (kg/ha) |
|---|---|---|
| Muito Argiloso | 550 | 2.750 |
| Argiloso | 420 | 2.100 |
| Médio | 250 | 1.250 |
| Arenoso | 150 | 750 |
| A Definir | 300 (conservador) | 1.500 |

**Gatilhos de aplicação:** a regra aciona a gessagem quando **ao menos uma** das condições for verdadeira:
1. Cálcio subsuperficial < 4 mmolc/dm³ — indica deficiência de Ca no perfil profundo
2. Saturação por alumínio > 40% — indica toxidez radicular

**Limitações e pontos para validação com ATVOS:**
- O campo `DE_TP_SOLO` contém valores textuais não padronizados (ex: "A Definir"). É necessário mapear todos os valores únicos desse campo e associar a uma argila estimada ou, preferencialmente, substituir por dado analítico de textura quando disponível.
- A gessagem é recomendada exclusivamente para cana planta pois a incorporação durante a preparação do solo maximiza a distribuição no perfil. O time ATVOS deve confirmar se há protocolo de gessagem superficial em cana soca na operação.

---

### 4.3 Regra A.3 — Fosfatagem

**Objetivo agronômico:** garantir disponibilidade de fósforo (P) para a cana planta na fase de enraizamento e perfilhamento inicial. O fósforo é imóvel no solo — não se desloca pela solução como o nitrogênio — por isso deve ser aplicado no sulco de plantio ou incorporado antes do plantio, próximo às raízes jovens.

**Variáveis envolvidas:**
- `p1` (fósforo disponível camada 0–25 cm, mg/dm³) do arquivo de análise de solo.
- `CATEGORIA` do inventário — fosfatagem de sulco é exclusiva para cana planta.

**Faixas de interpretação utilizadas:**

| Nível de P | Faixa (mg/dm³) | Dose de P₂O₅ (kg/ha) | Prioridade |
|---|---|---|---|
| Muito baixo | < 6 | 120 | Alta |
| Baixo | 6 a 12 | 80 | Média |
| Médio | 12 a 25 | 40 | Baixa |
| Suficiente | ≥ 25 | 0 | Nenhuma |

**Limitações e pontos para validação com ATVOS:**
- As faixas e doses estão baseadas na literatura para solos de textura média a argilosa, predominante nas unidades ATVOS. Para solos arenosos, os limiares são diferentes (menores). O PO ATVOS deve confirmar se as tabelas do PDA divergem dessas referências.
- A forma do fertilizante fosfatado (superfosfato simples, fosfato reativo, fosfato monoamônico) impacta a eficiência e não está codificada aqui — a regra define apenas a dose de P₂O₅, não o produto.

---

### 4.4 Regra B — Erradicação de Soqueira e Dessecação

**Objetivo agronômico:** decidir quais talhões de cana soca devem ser encerrados (erradicados) e reformados. A cana é uma cultura perene que rebrotará por vários ciclos após cada colheita, mas a produtividade decai ao longo dos cortes. Manter um talhão de baixa produtividade tem custo de oportunidade alto — o talhão ocupa área que poderia produzir mais com cana nova.

**Variáveis envolvidas:**
- `TCH_PROD` (toneladas por hectare de produtividade estimada) e `NO_CORTE` (número do corte atual) vêm do inventário.
- `SIT_TALHAO` determina o estado atual do talhão e guia o protocolo de dessecação.
- `CATEGORIA` é a guarda inicial — erradicação não faz sentido para cana em formação.

**Lógica de decisão em quatro cenários:**

| Cenário | TCH | Nº de corte | Decisão | Prioridade |
|---|---|---|---|---|
| Longevidade máxima | qualquer | ≥ 8 | Reforma obrigatória | Alta |
| Baixa produtividade madura | < 55 | ≥ 3 | Reforma por TCH | Alta |
| Baixa produtividade jovem | < 55 | < 3 | Reforma + investigação | Média |
| Longevidade elevada, TCH ok | ≥ 55 | ≥ 6 | Reforma preventiva | Baixa |
| Talhão produtivo | ≥ 55 | < 6 | Continuar ciclo | Nenhuma |

**Referência:** o manual Agroadvance estabelece que "produtividades inferiores a 55 t/ha no ciclo, a reforma do canavial é uma recomendação importante." O limiar de 8 cortes para reforma obrigatória é uma prática comum na região Centro-Sul, sujeita a confirmação pela ATVOS.

**Protocolo de dessecação:** quando a reforma é decidida, o talhão deve ser dessecado após a última colheita — antes das operações de subsolagem e preparo do solo — para evitar rebrotas da soqueira antiga durante o novo ciclo. A janela recomendada é de até 30 dias após a colheita.

**Limitações e pontos para validação com ATVOS:**
- O campo `TCH_PROD` no inventário pode ser produtividade estimada (pré-colheita) ou realizada (pós-colheita). Confirmar com ATVOS qual valor usar para a decisão de reforma.
- O limiar de 55 t/ha e os números de corte são parâmetros ajustáveis no bloco `DEFINIÇÕES`. O PO ATVOS deve confirmar os valores específicos do PDA antes da implementação.
- Talhões com flag `Reforma = "S"` já no inventário podem ser priorizados diretamente, sem precisar recalcular — isso deve ser tratado como um pré-filtro na implementação.
- O campo `NO_CORTE = 0` no inventário indica cana planta (formação), e o pseudocódigo encerra o processamento para esses casos.

---

## 5. Conclusão

Este documento formaliza quatro regras agronômicas do PDA da ATVOS em pseudocódigo revisável — calagem, gessagem, fosfatagem (Processo A) e erradicação de soqueira com dessecação (Processo B) — utilizando exclusivamente as variáveis disponíveis nos dois conjuntos de dados fornecidos: `Inventario_atvos_21_27_part_4.xlsx` e `Dados_analise_solo.csv`.

A lógica foi construída sobre três princípios:

1. **Fidelidade técnica:** as fórmulas e limiares utilizados têm respaldo no manual Agroadvance e na literatura agronômica brasileira (IAC/Embrapa). As fontes são rastreáveis.
2. **Implementabilidade direta:** todas as variáveis referenciadas no pseudocódigo existem nos dados disponíveis. Não há dependência de fontes externas ou campos inexistentes.
3. **Auditabilidade:** cada regra retorna não apenas o valor calculado, mas também os insumos que geraram aquela recomendação (V% atual, Ca subsuperficial, TCH, etc.), permitindo rastrear e contestar qualquer orientação gerada.

**Próximos passos antes da Task 2.3:**
- [ ] Validação do pseudocódigo com o orientador técnico
- [ ] Validação com o PO ATVOS — confirmar limiares, fórmulas e campos-chave do PDA
- [ ] Mapear todos os valores únicos de `DE_TP_SOLO` para refinar a tabela de argila
- [ ] Confirmar a chave de cruzamento entre `FST` e os campos do inventário
- [ ] Confirmar se `TCH_PROD` representa produtividade estimada ou realizada
- [ ] Alinhar o valor de PRNT do calcário padrão utilizado pela ATVOS

Após a validação dessas regras, o pseudocódigo estará pronto para ser traduzido para Python na Task 2.3, seguindo a arquitetura de pipeline definida pelo time ATVOS (GCP/BigQuery).
