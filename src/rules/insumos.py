"""
Módulo de gestão de insumos e doses — Regras de dosagem dinâmica.

Diferença em relação a fosfatagem.py:
  fosfatagem.py → decide SE o solo precisa de correção de P (análise de solo).
  insumos.py    → calcula QUANTO aplicar, ajustando a dose base pela produtividade
                  esperada (tchan_estimado) e pela textura do solo.
"""
from .utils import campo_invalido, sem_dado

# ---------------------------------------------------------------------------
# Constantes — Fosfatagem
# ---------------------------------------------------------------------------
TCH_REFERENCIA: float = 80.0
# kg P₂O₅ exportado por tonelada de cana (referência Embrapa / IAC)
P_EXPORTADO_POR_TONELADA: float = 0.40

# Dose base (kg P₂O₅/ha) por nível de P no solo — faixas IAC/Embrapa
_DOSE_BASE_P: dict[str, float] = {
    "muito_baixo": 120.0,  # p1 < 6 mg/dm³
    "baixo":        80.0,  # 6 ≤ p1 < 12
    "medio":        40.0,  # 12 ≤ p1 < 25
    "suficiente":    0.0,  # p1 ≥ 25
}

# Fator de correção pela fixação de P em função da textura
# Solos argilosos fixam mais P → precisam de dose maior
_FATOR_TEXTURA_P: dict[str, float] = {
    "Muito Argiloso": 1.20,
    "Argiloso":       1.00,  # referência
    "Médio":          0.85,
    "Arenoso":        0.70,
    "A Definir":      1.00,
}

_P_MUITO_BAIXO = 6.0
_P_BAIXO       = 12.0
_P_MEDIO       = 25.0

# ---------------------------------------------------------------------------
# Constantes — Dessecação
# ---------------------------------------------------------------------------
# Dose base (L/ha) de Glifosato 480 g/L por nível de infestação
_DOSE_BASE_DESSECACAO: dict[str, float] = {
    "baixa": 1.5,
    "média": 2.0,
    "alta":  3.0,
}

# Fator de ajuste pelo estágio da soqueira
# Soqueiras mais velhas são mais lignificadas → exigem dose maior
_FATOR_ESTAGIO_SOQUEIRA: dict[str, float] = {
    "jovem":  1.00,  # no_corte < 3
    "maduro": 1.10,  # 3 ≤ no_corte < 6
    "velho":  1.20,  # no_corte ≥ 6
}

_GLIFOSATO_G_POR_L = 480.0  # g i.a./L → converte L/ha em kg i.a./ha


# ---------------------------------------------------------------------------
# Função 1 — Fosfatagem
# ---------------------------------------------------------------------------

def calcular_dose_fosfatagem(
    p_disponivel,
    textura_solo: str | None,
    tchan_estimado,
) -> dict:
    """
    Dose de P₂O₅ ajustada pela produtividade esperada e textura do solo.

    Fórmula:
        dose_kg_ha = dose_base * fator_textura + ajuste_tchan
        ajuste_tchan = (tchan_estimado - TCH_REFERENCIA) * P_EXPORTADO_POR_TONELADA

    Parâmetros
    ----------
    p_disponivel : float
        Fósforo disponível no solo (mg/dm³) — campo p1 do silver.
    textura_solo : str
        Classe textual do solo ("Argiloso", "Arenoso", etc.) — campo tipo_solo.
    tchan_estimado : float
        Produtividade esperada (t/ha) — campo tch_prod do silver.

    Retorno
    -------
    dict com chaves: insumo, dose_kg_ha, orientacao, regra_acionada, detalhes.
    """
    if campo_invalido(p_disponivel):
        return sem_dado("dado_ausente_p_disponivel")
    if campo_invalido(tchan_estimado):
        return sem_dado("dado_ausente_tchan_estimado")

    p = float(p_disponivel)
    tch = float(tchan_estimado)
    textura = textura_solo or "A Definir"

    if p < _P_MUITO_BAIXO:
        dose_base = _DOSE_BASE_P["muito_baixo"]
        nivel_p = "muito_baixo"
    elif p < _P_BAIXO:
        dose_base = _DOSE_BASE_P["baixo"]
        nivel_p = "baixo"
    elif p < _P_MEDIO:
        dose_base = _DOSE_BASE_P["medio"]
        nivel_p = "medio"
    else:
        dose_base = _DOSE_BASE_P["suficiente"]
        nivel_p = "suficiente"

    fator_tex = _FATOR_TEXTURA_P.get(textura, _FATOR_TEXTURA_P["A Definir"])
    ajuste_tchan = (tch - TCH_REFERENCIA) * P_EXPORTADO_POR_TONELADA
    dose_final = max(0.0, round(dose_base * fator_tex + ajuste_tchan, 2))

    if dose_final == 0.0:
        orientacao = (
            f"Fosfatagem não necessária. "
            f"P {nivel_p.replace('_', ' ')} ({p} mg/dm³), "
            f"TCH estimado {tch:.0f} t/ha."
        )
        regra = "insumo_fosfato_nao_necessario"
    else:
        orientacao = (
            f"Aplicar {dose_final:.1f} kg P₂O₅/ha. "
            f"Base {dose_base:.0f} × textura {fator_tex:.2f} "
            f"+ ajuste TCH {ajuste_tchan:+.1f} kg/ha. "
            f"Nível P: {nivel_p.replace('_', ' ')}."
        )
        regra = f"insumo_fosfato_{nivel_p}"

    return {
        "insumo": "P₂O₅",
        "orientacao": orientacao,
        "dose_kg_ha": dose_final,
        "regra_acionada": regra,
        "detalhes": {
            "dose_base_kg_ha": dose_base,
            "fator_textura": fator_tex,
            "ajuste_tchan_kg_ha": round(ajuste_tchan, 2),
            "nivel_p": nivel_p,
            "p_disponivel_mgdm3": p,
            "tchan_estimado_tha": tch,
        },
    }


