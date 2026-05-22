from .utils import campo_invalido


def calcular_erradicacao(talhao: dict) -> dict:
    """
    Avalia a necessidade de erradicação de soqueira e reforma do talhão
    com base na produtividade (TCH) e no número de cortes (longevidade).

    Aplicável somente a talhões em produção (Cana Soca). Para talhões em
    formação, retorna orientação de não-aplicabilidade.

    Parameters
    ----------
    talhao : dict
        Registro de um talhão do inventario_silver.csv. Campos utilizados:

        - ``categoria`` (str): "Formação" retorna não-aplicável; demais aplicam a regra
        - ``tch_prod`` (float): toneladas de cana por hectare estimadas
        - ``no_corte`` (int): número do corte atual
        - ``sit_talhao`` (str): situação atual — "Fechado" ou "Cana Soca"
          habilitam protocolo de dessecação imediata

    Returns
    -------
    dict
        ``orientacao`` (str)
            Status (REFORMA ou CONTINUAR), motivo, prioridade e protocolo
            de dessecação.

        ``valor_calculado`` (float)
            TCH do talhão — valor central da decisão. None quando dado ausente
            ou não aplicável.

        ``regra_acionada`` (str)
            Identificador da condição disparada. Valores possíveis:

            - ``"reforma_longevidade_maxima"`` — no_corte ≥ 8
            - ``"reforma_tch_baixo_maduro"`` — TCH < 55 e no_corte ≥ 3
            - ``"reforma_tch_baixo_jovem"`` — TCH < 55 e no_corte < 3
            - ``"reforma_preventiva"`` — TCH ≥ 55 e no_corte ≥ 6
            - ``"sem_necessidade_reforma"`` — talhão dentro dos critérios
            - ``"nao_aplicavel_formacao"`` — talhão em formação
            - ``"dado_ausente_tch_prod"`` / ``"dado_ausente_no_corte"`` — campo nulo ou NaN

        ``detalhes`` (dict)
            Campos granulares: n_corte, TCH, reforma recomendada, motivo,
            prioridade, dessecação e protocolo.

    Notes
    -----
    Parâmetros ajustáveis conforme PDA ATVOS:

    - TCH_MINIMO_ECONOMICO = 55,0 t/ha
    - CORTE_ALERTA_LONGEVIDADE = 6
    - CORTE_REFORMA_OBRIGATORIA = 8

    Confirmar com ATVOS se ``tch_prod`` representa produtividade estimada ou
    realizada, pois isso impacta diretamente o disparo da regra.

    Examples
    --------
    >>> talhao = {
    ...     "id_talhao": "T001",
    ...     "categoria": "Cana Soca",
    ...     "tch_prod": 48.0,
    ...     "no_corte": 4,
    ...     "sit_talhao": "Fechado",
    ... }
    >>> calcular_erradicacao(talhao)
    {
        "orientacao": "[REFORMA RECOMENDADA] Produtividade abaixo do limiar ...",
        "valor_calculado": 48.0,
        "regra_acionada": "reforma_tch_baixo_maduro",
        "detalhes": {...}
    }
    """

    TCH_MINIMO_ECONOMICO      = 55.0
    CORTE_ALERTA_LONGEVIDADE  = 6
    CORTE_REFORMA_OBRIGATORIA = 8

    SITUACOES_DESSECACAO = {"Fechado", "Cana Soca"}

    # 1. Pré-condição: não se aplica a cana planta
    if talhao.get("categoria") == "Formação":
        return {
            "orientacao":      "Talhão em formação — erradicação de soqueira não aplicável.",
            "valor_calculado": None,
            "regra_acionada":  "nao_aplicavel_formacao",
            "detalhes":        {"id_talhao": talhao.get("id_talhao")},
        }

    # 2. Validar campos obrigatórios (None e NaN)
    for campo in ("tch_prod", "no_corte"):
        if campo_invalido(talhao.get(campo)):
            return {
                "orientacao":      f"Dado ausente ou inválido: {campo}.",
                "valor_calculado": None,
                "regra_acionada":  f"dado_ausente_{campo}",
                "detalhes":        {"id_talhao": talhao.get("id_talhao"), "campo_ausente": campo},
            }

    # 3. Extrair valores
    tch       = float(talhao["tch_prod"])
    n_corte   = int(talhao["no_corte"])
    situacao  = talhao.get("sit_talhao", "") or ""
    id_talhao = talhao.get("id_talhao", "desconhecido")
    observacao_extra = None

    # 4. Bloco de decisão de reforma
    if n_corte >= CORTE_REFORMA_OBRIGATORIA:
        reforma_recomendada = True
        motivo              = "longevidade máxima atingida — soqueira esgotada"
        prioridade          = "alta"
        regra               = "reforma_longevidade_maxima"

    elif tch < TCH_MINIMO_ECONOMICO and n_corte >= 3:
        reforma_recomendada = True
        motivo              = f"produtividade abaixo do limiar econômico (TCH {tch} t/ha < {TCH_MINIMO_ECONOMICO} t/ha)"
        prioridade          = "alta"
        regra               = "reforma_tch_baixo_maduro"

    elif tch < TCH_MINIMO_ECONOMICO and n_corte < 3:
        reforma_recomendada = True
        motivo              = "baixa produtividade em corte inicial — investigar estabelecimento"
        prioridade          = "média"
        regra               = "reforma_tch_baixo_jovem"
        observacao_extra    = (
            "Verificar presença de pragas (broca, cigarrinha-das-raízes) "
            "ou falhas de brotação antes de confirmar a reforma."
        )

    elif tch >= TCH_MINIMO_ECONOMICO and n_corte >= CORTE_ALERTA_LONGEVIDADE:
        reforma_recomendada = True
        motivo              = "longevidade elevada — programar reforma preventiva"
        prioridade          = "baixa"
        regra               = "reforma_preventiva"

    else:
        reforma_recomendada = False
        motivo              = "talhão dentro dos critérios de produtividade e longevidade"
        prioridade          = "nenhuma"
        regra               = "sem_necessidade_reforma"

    # 5. Protocolo de dessecação
    if reforma_recomendada:
        if situacao in SITUACOES_DESSECACAO:
            dessecacao_indicada  = True
            protocolo_dessecacao = "Aplicar herbicida dessecante pós-colheita, antes da subsolagem."
            janela_dessecacao    = "Até 30 dias após a colheita do último corte."
        else:
            dessecacao_indicada  = False
            protocolo_dessecacao = (
                f"Verificar situação atual do talhão com equipe de campo "
                f"(sit_talhao registrado: '{situacao}')."
            )
            janela_dessecacao = None
    else:
        dessecacao_indicada  = False
        protocolo_dessecacao = "Não aplicável — reforma não recomendada."
        janela_dessecacao    = None

    # 6. Montar orientação descritiva
    status = "REFORMA RECOMENDADA" if reforma_recomendada else "CONTINUAR CICLO"
    partes = [
        f"[{status}] {motivo.capitalize()}.",
        f"Prioridade: {prioridade}.",
        f"Dessecação: {'indicada' if dessecacao_indicada else 'não indicada'}.",
        f"Protocolo: {protocolo_dessecacao}",
    ]
    if observacao_extra:
        partes.append(f"Atenção: {observacao_extra}")
    orientacao = " ".join(partes)

    # 7. Retorno padronizado
    return {
        "orientacao":      orientacao,
        "valor_calculado": tch,
        "regra_acionada":  regra,
        "detalhes": {
            "id_talhao":           id_talhao,
            "n_corte":             n_corte,
            "tch_prod":            tch,
            "reforma_recomendada": reforma_recomendada,
            "motivo":              motivo,
            "prioridade":          prioridade,
            "dessecacao_indicada": dessecacao_indicada,
            "protocolo_dessecacao": protocolo_dessecacao,
            "janela_dessecacao":   janela_dessecacao,
            "observacao":          observacao_extra,
        },
    }
