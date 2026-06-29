from .utils import campo_invalido, sem_dado, nao_aplicavel

V_ALVO: float = 60.0
PRNT_PADRAO: float = 100.0
DOSE_MAXIMA: float = 4.0
MG_LIMIAR: float = 5.0


def calcular_necessidade_calagem(talhao: dict) -> dict:
    for campo in ("V1", "CTC1", "mg1"):
        if campo_invalido(talhao.get(campo)):
            return sem_dado(f"dado_ausente_{campo}")

    v_atual = float(talhao["V1"])
    ctc = float(talhao["CTC1"])
    mg_trocavel = float(talhao["mg1"])
    categoria = talhao.get("categoria", "")
    id_talhao = talhao.get("id_talhao", "desconhecido")

    if v_atual < V_ALVO:
        nc = ctc * (V_ALVO - v_atual) / (PRNT_PADRAO * 10)
        nc = min(nc, DOSE_MAXIMA)

        if mg_trocavel < MG_LIMIAR:
            tipo_calcario = "dolomítico"
            nc = max(nc, 1.0)
            regra = "calagem_necessaria_dolomítico"
        else:
            tipo_calcario = "calcítico ou dolomítico"
            regra = "calagem_necessaria_calcítico"

        if categoria == "Formação":
            tipo_aplicacao = "incorporada"
            momento = "60 a 90 dias antes do plantio — antes da aração"
        else:
            nc = nc * 0.5
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
        orientacao = (
            f"V% atual ({v_atual}%) já atingiu o alvo ({V_ALVO}%). "
            f"Calagem não necessária."
        )

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
