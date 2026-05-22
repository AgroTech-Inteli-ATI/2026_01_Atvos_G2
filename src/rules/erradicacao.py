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

        - ``categoria`` (str): "Cana Soca" para aplicar a regra; "Formação"
          retorna não-aplicável
        - ``tch_prod`` (float): toneladas de cana por hectare estimadas
        - ``no_corte`` (int): número do corte atual
        - ``sit_talhao`` (str): situação atual — "Fechado" ou "Cana Soca"
          habilitam protocolo de dessecação imediata

    Returns
    -------
    dict
        ``orientacao`` (str)
            Motivo da decisão, prioridade e protocolo de dessecação.

        ``valor_calculado`` (None)
            Não há valor numérico associado a esta regra.

        ``regra_acionada`` (str)
            Identificador da condição disparada. Valores possíveis:

            - ``"reforma_longevidade_maxima"`` — no_corte ≥ 8
            - ``"reforma_tch_baixo_maduro"`` — TCH < 55 e no_corte ≥ 3
            - ``"reforma_tch_baixo_jovem"`` — TCH < 55 e no_corte < 3
            - ``"reforma_preventiva"`` — TCH ≥ 55 e no_corte ≥ 6
            - ``"sem_necessidade_reforma"`` — talhão dentro dos critérios
            - ``"nao_aplicavel_formacao"`` — talhão em formação
            - ``"sem_dado"`` — tch_prod ou no_corte ausentes

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
        "orientacao": "produtividade abaixo do limiar econômico ... | prioridade alta | ...",
        "valor_calculado": None,
        "regra_acionada": "reforma_tch_baixo_maduro"
    }
    """

    TCH_MINIMO_ECONOMICO      = 55.0
    CORTE_ALERTA_LONGEVIDADE  = 6
    CORTE_REFORMA_OBRIGATORIA = 8

    if talhao.get("categoria") == "Formação":
        return {
            "orientacao":      "talhão em formação — erradicação não aplicável",
            "valor_calculado": None,
            "regra_acionada":  "nao_aplicavel_formacao"
        }

    if talhao.get("tch_prod") is None or talhao.get("no_corte") is None:
        return {
            "orientacao":      "sem dados suficientes — erradicação indeterminada",
            "valor_calculado": None,
            "regra_acionada":  "sem_dado"
        }

    TCH      = float(talhao["tch_prod"])
    n_corte  = int(talhao["no_corte"])
    situacao = talhao.get("sit_talhao", "")

    if n_corte >= CORTE_REFORMA_OBRIGATORIA:
        reforma_recomendada = True
        motivo              = "longevidade máxima atingida — soqueira esgotada"
        prioridade          = "alta"
        regra               = "reforma_longevidade_maxima"

    elif TCH < TCH_MINIMO_ECONOMICO and n_corte >= 3:
        reforma_recomendada = True
        motivo              = "produtividade abaixo do limiar econômico (TCH < 55 t/ha)"
        prioridade          = "alta"
        regra               = "reforma_tch_baixo_maduro"

    elif TCH < TCH_MINIMO_ECONOMICO and n_corte < 3:
        reforma_recomendada = True
        motivo              = "baixa produtividade em corte inicial — investigar estabelecimento"
        prioridade          = "média"
        regra               = "reforma_tch_baixo_jovem"

    elif TCH >= TCH_MINIMO_ECONOMICO and n_corte >= CORTE_ALERTA_LONGEVIDADE:
        reforma_recomendada = True
        motivo              = "longevidade elevada — programar reforma preventiva"
        prioridade          = "baixa"
        regra               = "reforma_preventiva"

    else:
        reforma_recomendada = False
        motivo              = "talhão dentro dos critérios de produtividade e longevidade"
        prioridade          = "nenhuma"
        regra               = "sem_necessidade_reforma"

    if reforma_recomendada:
        if situacao in ["Fechado", "Cana Soca"]:
            dessecacao       = "aplicar herbicida dessecante pós-colheita, antes da subsolagem"
            janela_dessecacao = "até 30 dias após a colheita do último corte"
        else:
            dessecacao        = "verificar situação atual do talhão com equipe de campo"
            janela_dessecacao = "a definir"
    else:
        dessecacao        = "não aplicável"
        janela_dessecacao = "não aplicável"

    return {
        "orientacao":      f"{motivo} | prioridade {prioridade} | {dessecacao}",
        "valor_calculado": None,
        "regra_acionada":  regra
    }