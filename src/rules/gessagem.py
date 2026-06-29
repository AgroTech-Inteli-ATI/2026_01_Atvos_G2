from .utils import campo_invalido, sem_dado, nao_aplicavel

CA_MINIMO: float = 4.0
SAT_AL_MAXIMO: float = 40.0

TABELA_ARGILA: dict = {
    "Muito Argiloso": 550,
    "Argiloso": 420,
    "Médio": 250,
    "Arenoso": 150,
    "A Definir": 300,
}


def calcular_necessidade_gessagem(talhao: dict) -> dict:
    if talhao.get("categoria") != "Formação":
        return nao_aplicavel(
            "Gessagem de incorporação recomendada apenas para cana planta (Formação).",
            "categoria_nao_formacao",
        )

    for campo in ("ca2", "al2", "sb2"):
        if campo_invalido(talhao.get(campo)):
            return sem_dado(f"dado_ausente_{campo}")

    ca_sub = float(talhao["ca2"])
    al_sub = float(talhao["al2"])
    sb_sub = float(talhao["sb2"])
    tipo_solo = talhao.get("tipo_solo", "A Definir") or "A Definir"
    id_talhao = talhao.get("id_talhao", "desconhecido")

    denominador = sb_sub + al_sub
    sat_al = (al_sub / denominador * 100) if denominador > 0 else 0.0

    gatilho_ca = ca_sub < CA_MINIMO
    gatilho_al = sat_al > SAT_AL_MAXIMO

    if gatilho_ca and gatilho_al:
        argila_g_kg = TABELA_ARGILA.get(tipo_solo, TABELA_ARGILA["A Definir"])
        dose_gesso = float(argila_g_kg * 5)
        momento = "na etapa da grade niveladora, antes do plantio"
        regra = "gessagem_ca_baixo_e_al_alto"

        orientacao = (
            f"Aplicar {dose_gesso:.0f} kg/ha de gesso agrícola. "
            f"Momento: {momento}. "
            f"(Ca subsurf.: {ca_sub} mmolc/dm³ | Sat. Al: {sat_al:.1f}%)"
        )
    else:
        dose_gesso = 0.0
        momento = "não aplicável — Ca e saturação de Al adequados"
        regra = "gessagem_nao_necessaria"
        argila_g_kg = None
        orientacao = (
            f"Gessagem não necessária. "
            f"Ca subsuperficial ({ca_sub} mmolc/dm³) e saturação de Al "
            f"({sat_al:.1f}%) dentro dos limites."
        )

    return {
        "orientacao": orientacao,
        "valor_calculado": dose_gesso,
        "regra_acionada": regra,
        "detalhes": {
            "id_talhao": id_talhao,
            "dose_gesso_kgha": dose_gesso,
            "momento": momento,
            "ca_sub_mmolc": ca_sub,
            "sat_al_perc": round(sat_al, 2),
            "tipo_solo": tipo_solo,
            "argila_estimada_gkg": argila_g_kg,
        },
    }
