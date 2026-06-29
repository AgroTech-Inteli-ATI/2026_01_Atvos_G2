import math

def campo_invalido(valor):
    if valor is None:
        return True

    if isinstance(valor, bool):
        return True

    if not isinstance(valor, (int, float)):
        return True

    if not math.isfinite(float(valor)):
        return True

    if valor < 0:
        return True

    return False


def sem_dado(regra_acionada):
    return {
        "orientacao": "SEM_DADO",
        "valor_calculado": None,
        "regra_acionada": regra_acionada
    }


def nao_aplicavel(motivo, regra_acionada):
    return {
        "orientacao": motivo,
        "valor_calculado": None,
        "regra_acionada": regra_acionada
    }