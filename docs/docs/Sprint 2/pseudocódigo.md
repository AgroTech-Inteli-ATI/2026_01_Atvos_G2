# Pseudocódigo — Motor de Regras Agronômicas ATVOS
**Projeto:** Módulo de Orientações Agrícolas Data-Driven  
**Equipe:** AgroTech Inteli  
**Parceiro:** ATVOS Agroindustrial  
**Versão:** 2.0 — refatorado para alinhamento com `inventario_silver.csv`

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

Este documento formaliza os **processos 3 e 4** em pseudocódigo alinhado ao script de limpeza (`limpeza.py` v2.0), cujo output é o arquivo `inventario_silver.csv`.

---

## 3. Sumário das Alterações (v1.0 → v2.0)

> Todas as mudanças foram motivadas pelo feedback do PO: **as colunas referenciadas na v1.0 não existem no silver** — os nomes foram padronizados pelo script de limpeza via `COLUNAS_RENAME`, e o join com solo passou a ser feito no pipeline, não no motor.

| Campo na v1.0 | Campo no silver (v2.0) | Motivo |
|---|---|---|
| `talhão.CHAVE` | `talhão.id_talhao` | `CHAVE` não existe; chave primária é `id_talhao` (vem de `TALHAO`) |
| `talhão.CATEGORIA` | `talhão.categoria` | Padronização para caixa baixa pelo `COLUNAS_RENAME` |
| `talhão.NO_CORTE` | `talhão.no_corte` | Padronização para caixa baixa pelo `COLUNAS_RENAME` |
| `talhão.TCH_PROD` | `talhão.tch_prod` | Padronização para caixa baixa pelo `COLUNAS_RENAME` |
| `talhão.SIT_TALHAO` | `talhão.sit_talhao` | Padronização para caixa baixa pelo `COLUNAS_RENAME` |
| `talhão.DE_TP_SOLO` | `talhão.tipo_solo` | `DE_TP_SOLO` renomeado para `tipo_solo` pelo `COLUNAS_RENAME` |
| `talhão.cd_upnivel1/2/3` | `talhão.numero_fazenda` | Chave de join simplificada — join feito no pipeline por `numero_fazenda` ↔ `cd_upnivel1` |
| `OBTER análise_solo ONDE FST = ...` | *(removido)* | Join já resolvido no pipeline; colunas de solo estão diretamente no registro silver |
| `análise_solo NÃO ENCONTRADA` | `SE talhão.V1 É NULO` (ou campo equivalente) | Verificação de nulo no campo após left join, não busca externa |

---

## 4. Nota sobre a Chave de Join com Solo

Na v1.0, o motor buscava a análise de solo em tempo de execução usando a combinação `cd_upnivel1 + cd_upnivel2 + cd_upnivel3`. No script atual (`limpeza.py`), **esse join já acontece no pipeline de limpeza** via `carregar_solo()` + `merge()` por `numero_fazenda` ↔ `cd_upnivel1`, e o `inventario_silver.csv` já sai com as colunas de solo embutidas em cada registro.

Por isso, em toda regra abaixo:
- O bloco `OBTER análise_solo ONDE FST = ...` foi **removido**
- O bloco `SE análise_solo NÃO ENCONTRADA` foi substituído por `SE talhão.<campo_solo> É NULO`, que é o comportamento correto para um **left join**

---

## 5. Pseudocódigos

### PROCESSO A — DIRETRIZES DE CORRETIVOS PARA CANA PLANTA

#### REGRA A.1 — CALAGEM

