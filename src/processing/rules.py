import math


# ---------------------------------------------------------------------------
# Utilitários compartilhados
# ---------------------------------------------------------------------------

def _campo_invalido(valor):
    if valor is None:
        return True
    if isinstance(valor, float) and math.isnan(valor):
        return True
    if not isinstance(valor, (int, float)):
        return True
    return False


def _sem_dado(regra_acionada):
    return {"orientacao": "SEM_DADO", "valor_calculado": None, "regra_acionada": regra_acionada}


def _nao_aplicavel(motivo, regra_acionada):
    return {"orientacao": motivo, "valor_calculado": None, "regra_acionada": regra_acionada}


# ---------------------------------------------------------------------------
# REGRA A.1 — CALAGEM
# ---------------------------------------------------------------------------

def calcular_necessidade_calagem(talhao: dict) -> dict:
    #  Constantes (ajustáveis conforme PDA ATVOS)
    V_ALVO: float = 60.0        # saturação por bases alvo (%)
    PRNT_PADRAO: float = 100.0  # poder relativo de neutralização total (%)
    DOSE_MAXIMA: float = 4.0    # t/ha — limite técnico por aplicação
    MG_LIMIAR: float = 5.0      # mmolc/dm³ — abaixo disso exige calcário dolomítico

    #  1. Validar campos obrigatórios
    for campo in ("V1", "CTC1", "mg1"):
        if _campo_invalido(talhao.get(campo)):
            return _sem_dado(f"dado_ausente_{campo}")

    #  2. Extrair valores
    v_atual = float(talhao["V1"])
    ctc = float(talhao["CTC1"])
    mg_trocavel = float(talhao["mg1"])
    categoria = talhao.get("categoria", "")
    id_talhao = talhao.get("id_talhao", "desconhecido")

    #  3. Lógica principal
    if v_atual < V_ALVO:

        # Fórmula IAC/Embrapa
        nc = ctc * (V_ALVO - v_atual) / (PRNT_PADRAO * 10)
        nc = min(nc, DOSE_MAXIMA)

        if mg_trocavel < MG_LIMIAR:
            tipo_calcario = "dolomítico"
            nc = max(nc, 1.0)   # mínimo 1 t/ha para corrigir deficiência de Mg
            regra = "calagem_necessaria_dolomítico"
        else:
            tipo_calcario = "calcítico ou dolomítico"
            regra = "calagem_necessaria_calcítico"

        if categoria == "Formação":
            tipo_aplicacao = "incorporada"
            momento = "60 a 90 dias antes do plantio — antes da aração"
        else:
            nc = nc * 0.5   # menor eficiência em aplicação superficial
            tipo_aplicacao = "superficial"
            momento = "início do período chuvoso"
            regra = regra + "_soca_superficial"

        orientacao = (
            f"Aplicar {nc:.2f} t/ha de calcário {tipo_calcario} ({tipo_aplicacao}). "
            f"Momento: {momento}."
        )

    else:
        nc = 0.0
        tipo_calcario = "nenhum"
        tipo_aplicacao = "nenhuma"
        momento = "não aplicável — V% já adequado"
        regra = "calagem_nao_necessaria"
        orientacao = f"V% atual ({v_atual}%) já atingiu o alvo ({V_ALVO}%). Calagem não necessária."

    #  4. Retorno padronizado
    return {
        "orientacao": orientacao,
        "valor_calculado": round(nc, 4),
        "regra_acionada": regra,
        "detalhes": {
            "id_talhao": id_talhao,
            "dose_calcario_tha": round(nc, 4),
            "tipo_calcario": tipo_calcario,
            "tipo_aplicacao": tipo_aplicacao,
            "momento": momento,
            "V_atual_perc": v_atual,
            "V_alvo_perc": V_ALVO,
        },
    }


# ---------------------------------------------------------------------------
# REGRA A.2 — GESSAGEM
# ---------------------------------------------------------------------------

