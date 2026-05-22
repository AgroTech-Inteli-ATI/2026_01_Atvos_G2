def calcular_necessidade_fosfatagem(talhao: dict) -> dict:
    """
    Calcula a necessidade de fosfatagem de sulco para talhões em implantação
    (cana planta — categoria "Formação").

    O fósforo é imóvel no solo e deve ser aplicado no sulco de plantio ou
    incorporado antes do plantio. A dose é determinada pelo nível de P
    disponível na análise de solo (camada 0–25 cm).

    Parameters
    ----------
    talhao : dict
        Registro de um talhão do inventario_silver.csv. Campos utilizados:

        - ``categoria`` (str): regra aplicável somente a "Formação"
        - ``p1`` (float): fósforo disponível na camada 0–25 cm (mg/dm³)

    Returns
    -------
    dict
        ``orientacao`` (str)
            Nível de P, prioridade e momento de aplicação.

        ``valor_calculado`` (float)
            Dose de P₂O₅ em kg/ha. Zero quando P for suficiente.

        ``regra_acionada`` (str)
            Identificador da condição disparada. Valores possíveis:

            - ``"fosfatagem_muito_baixo"`` — P < 6 mg/dm³ → 120 kg P₂O₅/ha
            - ``"fosfatagem_baixo"`` — P entre 6 e 12 mg/dm³ → 80 kg P₂O₅/ha
            - ``"fosfatagem_medio"`` — P entre 12 e 25 mg/dm³ → 40 kg P₂O₅/ha
            - ``"sem_necessidade_fosfatagem"`` — P ≥ 25 mg/dm³
            - ``"nao_aplicavel_categoria"`` — talhão não é cana planta
            - ``"sem_dado_solo"`` — p1 ausente no registro

    Notes
    -----
    Faixas de P e doses ajustáveis conforme PDA ATVOS:

    | Nível   | Faixa (mg/dm³) | Dose (kg P₂O₅/ha) | Prioridade |
    |---------|----------------|-------------------|------------|
    | Muito baixo | < 6       | 120               | Alta       |
    | Baixo   | 6 a 12         | 80                | Média      |
    | Médio   | 12 a 25        | 40                | Baixa      |
    | Suficiente | ≥ 25        | 0                 | Nenhuma    |

    Para solos muito arenosos, os limiares podem diferir. Validar com ATVOS.

    Examples
    --------
    >>> talhao = {
    ...     "id_talhao": "T001",
    ...     "categoria": "Formação",
    ...     "p1": 4.5,
    ... }
    >>> calcular_necessidade_fosfatagem(talhao)
    {
        "orientacao": "nível muito baixo | prioridade alta | no sulco de plantio ...",
        "valor_calculado": 120,
        "regra_acionada": "fosfatagem_muito_baixo"
    }
    """

    P_MUITO_BAIXO      = 6.0
    P_BAIXO            = 12.0
    P_MEDIO            = 25.0

    DOSE_P_MUITO_BAIXO = 120
    DOSE_P_BAIXO       = 80
    DOSE_P_MEDIO       = 40
    DOSE_P_SUFICIENTE  = 0

    if talhao.get("categoria") != "Formação":
        return {
            "orientacao":      "fosfatagem de sulco aplicável apenas na implantação (cana planta)",
            "valor_calculado": None,
            "regra_acionada":  "nao_aplicavel_categoria"
        }

    if talhao.get("p1") is None:
        return {
            "orientacao":      "sem dados de solo — fosfatagem indeterminada",
            "valor_calculado": None,
            "regra_acionada":  "sem_dado_solo"
        }

    p_disponivel = float(talhao["p1"])
    momento      = "no sulco de plantio (100% da dose) ou pré-plantio incorporado"

    if p_disponivel < P_MUITO_BAIXO:
        dose_fosfato = DOSE_P_MUITO_BAIXO
        nivel_p      = "muito baixo"
        prioridade   = "alta"
        regra        = "fosfatagem_muito_baixo"

    elif p_disponivel < P_BAIXO:
        dose_fosfato = DOSE_P_BAIXO
        nivel_p      = "baixo"
        prioridade   = "média"
        regra        = "fosfatagem_baixo"

    elif p_disponivel < P_MEDIO:
        dose_fosfato = DOSE_P_MEDIO
        nivel_p      = "médio"
        prioridade   = "baixa"
        regra        = "fosfatagem_medio"

    else:
        dose_fosfato = DOSE_P_SUFICIENTE
        nivel_p      = "suficiente"
        prioridade   = "nenhuma"
        regra        = "sem_necessidade_fosfatagem"

    return {
        "orientacao":      f"nível {nivel_p} | prioridade {prioridade} | {momento}",
        "valor_calculado": dose_fosfato,
        "regra_acionada":  regra
    }