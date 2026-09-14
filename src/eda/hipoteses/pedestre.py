"""Fase 3.1 — pedestre e atropelamento (F3-2; spec §2.8 D/B). H1–H4.

Base fixa: `apenas_vitimas(com_desfecho=True)` (Cn3). Toda taxa é P(morte | vítima).

- H1 — a letalidade de 27% do pedestre (Vi6) sobrevive ao ajuste por idade?
- H2 — atropelamento é mais letal ao anoitecer/noite que em pleno dia?
- H3 — o efeito "rural converte ferido em morto" (V3) é mais forte no pedestre?
- H4 — perfil etário/sexo da vítima-pedestre vs. as demais vítimas.

Uso: ``python -m src.eda.hipoteses.pedestre``
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

from src.const import FIGURES_PATH  # noqa: E402
from src.eda import inferencia as inf  # noqa: E402
from src.eda.dataset import apenas_vitimas, load_enriched, por_pessoa  # noqa: E402

DEST = FIGURES_PATH / "hipoteses" / "pedestre"
PAPEIS_OCUPANTE = ["Condutor", "Passageiro"]


def base(df: pd.DataFrame | None = None) -> pd.DataFrame:
    if df is None:
        df = load_enriched()
    return apenas_vitimas(por_pessoa(df), com_desfecho=True)


# --- H1 -------------------------------------------------------------------
def h1_pedestre_ajustado_idade(b: pd.DataFrame) -> dict:
    """Pedestre × ocupante de veículo, bruto e padronizado por faixa etária."""
    sub = b[b["tipo_envolvido"].isin(["Pedestre"] + PAPEIS_OCUPANTE)]
    res = inf.contraste(
        sub, sub["tipo_envolvido"].eq("Pedestre"), "mortos",
        eixos=["faixa_etaria"], rotulo="pedestre vs ocupante",
    )
    res["padronizacao"] = inf.padronizacao_direta(
        sub, "tipo_envolvido", "mortos", eixos=["faixa_etaria"]
    )
    return res


# --- H2 -----------------------------------------------------------------
def h2_atropelamento_por_fase_dia(b: pd.DataFrame) -> pd.DataFrame:
    atr = b[b["tipo_acidente"].str.contains("Atropelamento", na=False)]
    return inf.tabela_estratificada(atr, "fase_dia", "mortos")


def h2_contraste_noite_dia(b: pd.DataFrame) -> dict:
    atr = b[b["tipo_acidente"].str.contains("Atropelamento", na=False)].copy()
    noite = atr["fase_dia"].isin(["Plena Noite", "Amanhecer"])
    return inf.contraste(atr, noite, "mortos", eixos=["faixa_etaria"],
                         rotulo="atropelamento noite/amanhecer vs resto")


# --- H3 ---------------------------------------------------------------
def h3_interacao_rural_pedestre(b: pd.DataFrame) -> pd.DataFrame:
    """Δ rural−urbano da letalidade, para pedestre e para ocupante — a interação
    é a diferença entre os dois Δ."""
    linhas = {}
    for nome, sub in [
        ("pedestre", b[b["tipo_envolvido"] == "Pedestre"]),
        ("ocupante", b[b["tipo_envolvido"].isin(PAPEIS_OCUPANTE)]),
    ]:
        rural = sub[sub["uso_solo"] == "Não"]
        urb = sub[sub["uso_solo"] == "Sim"]
        rr = inf.rr_com_ic(int(rural["mortos"].sum()), len(rural),
                           int(urb["mortos"].sum()), len(urb))
        linhas[nome] = {
            "taxa_rural": rr.taxa_exposto.p, "taxa_urbano": rr.taxa_nao_exposto.p,
            "delta_pp": rr.delta_pp, "rr": rr.rr,
            "ic_baixo": rr.ic_baixo, "ic_alto": rr.ic_alto,
        }
    out = pd.DataFrame(linhas).T
    return out


# --- H4 -------------------------------------------------------------
def h4_perfil_pedestre(b: pd.DataFrame) -> pd.DataFrame:
    ped = b["tipo_envolvido"] == "Pedestre"
    out = pd.DataFrame({
        "pedestre": b[ped]["faixa_etaria"].value_counts(normalize=True),
        "demais_vitimas": b[~ped]["faixa_etaria"].value_counts(normalize=True),
    }).fillna(0.0)
    ordem = ["0-17", "18-24", "25-34", "35-44", "45-59", "60+", "Não informado"]
    return out.reindex([o for o in ordem if o in out.index])


def h4_sexo(b: pd.DataFrame) -> pd.DataFrame:
    ped = b["tipo_envolvido"] == "Pedestre"
    return pd.DataFrame({
        "pedestre": b[ped]["sexo"].value_counts(normalize=True),
        "demais_vitimas": b[~ped]["sexo"].value_counts(normalize=True),
    }).fillna(0.0)


# --- figuras / resumo -------------------------------------------------
def _salvar(fig: plt.Figure, nome: str, dest: Path) -> Path:
    dest.mkdir(parents=True, exist_ok=True)
    caminho = dest / nome
    fig.savefig(caminho, dpi=120, bbox_inches="tight")
    plt.close(fig)
    return caminho


def gerar_figuras(b: pd.DataFrame, dest: Path = DEST) -> list[Path]:
    figs = []

    pad = h1_pedestre_ajustado_idade(b)["padronizacao"]
    fig, ax = plt.subplots(figsize=(7, 4))
    x = range(len(pad))
    ax.bar([i - 0.2 for i in x], pad["taxa_bruta"], 0.4, label="bruta", color="#4C72B0")
    ax.bar([i + 0.2 for i in x], pad["taxa_ajustada"], 0.4, label="ajustada (idade)", color="#C44E52")
    ax.set_xticks(list(x)); ax.set_xticklabels(pad.index)
    ax.set_ylabel("letalidade"); ax.set_title("H1 — pedestre × ocupante, bruto vs padronizado por idade")
    ax.legend()
    figs.append(_salvar(fig, "h1_pedestre_ajuste_idade.png", dest))

    t = h2_atropelamento_por_fase_dia(b)
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.bar([str(i) for i in t.index], t["taxa"], color="#4C72B0")
    ax.set_ylabel("letalidade"); ax.set_title("H2 — atropelamento: letalidade por fase do dia")
    figs.append(_salvar(fig, "h2_atropelamento_fase_dia.png", dest))

    h3 = h3_interacao_rural_pedestre(b)
    fig, ax = plt.subplots(figsize=(7, 4))
    x = range(len(h3))
    ax.bar([i - 0.2 for i in x], h3["taxa_rural"], 0.4, label="rural", color="#C44E52")
    ax.bar([i + 0.2 for i in x], h3["taxa_urbano"], 0.4, label="urbano", color="#55A868")
    ax.set_xticks(list(x)); ax.set_xticklabels(h3.index)
    ax.set_ylabel("letalidade"); ax.set_title("H3 — efeito rural: pedestre vs ocupante")
    ax.legend()
    figs.append(_salvar(fig, "h3_interacao_rural.png", dest))

    p = h4_perfil_pedestre(b)
    fig, ax = plt.subplots(figsize=(7, 4))
    xx = range(len(p))
    ax.bar([i - 0.2 for i in xx], p["pedestre"], 0.4, label="pedestre", color="#4C72B0")
    ax.bar([i + 0.2 for i in xx], p["demais_vitimas"], 0.4, label="demais vítimas", color="#8172B2")
    ax.set_xticks(list(xx)); ax.set_xticklabels(p.index, rotation=30)
    ax.set_ylabel("proporção"); ax.set_title("H4 — faixa etária: pedestre vs demais vítimas")
    ax.legend()
    figs.append(_salvar(fig, "h4_perfil_etario.png", dest))

    return figs


def resumo(df: pd.DataFrame | None = None) -> dict:
    b = base(df)
    h1 = h1_pedestre_ajustado_idade(b)
    h2 = h2_contraste_noite_dia(b)
    h3 = h3_interacao_rural_pedestre(b)
    h4 = h4_perfil_pedestre(b)
    return {
        "n_base": len(b),
        "n_pedestre": int((b["tipo_envolvido"] == "Pedestre").sum()),
        "H1": {k: h1[k] for k in ("taxa_exposto", "taxa_controle", "delta_pp",
                                  "delta_pp_ajustado", "rr", "ic_rr", "veredito")},
        "H2": {k: h2[k] for k in ("taxa_exposto", "taxa_controle", "delta_pp",
                                  "delta_pp_ajustado", "rr", "ic_rr", "veredito")},
        "H3_pedestre_delta_pp": float(h3.loc["pedestre", "delta_pp"]),
        "H3_ocupante_delta_pp": float(h3.loc["ocupante", "delta_pp"]),
        "H3_pedestre_rr": float(h3.loc["pedestre", "rr"]),
        "H3_ocupante_rr": float(h3.loc["ocupante", "rr"]),
        "H4_pedestre_45mais": float(h4.loc[["45-59", "60+"], "pedestre"].sum()),
        "H4_demais_45mais": float(h4.loc[["45-59", "60+"], "demais_vitimas"].sum()),
    }


def main() -> None:
    b = base()
    import pprint

    pprint.pp(resumo())
    print("\nH1 padronização:\n", h1_pedestre_ajustado_idade(b)["padronizacao"].round(4))
    print("\nH2 atropelamento × fase_dia:\n", h2_atropelamento_por_fase_dia(b).round(4))
    print("\nH3 interação rural:\n", h3_interacao_rural_pedestre(b).round(4))
    print("\nH4 perfil etário:\n", h4_perfil_pedestre(b).round(3))
    print("\nH4 sexo:\n", h4_sexo(b).round(3))
    for f in gerar_figuras(b):
        print("figura:", f)


if __name__ == "__main__":
    main()