def calcular_necessidade_gessagem(talhao: dict) -> dict:
    #  Constantes (ajustáveis conforme PDA ATVOS)
    CA_MINIMO: float = 4.0
    SAT_AL_MAXIMO: float = 40.0

    # Estimativa de argila por classe textual de solo (g/kg)
    TABELA_ARGILA: dict = {
        "Muito Argiloso": 550,
        "Argiloso":       420,
        "Médio":          250,
        "Arenoso":        150,
        "A Definir":      300,  # valor conservador — confirmar em campo
    }

    #  1. Pré-condição: apenas cana planta
    if talhao.get("categoria") != "Formação":
        return _nao_aplicavel(
            "Gessagem de incorporação recomendada apenas para cana planta (Formação).",
            "categoria_nao_formacao",
        )

    #  2. Validar campos de solo obrigatórios
    for campo in ("ca2", "al2", "sb2"):
        if _campo_invalido(talhao.get(campo)):
            return _sem_dado(f"dado_ausente_{campo}")

    #  3. Extrair valores
    ca_sub = float(talhao["ca2"])
    al_sub = float(talhao["al2"])
    sb_sub = float(talhao["sb2"])
    tipo_solo = talhao.get("tipo_solo", "A Definir") or "A Definir"
    id_talhao = talhao.get("id_talhao", "desconhecido")

    #  4. Saturação por alumínio
    denominador = sb_sub + al_sub
    sat_al = (al_sub / denominador * 100) if denominador > 0 else 0.0

    #  5. Lógica principal
    gatilho_ca = ca_sub < CA_MINIMO
    gatilho_al = sat_al > SAT_AL_MAXIMO

    if gatilho_ca or gatilho_al:
        # Estimar argila pelo tipo textual; fallback para "A Definir"
        argila_g_kg = TABELA_ARGILA.get(tipo_solo, TABELA_ARGILA["A Definir"])
        dose_gesso = float(argila_g_kg * 5)
        momento = "na etapa da grade niveladora, antes do plantio"

        # Nomear a regra de forma auditável
        if gatilho_ca and gatilho_al:
            regra = "gessagem_ca_baixo_e_al_alto"
        elif gatilho_ca:
            regra = "gessagem_ca_subsuperficial_baixo"
        else:
            regra = "gessagem_saturacao_al_alta"

        orientacao = (
            f"Aplicar {dose_gesso:.0f} kg/ha de gesso agrícola. "
            f"Momento: {momento}. "
            f"(Ca subsurf.: {ca_sub} mmolc/dm³ | Sat. Al: {sat_al:.1f}%)"
        )
    else:
        dose_gesso = 0.0
        momento = "não aplicável — Ca e saturação de Al adequados"
        regra = "gessagem_nao_necessaria"
        argila_g_kg = None
        orientacao = (
            f"Gessagem não necessária. "
            f"Ca subsuperficial ({ca_sub} mmolc/dm³) e saturação de Al "
            f"({sat_al:.1f}%) dentro dos limites."
        )

    #  6. Retorno padronizado
    return {
        "orientacao": orientacao,
        "valor_calculado": dose_gesso,
        "regra_acionada": regra,
        "detalhes": {
            "id_talhao": id_talhao,
            "dose_gesso_kgha": dose_gesso,
            "momento": momento,
            "ca_sub_mmolc": ca_sub,
            "sat_al_perc": round(sat_al, 2),
            "tipo_solo": tipo_solo,
            "argila_estimada_gkg": argila_g_kg,
        },
    }


# ---------------------------------------------------------------------------
# REGRA A.3 — FOSFATAGEM
# ---------------------------------------------------------------------------

