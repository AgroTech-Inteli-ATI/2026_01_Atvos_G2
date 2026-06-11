from .utils import campo_invalido, sem_dado, nao_aplicavel

TCH_MINIMO_ECONOMICO: float = 55.0
CORTE_ALERTA_LONGEVIDADE: int = 6
CORTE_REFORMA_OBRIGATORIA: int = 8
SITUACOES_DESSECACAO: set = {"Fechado", "Cana Soca"}


def calcular_erradicacao(talhao: dict) -> dict:
    if talhao.get("categoria") == "Formação":
        return nao_aplicavel(
            "Talhão em formação — erradicação de soqueira não aplicável.",
            "categoria_formacao",
        )

    for campo in ("tch_prod", "no_corte"):
        if campo_invalido(talhao.get(campo)):
            return sem_dado(f"dado_ausente_{campo}")

    tch = float(talhao["tch_prod"])
    n_corte = int(talhao["no_corte"])
    situacao = talhao.get("sit_talhao", "") or ""
    id_talhao = talhao.get("id_talhao", "desconhecido")
    observacao_extra = None

    if n_corte >= CORTE_REFORMA_OBRIGATORIA:
        reforma_recomendada = True
        motivo = "longevidade máxima atingida — soqueira esgotada"
        prioridade = "alta"
        regra = "reforma_longevidade_maxima"

    elif tch < TCH_MINIMO_ECONOMICO and n_corte >= 3:
        reforma_recomendada = True
        motivo = (
            f"produtividade abaixo do limiar econômico "
            f"(TCH {tch} t/ha < {TCH_MINIMO_ECONOMICO} t/ha)"
        )
        prioridade = "alta"
        regra = "reforma_tch_baixo_corte_maduro"

    elif tch < TCH_MINIMO_ECONOMICO and n_corte < 3:
        reforma_recomendada = True
        motivo = "baixa produtividade em corte inicial — investigar estabelecimento"
        prioridade = "média"
        regra = "reforma_tch_baixo_corte_jovem"
        observacao_extra = (
            "Verificar presença de pragas (broca, cigarrinha-das-raízes) "
            "ou falhas de brotação antes de confirmar a reforma."
        )

    elif tch >= TCH_MINIMO_ECONOMICO and n_corte >= CORTE_ALERTA_LONGEVIDADE:
        reforma_recomendada = True
        motivo = "longevidade elevada — programar reforma preventiva"
        prioridade = "baixa"
        regra = "reforma_preventiva_longevidade"

    else:
        reforma_recomendada = False
        motivo = "talhão dentro dos critérios de produtividade e longevidade"
        prioridade = "nenhuma"
        regra = "sem_reforma_talhao_produtivo"

    if reforma_recomendada:
        if situacao in SITUACOES_DESSECACAO:
            dessecacao_indicada = True
            protocolo_dessecacao = (
                "Aplicar herbicida dessecante pós-colheita, antes da subsolagem."
            )
            janela_dessecacao = "Até 30 dias após a colheita do último corte."
        else:
            dessecacao_indicada = False
            protocolo_dessecacao = (
                f"Verificar situação atual do talhão com equipe de campo "
                f"(sit_talhao registrado: '{situacao}')."
            )
            janela_dessecacao = None
    else:
        dessecacao_indicada = False
        protocolo_dessecacao = "Não aplicável — reforma não recomendada."
        janela_dessecacao = None

    status = "REFORMA RECOMENDADA" if reforma_recomendada else "CONTINUAR CICLO"
    orientacao_partes = [
        f"[{status}] {motivo.capitalize()}.",
        f"Prioridade: {prioridade}.",
        f"Dessecação: {'indicada' if dessecacao_indicada else 'não indicada'}.",
        f"Protocolo: {protocolo_dessecacao}",
    ]
    if observacao_extra:
        orientacao_partes.append(f"Atenção: {observacao_extra}")
    orientacao = " ".join(orientacao_partes)

    return {
        "orientacao": orientacao,
        "valor_calculado": tch,
        "regra_acionada": regra,
        "detalhes": {
            "id_talhao": id_talhao,
            "n_corte": n_corte,
            "tch_prod": tch,
            "reforma_recomendada": reforma_recomendada,
            "motivo": motivo,
            "prioridade": prioridade,
            "dessecacao_indicada": dessecacao_indicada,
            "protocolo_dessecacao": protocolo_dessecacao,
            "janela_dessecacao": janela_dessecacao,
            "observacao": observacao_extra,
        },
    }
