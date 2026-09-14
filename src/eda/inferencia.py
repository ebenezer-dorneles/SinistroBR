"""Fase 3.0 — preparo comum de inferência (plan.md §Fase 3).

Ferramentas que toda hipótese H1–H19 usa, para que nenhuma decida o veredito na
mão nem calcule IC/RR de um jeito diferente:

- `taxa_com_ic`  — proporção + IC 95% de Wilson (estável em taxa baixa, ~3%);
- `rr_com_ic`    — razão de risco + IC 95% pelo log de Katz, com o Δ em pp;
- `tabela_estratificada` — taxa + IC por célula, marcando `n < MIN_N_CELULA`;
- `padronizacao_direta`  — taxa ajustada pela distribuição de vítimas do dataset
  inteiro nos eixos `POPULACAO_PADRAO_EIXOS` (padronização direta);
- `veredito`     — aplica a regra da Premissa 2 e devolve um dos 5 vereditos.

Base fixa de severidade da fase: `apenas_vitimas(com_desfecho=True)` (Cn3).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from statistics import NormalDist

import pandas as pd

from src.const import (
    MIN_DELTA_PP,
    MIN_N_CELULA,
    MIN_RR,
    NIVEL_CONFIANCA,
    POPULACAO_PADRAO_EIXOS,
)

VEREDITOS = ("confirmado", "rejeitado", "sem sinal", "confundido", "inconclusivo (n)")


def _z(nivel: float = NIVEL_CONFIANCA) -> float:
    """Quantil normal bicaudal para o nível de confiança (0.95 -> 1.959964)."""
    return NormalDist().inv_cdf(1 - (1 - nivel) / 2)


# --------------------------------------------------------------------------
@dataclass(frozen=True)
class Taxa:
    sucessos: int
    n: int
    p: float
    ic_baixo: float
    ic_alto: float

    @property
    def pct(self) -> float:
        return 100 * self.p


def taxa_com_ic(sucessos: int, n: int, nivel: float = NIVEL_CONFIANCA) -> Taxa:
    """Proporção `sucessos/n` + IC de Wilson (score) no nível dado.

    Wilson é preferível ao intervalo de Wald para taxa baixa (letalidade ~3%) e
    para `n` pequeno: nunca escapa de [0, 1] e não degenera quando `sucessos==0`.
    """
    if n <= 0:
        return Taxa(sucessos, n, float("nan"), float("nan"), float("nan"))
    z = _z(nivel)
    p = sucessos / n
    denom = 1 + z**2 / n
    centro = (p + z**2 / (2 * n)) / denom
    margem = (z / denom) * math.sqrt(p * (1 - p) / n + z**2 / (4 * n**2))
    lo = 0.0 if sucessos == 0 else max(0.0, centro - margem)
    hi = 1.0 if sucessos == n else min(1.0, centro + margem)
    return Taxa(int(sucessos), int(n), p, lo, hi)


@dataclass(frozen=True)
class RiscoRelativo:
    taxa_exposto: Taxa
    taxa_nao_exposto: Taxa
    rr: float
    ic_baixo: float
    ic_alto: float
    delta_pp: float

    @property
    def ic_cruza_1(self) -> bool:
        if math.isnan(self.ic_baixo) or math.isnan(self.ic_alto):
            return True
        return self.ic_baixo <= 1.0 <= self.ic_alto


def rr_com_ic(
    a: int, na: int, b: int, nb: int, nivel: float = NIVEL_CONFIANCA
) -> RiscoRelativo:
    """Razão de risco (grupo exposto A vs. não exposto B) + IC 95% pelo log de Katz.

    `a` sucessos em `na` expostos, `b` sucessos em `nb` não expostos. Expõe também
    o Δ em pontos percentuais (`delta_pp = 100*(pa - pb)`).
    """
    ta = taxa_com_ic(a, na, nivel)
    tb = taxa_com_ic(b, nb, nivel)
    delta_pp = 100 * (ta.p - tb.p)
    if a == 0 or b == 0 or na == 0 or nb == 0:
        return RiscoRelativo(ta, tb, float("nan"), float("nan"), float("nan"), delta_pp)
    rr = ta.p / tb.p
    se_log = math.sqrt((1 - ta.p) / a + (1 - tb.p) / b)
    z = _z(nivel)
    return RiscoRelativo(
        ta, tb, rr,
        rr * math.exp(-z * se_log),
        rr * math.exp(z * se_log),
        delta_pp,
    )


# --------------------------------------------------------------------------
def tabela_estratificada(
    df: pd.DataFrame,
    exposicao: str,
    desfecho: str = "mortos",
    por: list[str] | None = None,
    n_min: int = MIN_N_CELULA,
) -> pd.DataFrame:
    """Taxa de `desfecho` + IC de Wilson por célula (`exposicao` × `por`).

    Não deleta célula pequena — marca `n_baixo = n < n_min`. `desfecho` é uma flag
    binária (0/1) por linha (`mortos`, `feridos_graves`). Índice: `exposicao` (+
    `por`, se dado). Colunas: `n`, `sucessos`, `taxa`, `ic_baixo`, `ic_alto`,
    `n_baixo`.
    """
    chaves = [exposicao] + list(por or [])
    g = df.groupby(chaves, observed=True, dropna=False)[desfecho].agg(["sum", "count"])
    g.columns = ["sucessos", "n"]
    ics = g.apply(lambda r: taxa_com_ic(int(r["sucessos"]), int(r["n"])), axis=1)
    g["taxa"] = [t.p for t in ics]
    g["ic_baixo"] = [t.ic_baixo for t in ics]
    g["ic_alto"] = [t.ic_alto for t in ics]
    g["n_baixo"] = g["n"] < n_min
    return g[["n", "sucessos", "taxa", "ic_baixo", "ic_alto", "n_baixo"]]


def populacao_padrao(
    df: pd.DataFrame, eixos: list[str] = POPULACAO_PADRAO_EIXOS
) -> pd.Series:
    """Distribuição (pesos que somam 1) das vítimas do dataset inteiro nos `eixos`.

    É a população-padrão da padronização direta — fixada uma vez e reutilizada em
    toda a fase (mudar a população-padrão muda toda taxa ajustada).
    """
    contagem = df.groupby(eixos, observed=True, dropna=False).size()
    return (contagem / contagem.sum()).rename("peso")


def padronizacao_direta(
    df: pd.DataFrame,
    exposicao: str,
    desfecho: str = "mortos",
    eixos: list[str] = POPULACAO_PADRAO_EIXOS,
    padrao: pd.Series | None = None,
    n_min: int = MIN_N_CELULA,
) -> pd.DataFrame:
    """Taxa de `desfecho` ajustada por `eixos` (padronização direta), por grupo de
    `exposicao`.

    Para cada valor de `exposicao`, calcula a taxa dentro de cada estrato de
    `eixos` e a recombina com os pesos da população-padrão (`padrao`, default =
    `populacao_padrao(df)`). Estrato com `n < n_min` no grupo entra com a taxa
    observada mesmo assim, mas conta para `estratos_ralos`. Devolve, por grupo:
    `n`, `taxa_bruta`, `taxa_ajustada`, `estratos_ralos`.
    """
    if padrao is None:
        padrao = populacao_padrao(df, eixos)
    padrao = padrao / padrao.sum()

    linhas = {}
    for grupo, sub in df.groupby(exposicao, observed=True, dropna=False):
        taxa_estrato = sub.groupby(eixos, observed=True, dropna=False)[desfecho].mean()
        n_estrato = sub.groupby(eixos, observed=True, dropna=False)[desfecho].size()
        alinhada = taxa_estrato.reindex(padrao.index)
        pesos = padrao.copy()
        # estrato sem observação no grupo: descarta o peso e renormaliza
        pesos = pesos[alinhada.notna()]
        pesos = pesos / pesos.sum()
        ajustada = float((alinhada.dropna() * pesos).sum())
        linhas[grupo] = {
            "n": int(len(sub)),
            "taxa_bruta": float(sub[desfecho].mean()),
            "taxa_ajustada": ajustada,
            "estratos_ralos": int((n_estrato.reindex(padrao.index).fillna(0) < n_min).sum()),
        }
    return pd.DataFrame(linhas).T


# --------------------------------------------------------------------------
def contraste(
    df: pd.DataFrame,
    exposto: "pd.Series",
    desfecho: str = "mortos",
    eixos: list[str] | None = None,
    rotulo: str = "",
) -> dict:
    """Contraste binário exposto × não exposto, bruto e ajustado, com veredito.

    `exposto` é uma máscara booleana alinhada a `df`. Devolve um dict pronto para
    virar linha de `resultados-fase3.md`: taxas, `rr` (+ IC), `delta_pp`,
    `delta_pp_ajustado` (padronização direta por `eixos`, se dados) e `veredito`.
    O veredito usa o Δ/RR brutos, mas vira `confundido` se o ajuste derruba o Δ
    abaixo de `MIN_DELTA_PP` ou inverte o sinal.
    """
    exposto = exposto.reindex(df.index).fillna(False).astype(bool)
    ex, nex = df[exposto], df[~exposto]
    a, na_ = int(ex[desfecho].sum()), len(ex)
    b, nb = int(nex[desfecho].sum()), len(nex)
    rr = rr_com_ic(a, na_, b, nb)
    n_ok = na_ >= MIN_N_CELULA and nb >= MIN_N_CELULA

    delta_aj = float("nan")
    sumiu = False
    if eixos:
        grp = df.assign(_grp=exposto.map({True: "exposto", False: "controle"}))
        pad = padronizacao_direta(grp, "_grp", desfecho, eixos=eixos)
        if {"exposto", "controle"} <= set(pad.index):
            delta_aj = 100 * (pad.loc["exposto", "taxa_ajustada"] - pad.loc["controle", "taxa_ajustada"])
            houve = abs(rr.delta_pp) >= MIN_DELTA_PP and not rr.ic_cruza_1
            sumiu = houve and (
                abs(delta_aj) < MIN_DELTA_PP
                or (delta_aj * rr.delta_pp < 0)
            )

    v = veredito(
        rr.delta_pp, rr.rr, (rr.ic_baixo, rr.ic_alto), n_ok,
        houve_efeito_bruto=abs(rr.delta_pp) >= MIN_DELTA_PP,
        efeito_bruto_sumiu=sumiu,
    )
    return {
        "rotulo": rotulo,
        "n_exposto": na_, "n_controle": nb,
        "taxa_exposto": rr.taxa_exposto.p, "taxa_controle": rr.taxa_nao_exposto.p,
        "delta_pp": rr.delta_pp, "delta_pp_ajustado": delta_aj,
        "rr": rr.rr, "ic_rr": (rr.ic_baixo, rr.ic_alto),
        "veredito": v,
    }


def veredito(
    delta_pp: float,
    rr: float,
    ic_rr: tuple[float, float],
    n_ok: bool,
    houve_efeito_bruto: bool | None = None,
    efeito_bruto_sumiu: bool = False,
) -> str:
    """Aplica a regra da Premissa 2 (plan.md) e devolve um de `VEREDITOS`.

    - `n_ok=False` (alguma célula-chave `< MIN_N_CELULA`) -> `inconclusivo (n)`;
    - `efeito_bruto_sumiu=True` (efeito existia no bruto e some/inverte após o
      ajuste) -> `confundido`;
    - `confirmado`: `abs(delta_pp) >= MIN_DELTA_PP` E `rr >= MIN_RR` (ou
      `<= 1/MIN_RR` para efeito protetor) E o IC do RR não cruza 1;
    - efeito existia como hipótese e não se sustenta -> `rejeitado`;
    - caso contrário -> `sem sinal`.
    """
    if not n_ok:
        return "inconclusivo (n)"
    if efeito_bruto_sumiu:
        return "confundido"

    lo, hi = ic_rr
    ic_ok = not (lo <= 1.0 <= hi) and not (math.isnan(lo) or math.isnan(hi))
    forte = abs(delta_pp) >= MIN_DELTA_PP and ic_ok and (
        rr >= MIN_RR or (0 < rr <= 1 / MIN_RR)
    )
    if forte:
        return "confirmado"
    if houve_efeito_bruto:
        return "rejeitado"
    return "sem sinal"