```
DEFINIÇÕES:
  V_ALVO           = 60        # saturação por bases alvo (%)
  PRNT_PADRAO      = 100       # poder relativo de neutralização total do calcário (%)
  DOSE_MAXIMA      = 4.0       # t/ha por aplicação (limite técnico recomendado)
  MG_LIMIAR        = 5.0       # mmolc/dm³ — abaixo disso, obrigatório calcário dolomítico


PARA CADA talhão NO inventario_silver:

  # O join com solo já foi realizado no pipeline de limpeza.
  # As colunas de solo estão diretamente no registro do talhão.

  SE talhão.V1 É NULO:                          # [v1.0: "análise_solo NÃO ENCONTRADA"]
    resultado.observacao = "sem dados de solo — calagem indeterminada"
    ENCERRAR

  V_atual      = talhão.V1
  CTC          = talhão.CTC1
  mg_trocavel  = talhão.mg1

  SE V_atual < V_ALVO:

    NC = CTC * (V_ALVO - V_atual) / (PRNT_PADRAO * 10)
    NC = MIN(NC, DOSE_MAXIMA)

    SE mg_trocavel < MG_LIMIAR:
      tipo_calcario = "dolomítico"
      NC            = MAX(NC, 1.0)
    SENÃO:
      tipo_calcario = "calcítico ou dolomítico"

    SE talhão.categoria == "Formação":           # [v1.0: talhão.CATEGORIA]
      tipo_aplicacao = "incorporada"
      momento        = "60 a 90 dias antes do plantio — antes da aração"
    SENÃO:
      NC             = NC * 0.5
      tipo_aplicacao = "superficial"
      momento        = "início do período chuvoso"

  SENÃO:
    NC             = 0
    tipo_calcario  = "nenhum"
    tipo_aplicacao = "nenhuma"
    momento        = "não aplicável — V% já adequado"

  RETORNAR {
    id_talhao       : talhão.id_talhao,          # [v1.0: talhão.CHAVE]
    dose_calcario   : NC,
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

  TABELA_ARGILA = {
    "Muito Argiloso" : 550,
    "Argiloso"       : 420,
    "Médio"          : 250,
    "Arenoso"        : 150,
    "A Definir"      : 300    # valor conservador — deve ser validado em campo
  }


PARA CADA talhão NO inventario_silver:

  SE talhão.categoria != "Formação":             # [v1.0: talhão.CATEGORIA]
    resultado.observacao = "gessagem de incorporação recomendada apenas para cana planta"
    ENCERRAR

  SE talhão.ca2 É NULO:                          # [v1.0: "análise_solo NÃO ENCONTRADA"]
    resultado.observacao = "sem dados de solo — gessagem indeterminada"
    ENCERRAR

  ca_sub  = talhão.ca2
  al_sub  = talhão.al2
  sb_sub  = talhão.sb2

  SE (sb_sub + al_sub) > 0:
    sat_al = al_sub / (sb_sub + al_sub) * 100
  SENÃO:
    sat_al = 0

  SE ca_sub < CA_MINIMO OU sat_al > SAT_AL_MAXIMO:

    tipo_solo = talhão.tipo_solo                 # [v1.0: talhão.DE_TP_SOLO]

    SE tipo_solo ESTÁ EM TABELA_ARGILA:
      argila_g_kg = TABELA_ARGILA[tipo_solo]
    SENÃO:
      argila_g_kg = TABELA_ARGILA["A Definir"]

    dose_gesso    = argila_g_kg * 5
    aplicar_gesso = VERDADEIRO
    momento       = "na etapa da grade niveladora, antes do plantio"

  SENÃO:
    dose_gesso    = 0
    aplicar_gesso = FALSO
    momento       = "não aplicável — Ca e saturação de Al adequados"

  RETORNAR {
    id_talhao      : talhão.id_talhao,           # [v1.0: talhão.CHAVE]
    aplicar_gesso  : aplicar_gesso,
    dose_gesso     : dose_gesso,                 # kg/ha
    momento        : momento,
    ca_sub         : ca_sub,
    sat_al_perc    : sat_al
  }
```

---

#### REGRA A.3 — FOSFATAGEM

