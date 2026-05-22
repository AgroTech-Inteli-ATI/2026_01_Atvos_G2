def calcular_necessidade_calagem(talhao: dict) -> dict:
    """
    Calcula a necessidade de calagem para o talhão com base na saturação
    por bases (V%) e na capacidade de troca de cátions (CTC) do solo.

    Utiliza a fórmula IAC/Embrapa:
        NC (t/ha) = CTC × (V_alvo − V_atual) / (PRNT × 10)

    Parameters
    ----------
    talhao : dict
        Registro de um talhão do inventario_silver.csv. Campos utilizados:

        - ``V1`` (float): saturação por bases na camada 0–25 cm (%)
        - ``CTC1`` (float): capacidade de troca de cátions (mmolc/dm³)
        - ``mg1`` (float): magnésio trocável (mmolc/dm³); abaixo de 5
          torna obrigatório o calcário dolomítico
        - ``categoria`` (str): "Formação" = incorporada; demais = superficial

    Returns
    -------
    dict
        ``orientacao`` (str)
            Tipo de aplicação, tipo de calcário e momento recomendado.

        ``valor_calculado`` (float)
            Dose de calcário em t/ha. Zero quando calagem não for necessária.

        ``regra_acionada`` (str)
            Identificador da condição disparada. Valores possíveis:

            - ``"calagem_incorporada"`` — cana planta, V% abaixo do alvo
            - ``"calagem_superficial"`` — cana soca, V% abaixo do alvo
            - ``"sem_necessidade_calagem"`` — V% já adequado (≥ 60%)
            - ``"sem_dado_solo"`` — V1 ausente no registro

    Notes
    -----
    Constantes ajustáveis conforme PDA ATVOS:

    - V_ALVO = 60 %
    - PRNT_PADRAO = 100 %  (confirmar com ATVOS o PRNT real do calcário utilizado)
    - DOSE_MAXIMA = 4,0 t/ha  (limite técnico por aplicação)
    - MG_LIMIAR = 5,0 mmolc/dm³

    Examples
    --------
    >>> talhao = {
    ...     "id_talhao": "T001",
    ...     "categoria": "Formação",
    ...     "V1": 42.0,
    ...     "CTC1": 90.0,
    ...     "mg1": 3.5,
    ... }
    >>> calcular_necessidade_calagem(talhao)
    {
        "orientacao": "incorporada | dolomítico | 60 a 90 dias antes do plantio — antes da aração",
        "valor_calculado": 1.62,
        "regra_acionada": "calagem_incorporada"
    }
    """

    V_ALVO       = 60
    PRNT_PADRAO  = 100
    DOSE_MAXIMA  = 4.0
    MG_LIMIAR    = 5.0

    # Sem dados de solo
    if talhao.get("V1") is None:
        return {
            "orientacao":      "sem dados de solo — calagem indeterminada",
            "valor_calculado": None,
            "regra_acionada":  "sem_dado_solo"
        }

    V_atual     = float(talhao["V1"])
    CTC         = float(talhao["CTC1"])
    mg_trocavel = float(talhao["mg1"])

    if V_atual < V_ALVO:

        NC = CTC * (V_ALVO - V_atual) / (PRNT_PADRAO * 10)
        NC = min(NC, DOSE_MAXIMA)

        if mg_trocavel < MG_LIMIAR:
            tipo_calcario = "dolomítico"
            NC = max(NC, 1.0)
        else:
            tipo_calcario = "calcítico ou dolomítico"

        if talhao.get("categoria") == "Formação":
            tipo_aplicacao = "incorporada"
            momento        = "60 a 90 dias antes do plantio — antes da aração"
            regra          = "calagem_incorporada"
        else:
            NC             = NC * 0.5
            tipo_aplicacao = "superficial"
            momento        = "início do período chuvoso"
            regra          = "calagem_superficial"

    else:
        NC             = 0
        tipo_calcario  = "nenhum"
        tipo_aplicacao = "nenhuma"
        momento        = "não aplicável — V% já adequado"
        regra          = "sem_necessidade_calagem"

    return {
        "orientacao":      f"{tipo_aplicacao} | {tipo_calcario} | {momento}",
        "valor_calculado": round(NC, 2),
        "regra_acionada":  regra
    }