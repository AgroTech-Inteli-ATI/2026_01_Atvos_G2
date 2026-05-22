from .utils import campo_invalido


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
            Dose calculada, momento de aplicação ou motivo da não aplicação.

        ``valor_calculado`` (float)
            Dose de gesso em kg/ha. Zero quando não necessário.

        ``regra_acionada`` (str)
            Identificador da condição disparada. Valores possíveis:

            - ``"gessagem_ca_baixo_e_al_alto"`` — Ca baixo E saturação Al alta
            - ``"gessagem_ca_subsuperficial_baixo"`` — apenas Ca abaixo do limiar
            - ``"gessagem_saturacao_al_alta"`` — apenas saturação Al acima do limiar
            - ``"sem_necessidade_gessagem"`` — Ca e Al dentro dos limites
            - ``"nao_aplicavel_categoria"`` — talhão não é cana planta
            - ``"dado_ausente_ca2"`` / ``"dado_ausente_al2"`` / ``"dado_ausente_sb2"`` — campo nulo ou NaN

        ``detalhes`` (dict)
            Campos granulares: dose, momento, Ca subsuperficial, saturação Al,
            tipo de solo e argila estimada.

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
        "orientacao": "Aplicar 2100 kg/ha de gesso agrícola. ...",
        "valor_calculado": 2100,
        "regra_acionada": "gessagem_ca_subsuperficial_baixo",
        "detalhes": {...}
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

    # 1. Pré-condição: apenas cana planta
    if talhao.get("categoria") != "Formação":
        return {
            "orientacao":      "Gessagem de incorporação recomendada apenas para cana planta (Formação).",
            "valor_calculado": None,
            "regra_acionada":  "nao_aplicavel_categoria",
            "detalhes":        {"id_talhao": talhao.get("id_talhao")},
        }

    # 2. Validar campos de solo obrigatórios (None e NaN)
    for campo in ("ca2", "al2", "sb2"):
        if campo_invalido(talhao.get(campo)):
            return {
                "orientacao":      f"Dado ausente ou inválido: {campo}.",
                "valor_calculado": None,
                "regra_acionada":  f"dado_ausente_{campo}",
                "detalhes":        {"id_talhao": talhao.get("id_talhao"), "campo_ausente": campo},
            }

    # 3. Extrair valores
    ca_sub    = float(talhao["ca2"])
    al_sub    = float(talhao["al2"])
    sb_sub    = float(talhao["sb2"])
    tipo_solo = talhao.get("tipo_solo", "A Definir") or "A Definir"
    id_talhao = talhao.get("id_talhao", "desconhecido")

    # 4. Saturação por alumínio
    denominador = sb_sub + al_sub
    sat_al      = (al_sub / denominador * 100) if denominador > 0 else 0.0

    # 5. Lógica principal
    gatilho_ca = ca_sub < CA_MINIMO
    gatilho_al = sat_al > SAT_AL_MAXIMO

    if gatilho_ca or gatilho_al:
        argila_g_kg = TABELA_ARGILA.get(tipo_solo, TABELA_ARGILA["A Definir"])
        dose_gesso  = float(argila_g_kg * 5)
        momento     = "na etapa da grade niveladora, antes do plantio"

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
        dose_gesso  = 0.0
        momento     = "não aplicável — Ca e saturação de Al adequados"
        regra       = "sem_necessidade_gessagem"
        argila_g_kg = None
        orientacao  = (
            f"Gessagem não necessária. "
            f"Ca subsuperficial ({ca_sub} mmolc/dm³) e saturação de Al "
            f"({sat_al:.1f}%) dentro dos limites."
        )

    # 6. Retorno padronizado
    return {
        "orientacao":      orientacao,
        "valor_calculado": dose_gesso,
        "regra_acionada":  regra,
        "detalhes": {
            "id_talhao":             id_talhao,
            "dose_gesso_kgha":       dose_gesso,
            "momento":               momento,
            "ca_sub_mmolc":          ca_sub,
            "sat_al_perc":           round(sat_al, 2),
            "tipo_solo":             tipo_solo,
            "argila_estimada_gkg":   argila_g_kg,
        },
    }