def calcular_necessidade_fosfatagem(talhao: dict) -> dict:
    #  Constantes (ajustáveis conforme PDA ATVOS)
    P_MUITO_BAIXO: float = 6.0
    P_BAIXO: float = 12.0
    P_MEDIO: float = 25.0

    # Doses correspondentes (kg P₂O₅/ha)
    DOSE_P_MUITO_BAIXO: float = 120.0
    DOSE_P_BAIXO: float = 80.0
    DOSE_P_MEDIO: float = 40.0
    DOSE_P_SUFICIENTE: float = 0.0

    MOMENTO_APLICACAO: str = "no sulco de plantio (100% da dose) ou pré-plantio incorporado"

    #  1. Pré-condição: apenas cana planta
    if talhao.get("categoria") != "Formação":
        return _nao_aplicavel(
            "Fosfatagem de sulco aplicável apenas na implantação (cana planta — Formação).",
            "categoria_nao_formacao",
        )

    #  2. Validar campo de solo obrigatório
    if _campo_invalido(talhao.get("p1")):
        return _sem_dado("dado_ausente_p1")

    #  3. Extrair valores
    p_disponivel = float(talhao["p1"])
    id_talhao = talhao.get("id_talhao", "desconhecido")

    #  4. Lógica de faixas
    if p_disponivel < P_MUITO_BAIXO:
        dose_fosfato = DOSE_P_MUITO_BAIXO
        nivel_p = "muito baixo"
        prioridade = "alta"
        regra = "fosfatagem_p_muito_baixo"

    elif p_disponivel < P_BAIXO:
        dose_fosfato = DOSE_P_BAIXO
        nivel_p = "baixo"
        prioridade = "média"
        regra = "fosfatagem_p_baixo"

    elif p_disponivel < P_MEDIO:
        dose_fosfato = DOSE_P_MEDIO
        nivel_p = "médio"
        prioridade = "baixa"
        regra = "fosfatagem_p_medio"

    else:
        dose_fosfato = DOSE_P_SUFICIENTE
        nivel_p = "suficiente"
        prioridade = "nenhuma"
        regra = "fosfatagem_p_suficiente"

    #  5. Montar orientação descritiva
    if dose_fosfato > 0:
        orientacao = (
            f"Aplicar {dose_fosfato:.0f} kg P₂O₅/ha. "
            f"Nível de P: {nivel_p} ({p_disponivel} mg/dm³). "
            f"Prioridade: {prioridade}. "
            f"Momento: {MOMENTO_APLICACAO}."
        )
    else:
        orientacao = (
            f"Fosfatagem não necessária. "
            f"P disponível ({p_disponivel} mg/dm³) está em nível suficiente (≥ {P_MEDIO} mg/dm³)."
        )

    #  6. Retorno padronizado
    return {
        "orientacao": orientacao,
        "valor_calculado": dose_fosfato,
        "regra_acionada": regra,
        "detalhes": {
            "id_talhao": id_talhao,
            "dose_fosfato_kgha": dose_fosfato,
            "nivel_p": nivel_p,
            "prioridade": prioridade,
            "momento": MOMENTO_APLICACAO,
            "p_disponivel_mgdm3": p_disponivel,
        },
    }


# ---------------------------------------------------------------------------
# REGRA B — ERRADICAÇÃO DE SOQUEIRA
# ---------------------------------------------------------------------------

