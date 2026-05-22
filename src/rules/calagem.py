from .utils import campo_invalido


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

            - ``"calagem_incorporada_dolomitico"`` — cana planta, V% baixo, Mg deficiente
            - ``"calagem_incorporada_calcitico"`` — cana planta, V% baixo, Mg adequado
            - ``"calagem_superficial_dolomitico"`` — cana soca, V% baixo, Mg deficiente
            - ``"calagem_superficial_calcitico"`` — cana soca, V% baixo, Mg adequado
            - ``"sem_necessidade_calagem"`` — V% já adequado (≥ 60%)
            - ``"dado_ausente_V1"`` / ``"dado_ausente_CTC1"`` / ``"dado_ausente_mg1"`` — campo nulo ou NaN

        ``detalhes`` (dict)
            Campos granulares: dose, tipo de calcário, tipo de aplicação,
            momento, V% atual e alvo.

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
        "orientacao": "Aplicar 1.62 t/ha de calcário dolomítico (incorporada). ...",
        "valor_calculado": 1.62,
        "regra_acionada": "calagem_incorporada_dolomitico",
        "detalhes": {...}
    }
    """

    V_ALVO      = 60.0
    PRNT_PADRAO = 100.0
    DOSE_MAXIMA = 4.0
    MG_LIMIAR   = 5.0

    # 1. Validar campos obrigatórios (None e NaN)
    for campo in ("V1", "CTC1", "mg1"):
        if campo_invalido(talhao.get(campo)):
            return {
                "orientacao":      f"Dado ausente ou inválido: {campo}.",
                "valor_calculado": None,
                "regra_acionada":  f"dado_ausente_{campo}",
                "detalhes":        {"id_talhao": talhao.get("id_talhao"), "campo_ausente": campo},
            }

    # 2. Extrair valores
    v_atual     = float(talhao["V1"])
    ctc         = float(talhao["CTC1"])
    mg_trocavel = float(talhao["mg1"])
    categoria   = talhao.get("categoria", "")
    id_talhao   = talhao.get("id_talhao", "desconhecido")

    # 3. Lógica principal
    if v_atual < V_ALVO:

        nc = ctc * (V_ALVO - v_atual) / (PRNT_PADRAO * 10)
        nc = min(nc, DOSE_MAXIMA)

        if mg_trocavel < MG_LIMIAR:
            tipo_calcario = "dolomítico"
            nc = max(nc, 1.0)
            sufixo_regra = "dolomitico"
        else:
            tipo_calcario = "calcítico ou dolomítico"
            sufixo_regra = "calcitico"

        if categoria == "Formação":
            tipo_aplicacao = "incorporada"
            momento        = "60 a 90 dias antes do plantio — antes da aração"
            regra          = f"calagem_incorporada_{sufixo_regra}"
        else:
            nc             = nc * 0.5
            tipo_aplicacao = "superficial"
            momento        = "início do período chuvoso"
            regra          = f"calagem_superficial_{sufixo_regra}"

        orientacao = (
            f"Aplicar {nc:.2f} t/ha de calcário {tipo_calcario} ({tipo_aplicacao}). "
            f"Momento: {momento}."
        )

    else:
        nc             = 0.0
        tipo_calcario  = "nenhum"
        tipo_aplicacao = "nenhuma"
        momento        = "não aplicável — V% já adequado"
        regra          = "sem_necessidade_calagem"
        orientacao     = (
            f"V% atual ({v_atual}%) já atingiu o alvo ({V_ALVO}%). "
            f"Calagem não necessária."
        )

    # 4. Retorno padronizado
    return {
        "orientacao":      orientacao,
        "valor_calculado": round(nc, 4),
        "regra_acionada":  regra,
        "detalhes": {
            "id_talhao":        id_talhao,
            "dose_calcario_tha": round(nc, 4),
            "tipo_calcario":    tipo_calcario,
            "tipo_aplicacao":   tipo_aplicacao,
            "momento":          momento,
            "V_atual_perc":     v_atual,
            "V_alvo_perc":      V_ALVO,
        },
    }
