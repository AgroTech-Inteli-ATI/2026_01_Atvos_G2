def calcular_necessidade_gessagem(talhao: dict) -> dict:
    """
    Calcula a necessidade e a dose de gessagem para talhões em implantação
    (cana planta — categoria "Formação").

    O gesso agrícola (CaSO₄) corrige a subsuperfície do solo (camada 25–50 cm),
    reduzindo a toxidez por alumínio e aumentando o teor de cálcio em profundidade.

    Fórmula utilizada (Agroadvance / Embrapa):
        dose_gesso (kg/ha) = argila (g/kg) × 5

    Parameters
    ----------
    talhao : dict
        Registro de um talhão do inventario_silver.csv. Campos utilizados:

        - ``categoria`` (str): regra aplicável somente a "Formação"
        - ``ca2`` (float): cálcio na camada 25–50 cm (mmolc/dm³)
        - ``al2`` (float): alumínio trocável na camada 25–50 cm (mmolc/dm³)
        - ``sb2`` (float): soma de bases na camada 25–50 cm (mmolc/dm³)
        - ``tipo_solo`` (str): classificação textural — "Muito Argiloso",
          "Argiloso", "Médio", "Arenoso" ou "A Definir"

    Returns
    -------
    dict
        ``orientacao`` (str)
            Momento de aplicação ou motivo da não aplicação.

        ``valor_calculado`` (float)
            Dose de gesso em kg/ha. Zero quando não necessário.

        ``regra_acionada`` (str)
            Identificador da condição disparada. Valores possíveis:

            - ``"gessagem_necessaria"`` — Ca subsuperficial baixo ou saturação Al alta
            - ``"sem_necessidade_gessagem"`` — Ca e Al dentro dos limites
            - ``"nao_aplicavel_categoria"`` — talhão não é cana planta
            - ``"sem_dado_solo"`` — ca2 ausente no registro

    Notes
    -----
    Limiares ajustáveis conforme PDA ATVOS:

    - CA_MINIMO = 4,0 mmolc/dm³
    - SAT_AL_MAXIMO = 40 %

    Mapeamento tipo_solo → argila (g/kg):
        Muito Argiloso → 550  |  Argiloso → 420  |  Médio → 250
        Arenoso → 150  |  A Definir → 300 (conservador)

    Examples
    --------
    >>> talhao = {
    ...     "id_talhao": "T001",
    ...     "categoria": "Formação",
    ...     "ca2": 2.5, "al2": 5.0, "sb2": 15.0,
    ...     "tipo_solo": "Argiloso",
    ... }
    >>> calcular_necessidade_gessagem(talhao)
    {
        "orientacao": "na etapa da grade niveladora, antes do plantio",
        "valor_calculado": 2100,
        "regra_acionada": "gessagem_necessaria"
    }
    """

    CA_MINIMO     = 4.0
    SAT_AL_MAXIMO = 40.0

    TABELA_ARGILA = {
        "Muito Argiloso": 550,
        "Argiloso":       420,
        "Médio":          250,
        "Arenoso":        150,
        "A Definir":      300,
    }

    if talhao.get("categoria") != "Formação":
        return {
            "orientacao":      "gessagem de incorporação recomendada apenas para cana planta",
            "valor_calculado": None,
            "regra_acionada":  "nao_aplicavel_categoria"
        }

    if talhao.get("ca2") is None:
        return {
            "orientacao":      "sem dados de solo — gessagem indeterminada",
            "valor_calculado": None,
            "regra_acionada":  "sem_dado_solo"
        }

    ca_sub = float(talhao["ca2"])
    al_sub = float(talhao["al2"])
    sb_sub = float(talhao["sb2"])

    sat_al = (al_sub / (sb_sub + al_sub) * 100) if (sb_sub + al_sub) > 0 else 0

    if ca_sub < CA_MINIMO or sat_al > SAT_AL_MAXIMO:
        tipo_solo   = talhao.get("tipo_solo", "A Definir")
        argila_g_kg = TABELA_ARGILA.get(tipo_solo, TABELA_ARGILA["A Definir"])
        dose_gesso  = argila_g_kg * 5
        momento     = "na etapa da grade niveladora, antes do plantio"
        regra       = "gessagem_necessaria"
    else:
        dose_gesso = 0
        momento    = "não aplicável — Ca e saturação de Al adequados"
        regra      = "sem_necessidade_gessagem"

    return {
        "orientacao":      momento,
        "valor_calculado": dose_gesso,
        "regra_acionada":  regra
    }