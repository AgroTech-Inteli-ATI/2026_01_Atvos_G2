from datetime import date


# Janelas de plantio recomendadas por perfil de maturação (Centro-Sul do Brasil)
# Chave: MAN_HIPOT | Valores: meses ideais de plantio (1 = janeiro ... 12 = dezembro)
JANELAS_PLANTIO = {
    "Precoce":   {"meses": [10, 11, 12],     "descricao": "outubro a dezembro"},
    "Média":     {"meses": [1,  2,  3],      "descricao": "janeiro a março"},
    "Tardia":    {"meses": [3,  4,  5],      "descricao": "março a maio"},
    "A Definir": {"meses": [10, 11, 12, 1, 2, 3, 4, 5], "descricao": "outubro a maio (janela ampla — validar com agrônomo)"},
}

# Duração estimada do ciclo cana planta por perfil (meses desde o plantio até o corte)
CICLO_CANA_PLANTA = {
    "Precoce":   {"min": 12, "max": 14},
    "Média":     {"min": 14, "max": 16},
    "Tardia":    {"min": 16, "max": 18},
    "A Definir": {"min": 12, "max": 18},
}

# Derivação de perfil a partir do campo 'estagio' (fallback quando man_hipot ausente)
# Usado enquanto limpeza.py não regenerar o silver com a coluna man_hipot
_ESTAGIO_PARA_PERFIL = {
    "Formação 12m":      "Precoce",
    "Cana de Ano":       "Precoce",
    "Formação 15m":      "Média",
    "Cana de Inverno":   "Média",
    "Formação 18m":      "Tardia",
    "Cana de Ano e Meio": "Tardia",
}

def _inferir_perfil(talhao: dict) -> str:
    """
    Retorna o perfil de maturação do talhão.
    Prioridade: man_hipot (coluna direta) → estagio (fallback derivado).
    """
    man = talhao.get("man_hipot") or talhao.get("MAN_HIPOT") or ""
    man = str(man).strip() if man else ""
    if man and man not in ("None", "nan", ""):
        return man

    # Fallback: derivar do estagio
    estagio = str(talhao.get("estagio") or "").strip()
    return _ESTAGIO_PARA_PERFIL.get(estagio, "")