```
DEFINIÇÕES:
  P_MUITO_BAIXO       = 6.0     # < 6 mg/dm³
  P_BAIXO             = 12.0    # 6 a 12 mg/dm³
  P_MEDIO             = 25.0    # 12 a 25 mg/dm³
                                 # ≥ 25 = suficiente, sem necessidade de aplicação

  DOSE_P_MUITO_BAIXO  = 120     # kg P₂O₅/ha
  DOSE_P_BAIXO        = 80      # kg P₂O₅/ha
  DOSE_P_MEDIO        = 40      # kg P₂O₅/ha
  DOSE_P_SUFICIENTE   = 0


PARA CADA talhão NO inventario_silver:

  SE talhão.categoria != "Formação":             # [v1.0: talhão.CATEGORIA]
    resultado.observacao = "fosfatagem de sulco aplicável apenas na implantação (cana planta)"
    ENCERRAR

  SE talhão.p1 É NULO:                           # [v1.0: "análise_solo NÃO ENCONTRADA"]
    resultado.observacao = "sem dados de solo — fosfatagem indeterminada"
    ENCERRAR

  p_disponivel = talhão.p1

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
    id_talhao           : talhão.id_talhao,      # [v1.0: talhão.CHAVE]
    dose_fosfato        : dose_fosfato,           # kg P₂O₅/ha
    nivel_p             : nivel_p,
    prioridade          : prioridade,
    momento             : momento,
    p_disponivel        : p_disponivel
  }
```

---

### PROCESSO B — ERRADICAÇÃO DE SOQUEIRA E DESSECAÇÃO