# ---------------------------------------------------------------------------
# Função 2 — Dessecação
# ---------------------------------------------------------------------------

def calcular_dose_dessecacao(
    infestacao: str,
    estagio_soqueira: str,
) -> dict:
    """
    Dose de Glifosato 480 g/L para dessecação pré-reforma de soqueira.

    Fórmula:
        dose_l_ha = dose_base[infestacao] * fator_estagio[estagio_soqueira]
        dose_kg_ha = dose_l_ha * (480 g/L / 1000)   → kg i.a./ha

    Parâmetros
    ----------
    infestacao : str
        Nível de infestação da soqueira ("baixa", "média", "alta").
    estagio_soqueira : str
        Estágio de envelhecimento da soqueira ("jovem", "maduro", "velho"),
        derivado de no_corte: jovem < 3, maduro 3-5, velho ≥ 6.

    Retorno
    -------
    dict com chaves: insumo, dose_kg_ha, dose_l_ha, orientacao,
                     regra_acionada, detalhes.
    """
    infestacoes_validas = set(_DOSE_BASE_DESSECACAO)
    estagios_validos = set(_FATOR_ESTAGIO_SOQUEIRA)

    if infestacao not in infestacoes_validas:
        return sem_dado(f"infestacao_invalida__{infestacao}")
    if estagio_soqueira not in estagios_validos:
        return sem_dado(f"estagio_soqueira_invalido__{estagio_soqueira}")

    dose_base_l = _DOSE_BASE_DESSECACAO[infestacao]
    fator_est = _FATOR_ESTAGIO_SOQUEIRA[estagio_soqueira]
    dose_l = round(dose_base_l * fator_est, 2)
    dose_kg = round(dose_l * _GLIFOSATO_G_POR_L / 1000.0, 3)

    orientacao = (
        f"Aplicar {dose_l:.2f} L/ha de Glifosato 480 g/L "
        f"({dose_kg:.3f} kg i.a./ha). "
        f"Infestação: {infestacao} | Estágio soqueira: {estagio_soqueira}. "
        f"Aplicar pós-colheita, antes da subsolagem."
    )

    return {
        "insumo": "Glifosato 480 g/L",
        "orientacao": orientacao,
        "dose_kg_ha": dose_kg,
        "dose_l_ha": dose_l,
        "regra_acionada": f"dessecacao_{infestacao}_{estagio_soqueira}",
        "detalhes": {
            "dose_base_l_ha": dose_base_l,
            "fator_estagio": fator_est,
            "dose_comercial_l_ha": dose_l,
            "dose_ia_kg_ha": dose_kg,
            "infestacao": infestacao,
            "estagio_soqueira": estagio_soqueira,
        },
    }


# ---------------------------------------------------------------------------
# Helpers de derivação de parâmetros a partir do talhão
# ---------------------------------------------------------------------------

def estagio_soqueira_de_no_corte(no_corte) -> str:
    """Converte no_corte (int) em categoria de estágio da soqueira."""
    try:
        n = int(no_corte)
    except (TypeError, ValueError):
        return "jovem"
    if n < 3:
        return "jovem"
    if n < 6:
        return "maduro"
    return "velho"


def infestacao_de_sit_talhao(sit_talhao: str | None) -> str:
    """
    Estima nível de infestação a partir da situação do talhão.
    Proxy conservador até que dado de campo esteja disponível.
    """
    sit = (sit_talhao or "").strip()
    if sit == "Fechado":
        return "alta"
    if sit == "Cana Soca":
        return "média"
    return "baixa"