def calcular_janela_plantio(talhao: dict) -> dict:
    """
    Sugere a janela de plantio recomendada para o talhão com base no perfil
    de maturação (MAN_HIPOT) e na data de plantio registrada.

    Para talhões em Formação (cana planta), estima a janela ideal de
    plantio de novos talhões em reforma futura, além de calcular a faixa
    esperada de colheita.

    Para talhões em produção (Cana Soca), a janela de plantio não se aplica
    diretamente — o módulo retorna orientação para planejamento de reforma.

    Parameters
    ----------
    talhao : dict
        Registro de um talhão do inventario_silver.csv. Campos utilizados:

        - ``categoria`` (str): "Formação", "Cana Soca" ou "Muda"
        - ``man_hipot`` (str): perfil de maturação — "Precoce", "Média",
          "Tardia" ou "A Definir"
        - ``data_plantio`` (str | datetime, opcional): data do plantio atual;
          usada para estimar a janela de colheita esperada
        - ``unidade_industrial`` (str, opcional): código da UI

    Returns
    -------
    dict
        ``orientacao`` (str)
            Texto descritivo com a janela de plantio sugerida e, quando
            possível, a faixa estimada de colheita.

        ``valor_calculado`` (None)
            Não há valor numérico associado a esta regra.

        ``regra_acionada`` (str)
            Identificador da condição disparada. Valores possíveis:

            - ``"janela_precoce"`` — perfil Precoce, janela out–dez
            - ``"janela_media"`` — perfil Média, janela jan–mar
            - ``"janela_tardia"`` — perfil Tardia, janela mar–mai
            - ``"janela_a_definir"`` — perfil não especificado
            - ``"janela_soca_reforma"`` — cana soca com planejamento de reforma
            - ``"janela_muda"`` — talhão de muda (não aplicável)
            - ``"sem_dado_man_hipot"`` — MAN_HIPOT ausente

    Notes
    -----
    **Pendente de validação com PO ATVOS:** os meses sugeridos são baseados
    no calendário sucroalcooleiro do Centro-Sul do Brasil. Unidades industriais
    em outras regiões podem ter janelas distintas. Confirmar tabela de aptidão
    regional com o time agronômico antes de usar em produção.

    Examples
    --------
    >>> talhao = {
    ...     "id_talhao": "T001",
    ...     "categoria": "Formação",
    ...     "man_hipot": "Média",
    ...     "data_plantio": "2025-02-15",
    ... }
    >>> calcular_janela_plantio(talhao)
    {
        "orientacao": "Perfil Média | janela de plantio: janeiro a março ...",
        "valor_calculado": None,
        "regra_acionada": "janela_media"
    }
    """

    categoria  = talhao.get("categoria", "")
    man_hipot  = _inferir_perfil(talhao)

    # Talhão de muda: não aplicável
    if categoria == "Muda":
        return {
            "orientacao":      "talhão de muda — janela de plantio não aplicável a viveiros",
            "valor_calculado": None,
            "regra_acionada":  "janela_muda",
        }

    # Sem perfil identificável: não é possível calcular
    if not man_hipot or man_hipot in ("None", "nan", ""):
        return {
            "orientacao":      "sem dados de perfil de maturação (MAN_HIPOT) — janela de plantio indeterminada",
            "valor_calculado": None,
            "regra_acionada":  "sem_dado_man_hipot",
        }

    # Normalizar para chave da tabela
    chave = man_hipot if man_hipot in JANELAS_PLANTIO else "A Definir"
    janela = JANELAS_PLANTIO[chave]
    ciclo  = CICLO_CANA_PLANTA[chave]

    # -- Cana Soca: orientação de planejamento de reforma --
    if categoria != "Formação":
        regra = "janela_soca_reforma"
        orientacao = (
            f"Para reforma futura deste talhão: plantar no período de {janela['descricao']}. "
            f"Perfil {man_hipot} — ciclo estimado de {ciclo['min']} a {ciclo['max']} meses após o plantio. "
            f"⚠️ Validar janela regional com equipe agronômica."
        )
        return {
            "orientacao":      orientacao,
            "valor_calculado": None,
            "regra_acionada":  regra,
        }

    # -- Cana Planta (Formação): janela de plantio + estimativa de colheita --
    regra_map = {
        "Precoce":   "janela_precoce",
        "Média":     "janela_media",
        "Tardia":    "janela_tardia",
        "A Definir": "janela_a_definir",
    }
    regra = regra_map.get(chave, "janela_a_definir")

    # Tentar estimar janela de colheita a partir da data de plantio
    estimativa_colheita = ""
    data_plantio_raw = talhao.get("data_plantio")
    if data_plantio_raw and str(data_plantio_raw) not in ("None", "nan", "NaT", ""):
        try:
            import pandas as pd
            dt_plantio = pd.to_datetime(data_plantio_raw)
            if not pd.isnull(dt_plantio):
                from dateutil.relativedelta import relativedelta
                dt_min = dt_plantio + relativedelta(months=ciclo["min"])
                dt_max = dt_plantio + relativedelta(months=ciclo["max"])
                estimativa_colheita = (
                    f" | Colheita estimada: {dt_min.strftime('%m/%Y')} a {dt_max.strftime('%m/%Y')}"
                )
        except Exception:
            pass

    orientacao = (
        f"Perfil {man_hipot} | janela de plantio recomendada: {janela['descricao']}"
        f"{estimativa_colheita}. "
        f"⚠️ Pendente validação com equipe agronômica ATVOS — calendário regional pode divergir."
    )

    return {
        "orientacao":      orientacao,
        "valor_calculado": None,
        "regra_acionada":  regra,
    }