def calcular_erradicacao_soqueira(talhao: dict) -> dict:
    #  Constantes (ajustáveis conforme PDA ATVOS)
    TCH_MINIMO_ECONOMICO: float = 55.0  # t/ha — abaixo disso, reforma recomendada
    CORTE_ALERTA_LONGEVIDADE: int = 6   # a partir daqui, monitorar produtividade
    CORTE_REFORMA_OBRIGATORIA: int = 8  # acima disso, reforma independente da TCH

    # Situações do talhão que habilitam protocolo de dessecação imediata
    SITUACOES_DESSECACAO: set = {"Fechado", "Cana Soca"}

    #  1. Pré-condição: não se aplica a cana planta
    if talhao.get("categoria") == "Formação":
        return _nao_aplicavel(
            "Talhão em formação — erradicação de soqueira não aplicável.",
            "categoria_formacao",
        )

    #  2. Validar campos obrigatórios
    for campo in ("tch_prod", "no_corte"):
        if _campo_invalido(talhao.get(campo)):
            return _sem_dado(f"dado_ausente_{campo}")

    #  3. Extrair valores
    tch = float(talhao["tch_prod"])
    n_corte = int(talhao["no_corte"])
    situacao = talhao.get("sit_talhao", "") or ""
    id_talhao = talhao.get("id_talhao", "desconhecido")
    observacao_extra = None

    #  4. Bloco de decisão de reforma
    if n_corte >= CORTE_REFORMA_OBRIGATORIA:
        reforma_recomendada = True
        motivo = "longevidade máxima atingida — soqueira esgotada"
        prioridade = "alta"
        regra = "reforma_longevidade_maxima"

    elif tch < TCH_MINIMO_ECONOMICO and n_corte >= 3:
        reforma_recomendada = True
        motivo = f"produtividade abaixo do limiar econômico (TCH {tch} t/ha < {TCH_MINIMO_ECONOMICO} t/ha)"
        prioridade = "alta"
        regra = "reforma_tch_baixo_corte_maduro"

    elif tch < TCH_MINIMO_ECONOMICO and n_corte < 3:
        reforma_recomendada = True
        motivo = "baixa produtividade em corte inicial — investigar estabelecimento"
        prioridade = "média"
        regra = "reforma_tch_baixo_corte_jovem"
        observacao_extra = (
            "Verificar presença de pragas (broca, cigarrinha-das-raízes) "
            "ou falhas de brotação antes de confirmar a reforma."
        )

    elif tch >= TCH_MINIMO_ECONOMICO and n_corte >= CORTE_ALERTA_LONGEVIDADE:
        reforma_recomendada = True
        motivo = "longevidade elevada — programar reforma preventiva"
        prioridade = "baixa"
        regra = "reforma_preventiva_longevidade"

    else:
        reforma_recomendada = False
        motivo = "talhão dentro dos critérios de produtividade e longevidade"
        prioridade = "nenhuma"
        regra = "sem_reforma_talhao_produtivo"

    #  5. Protocolo de dessecação
    if reforma_recomendada:
        if situacao in SITUACOES_DESSECACAO:
            dessecacao_indicada = True
            protocolo_dessecacao = (
                "Aplicar herbicida dessecante pós-colheita, antes da subsolagem."
            )
            janela_dessecacao = "Até 30 dias após a colheita do último corte."
        else:
            dessecacao_indicada = False
            protocolo_dessecacao = (
                "Verificar situação atual do talhão com equipe de campo "
                f"(sit_talhao registrado: '{situacao}')."
            )
            janela_dessecacao = None
    else:
        dessecacao_indicada = False
        protocolo_dessecacao = "Não aplicável — reforma não recomendada."
        janela_dessecacao = None

    #  6. Montar orientação descritiva
    status = "REFORMA RECOMENDADA" if reforma_recomendada else "CONTINUAR CICLO"
    orientacao_partes = [
        f"[{status}] {motivo.capitalize()}.",
        f"Prioridade: {prioridade}.",
        f"Dessecação: {'indicada' if dessecacao_indicada else 'não indicada'}.",
    ]
    if protocolo_dessecacao:
        orientacao_partes.append(f"Protocolo: {protocolo_dessecacao}")
    if observacao_extra:
        orientacao_partes.append(f"Atenção: {observacao_extra}")
    orientacao = " ".join(orientacao_partes)

    #  7. Retorno padronizado
    return {
        "orientacao": orientacao,
        "valor_calculado": tch,   # TCH é o valor central da decisão
        "regra_acionada": regra,
        "detalhes": {
            "id_talhao": id_talhao,
            "n_corte": n_corte,
            "tch_prod": tch,
            "reforma_recomendada": reforma_recomendada,
            "motivo": motivo,
            "prioridade": prioridade,
            "dessecacao_indicada": dessecacao_indicada,
            "protocolo_dessecacao": protocolo_dessecacao,
            "janela_dessecacao": janela_dessecacao,
            "observacao": observacao_extra,
        },
    }