```
DEFINIÇÕES:
  TCH_MINIMO_ECONOMICO      = 55.0   # t/ha — abaixo disso, reforma recomendada
  CORTE_ALERTA_LONGEVIDADE  = 6      # a partir daqui, monitorar produtividade
  CORTE_REFORMA_OBRIGATORIA = 8      # acima disso, reforma independente da produtividade


PARA CADA talhão NO inventario_silver:

  SE talhão.categoria == "Formação":             # [v1.0: talhão.CATEGORIA]
    resultado.observacao = "talhão em formação — erradicação não aplicável"
    ENCERRAR

  TCH      = talhão.tch_prod                     # [v1.0: talhão.TCH_PROD]
  n_corte  = talhão.no_corte                     # [v1.0: talhão.NO_CORTE]
  situacao = talhão.sit_talhao                   # [v1.0: talhão.SIT_TALHAO]

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
      dessecacao_indicada  = VERDADEIRO
      protocolo_dessecacao = "aplicar herbicida dessecante pós-colheita, antes da subsolagem"
      janela_dessecacao    = "até 30 dias após a colheita do último corte"
    SENÃO:
      dessecacao_indicada  = FALSO
      protocolo_dessecacao = "verificar situação atual do talhão com equipe de campo"
  SENÃO:
    dessecacao_indicada  = FALSO
    protocolo_dessecacao = "não aplicável"

  RETORNAR {
    id_talhao            : talhão.id_talhao,     # [v1.0: talhão.CHAVE]
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

## 6. Explicação Detalhada

### 6.1 Regra A.1 — Calagem

**Objetivo agronômico:** elevar a saturação por bases (V%) do solo a 60%, nível a partir do qual os principais nutrientes da cana ficam disponíveis para absorção radicular. Em solos ácidos (pH < 5,5 ou V% < 50%), o alumínio trocável se torna tóxico para as raízes e o fósforo se precipita, tornando-se indisponível.

**Variáveis envolvidas:**
- `V1` e `CTC1` (camada 0–25 cm) e `mg1` vêm do solo, disponíveis diretamente no silver após o join por `numero_fazenda`.
- `categoria` determina se a aplicação pode ser incorporada (cana planta) ou superficial (cana soca).
- `mg1` abaixo de 5 mmolc/dm³ torna o calcário **dolomítico** obrigatório.

**Fórmula utilizada — Necessidade de Calcário (IAC/Embrapa):**

```
NC (t/ha) = CTC × (V_alvo − V_atual) / (PRNT × 10)
```

**Exemplo prático:** Talhão com CTC = 90 mmolc/dm³ e V% atual = 42%.
```
NC = 90 × (60 − 42) / (100 × 10) = 90 × 18 / 1000 = 1,62 t/ha
```

**Limitações e pontos para validação com ATVOS:**
- O PRNT do calcário a ser utilizado pode diferir de 100.
- A dose máxima de 4 t/ha por aplicação é uma salvaguarda técnica.
- O fator 0,5 para cana soca deve ser validado com o PO ATVOS.

---

### 6.2 Regra A.2 — Gessagem

**Objetivo agronômico:** corrigir a subsuperfície do solo (camada 25–50 cm) onde o calcário não chega por incorporação. O gesso agrícola (CaSO₄) é móvel no perfil — desce com a água de chuva — corrigindo a toxidez por alumínio e aumentando o teor de cálcio em profundidade.

**Fórmula utilizada (Agroadvance / Embrapa):**

```
dose_gesso (kg/ha) = argila (g/kg) × 5
```

**Mapeamento `tipo_solo` → argila:**

| Classificação textual | Argila estimada (g/kg) | Dose de gesso (kg/ha) |
|---|---|---|
| Muito Argiloso | 550 | 2.750 |
| Argiloso | 420 | 2.100 |
| Médio | 250 | 1.250 |
| Arenoso | 150 | 750 |
| A Definir | 300 (conservador) | 1.500 |

**Limitações e pontos para validação com ATVOS:**
- O campo `tipo_solo` pode conter valores textuais não padronizados. É necessário mapear todos os valores únicos e associar a uma argila estimada.
- Confirmar com ATVOS se há protocolo de gessagem superficial em cana soca.

---

### 6.3 Regra A.3 — Fosfatagem

**Objetivo agronômico:** garantir disponibilidade de fósforo (P) para a cana planta na fase de enraizamento e perfilhamento inicial. O fósforo é imóvel no solo — deve ser aplicado no sulco de plantio ou incorporado antes do plantio.

**Faixas de interpretação utilizadas:**

| Nível de P | Faixa (mg/dm³) | Dose de P₂O₅ (kg/ha) | Prioridade |
|---|---|---|---|
| Muito baixo | < 6 | 120 | Alta |
| Baixo | 6 a 12 | 80 | Média |
| Médio | 12 a 25 | 40 | Baixa |
| Suficiente | ≥ 25 | 0 | Nenhuma |

**Limitações e pontos para validação com ATVOS:**
- Para solos arenosos, os limiares de P são diferentes. O PO ATVOS deve confirmar se as tabelas do PDA divergem dessas referências.

---

### 6.4 Regra B — Erradicação de Soqueira e Dessecação

**Objetivo agronômico:** decidir quais talhões de cana soca devem ser encerrados e reformados. A produtividade da cana decai ao longo dos cortes — manter um talhão de baixa produtividade tem custo de oportunidade elevado.

**Lógica de decisão em cinco cenários:**

| Cenário | TCH | Nº de corte | Decisão | Prioridade |
|---|---|---|---|---|
| Longevidade máxima | qualquer | ≥ 8 | Reforma obrigatória | Alta |
| Baixa produtividade madura | < 55 | ≥ 3 | Reforma por TCH | Alta |
| Baixa produtividade jovem | < 55 | < 3 | Reforma + investigação | Média |
| Longevidade elevada, TCH ok | ≥ 55 | ≥ 6 | Reforma preventiva | Baixa |
| Talhão produtivo | ≥ 55 | < 6 | Continuar ciclo | Nenhuma |

**Limitações e pontos para validação com ATVOS:**
- Confirmar se `tch_prod` representa produtividade estimada ou realizada.
- O limiar de 55 t/ha e os números de corte são parâmetros ajustáveis no bloco `DEFINIÇÕES`.
- Talhões com flag `Reforma = "S"` já no inventário podem ser pré-filtrados antes de entrar no motor.

---

## 7. Conclusão

Esta versão 2.0 do pseudocódigo está alinhada ao output do script de limpeza (`inventario_silver.csv`), eliminando todas as referências a colunas inexistentes no silver e adaptando a lógica de acesso ao solo para o modelo de join centralizado no pipeline.

**Próximos passos antes da Task 2.3:**
- [ ] Validação do pseudocódigo com o orientador técnico
- [ ] Validação com o PO ATVOS — confirmar limiares, fórmulas e campos-chave do PDA
- [ ] Mapear todos os valores únicos de `tipo_solo` para refinar a tabela de argila
- [ ] Confirmar se `tch_prod` representa produtividade estimada ou realizada
- [ ] Alinhar o valor de PRNT do calcário padrão utilizado pela ATVOS
- [ ] Preencher `UNIDADES_OFICIAIS` no script de limpeza para habilitar validação de UIs