from .utils import campo_invalido, sem_dado, nao_aplicavel

P_MUITO_BAIXO: float = 6.0
P_BAIXO: float = 12.0
P_MEDIO: float = 25.0

DOSE_P_MUITO_BAIXO: float = 120.0
DOSE_P_BAIXO: float = 80.0
DOSE_P_MEDIO: float = 40.0
DOSE_P_SUFICIENTE: float = 0.0

MOMENTO_APLICACAO: str = "no sulco de plantio (100% da dose) ou pré-plantio incorporado"


def calcular_necessidade_fosfatagem(talhao: dict) -> dict:
    if talhao.get("categoria") != "Formação":
        return nao_aplicavel(
            "Fosfatagem de sulco aplicável apenas na implantação (cana planta — Formação).",
            "categoria_nao_formacao",
        )

    if campo_invalido(talhao.get("p1")):
        return sem_dado("dado_ausente_p1")

    p_disponivel = float(talhao["p1"])
    id_talhao = talhao.get("id_talhao", "desconhecido")

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
            f"P disponível ({p_disponivel} mg/dm³) está em nível "
            f"suficiente (≥ {P_MEDIO} mg/dm³)."
        )

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