# ---------------------------------------------------------------------------
# Testes isolados — rodar com: python src/processing/rules.py
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import json

    print("\n" + "="*60)
    print("  TESTES — CALAGEM")
    print("="*60)
    casos_calagem = [
        {"id_talhao": "T001", "categoria": "Formação",  "V1": 42.0, "CTC1": 90.0,  "mg1": 3.5},
        {"id_talhao": "T002", "categoria": "Formação",  "V1": 50.0, "CTC1": 80.0,  "mg1": 7.0},
        {"id_talhao": "T003", "categoria": "Formação",  "V1": 65.0, "CTC1": 80.0,  "mg1": 6.0},
        {"id_talhao": "T004", "categoria": "Cana Soca", "V1": 40.0, "CTC1": 100.0, "mg1": 6.0},
        {"id_talhao": "T005", "V1": None,               "CTC1": 80.0, "mg1": 5.0},
        {"id_talhao": "T006", "V1": 40.0,               "CTC1": float("nan"), "mg1": 5.0},
    ]
    for c in casos_calagem:
        r = calcular_necessidade_calagem(c)
        print(f"\n[{c.get('id_talhao')}] regra={r['regra_acionada']} | val={r['valor_calculado']}")
        print(f"  {r['orientacao']}")

    print("\n" + "="*60)
    print("  TESTES — GESSAGEM")
    print("="*60)
    casos_gessagem = [
        {"id_talhao": "T001", "categoria": "Formação",  "ca2": 2.5, "al2": 5.0,  "sb2": 15.0, "tipo_solo": "Argiloso"},
        {"id_talhao": "T002", "categoria": "Formação",  "ca2": 6.0, "al2": 10.0, "sb2": 10.0, "tipo_solo": "Médio"},
        {"id_talhao": "T003", "categoria": "Formação",  "ca2": 5.0, "al2": 3.0,  "sb2": 20.0, "tipo_solo": "Muito Argiloso"},
        {"id_talhao": "T004", "categoria": "Cana Soca", "ca2": 1.0, "al2": 10.0, "sb2": 5.0,  "tipo_solo": "Arenoso"},
        {"id_talhao": "T005", "categoria": "Formação",  "ca2": 2.0, "al2": 8.0,  "sb2": 12.0, "tipo_solo": "Tipo Desconhecido"},
        {"id_talhao": "T006", "categoria": "Formação",  "ca2": None,"al2": 8.0,  "sb2": 12.0, "tipo_solo": "Médio"},
    ]
    for c in casos_gessagem:
        r = calcular_necessidade_gessagem(c)
        print(f"\n[{c.get('id_talhao')}] regra={r['regra_acionada']} | val={r['valor_calculado']}")
        print(f"  {r['orientacao']}")

    print("\n" + "="*60)
    print("  TESTES — FOSFATAGEM")
    print("="*60)
    casos_fosfatagem = [
        {"id_talhao": "T001", "categoria": "Formação",  "p1": 4.5},
        {"id_talhao": "T002", "categoria": "Formação",  "p1": 9.0},
        {"id_talhao": "T003", "categoria": "Formação",  "p1": 18.0},
        {"id_talhao": "T004", "categoria": "Formação",  "p1": 30.0},
        {"id_talhao": "T005", "categoria": "Cana Soca", "p1": 4.0},
        {"id_talhao": "T006", "categoria": "Formação",  "p1": None},
        {"id_talhao": "T007", "categoria": "Formação",  "p1": 6.0},
    ]
    for c in casos_fosfatagem:
        r = calcular_necessidade_fosfatagem(c)
        print(f"\n[{c.get('id_talhao')}] regra={r['regra_acionada']} | val={r['valor_calculado']}")
        print(f"  {r['orientacao']}")

    print("\n" + "="*60)
    print("  TESTES — ERRADICAÇÃO")
    print("="*60)
    casos_erradicacao = [
        {"id_talhao": "T001", "categoria": "Cana Soca", "tch_prod": 60.0, "no_corte": 9, "sit_talhao": "Fechado"},
        {"id_talhao": "T002", "categoria": "Cana Soca", "tch_prod": 48.0, "no_corte": 4, "sit_talhao": "Cana Soca"},
        {"id_talhao": "T003", "categoria": "Cana Soca", "tch_prod": 40.0, "no_corte": 2, "sit_talhao": "Cana Soca"},
        {"id_talhao": "T004", "categoria": "Cana Soca", "tch_prod": 70.0, "no_corte": 7, "sit_talhao": "Fechado"},
        {"id_talhao": "T005", "categoria": "Cana Soca", "tch_prod": 75.0, "no_corte": 3, "sit_talhao": "Cana Soca"},
        {"id_talhao": "T006", "categoria": "Formação",  "tch_prod": 0.0,  "no_corte": 0, "sit_talhao": "Cana Planta"},
        {"id_talhao": "T007", "categoria": "Cana Soca", "tch_prod": None, "no_corte": 5, "sit_talhao": "Fechado"},
        {"id_talhao": "T008", "categoria": "Cana Soca", "tch_prod": 30.0, "no_corte": 5, "sit_talhao": "Em Colheita"},
    ]
    for c in casos_erradicacao:
        r = calcular_erradicacao_soqueira(c)
        print(f"\n[{c.get('id_talhao')}] regra={r['regra_acionada']} | val={r['valor_calculado']}")
        print(f"  {r['orientacao']}")
