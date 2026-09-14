"""Fase 3.4 — via, ambiente e infraestrutura (F3-5, F3-7 + spec §2.8 A). H14–H16.

- H14 — a letalidade 2× da pista simples (V2) é o excesso de colisão frontal?
  Decomposição: letalidade por `tipo_pista` **dentro de** `tipo_acidente`.
- H15 — geometria (declive/curva, V5) agrava após ajustar por `tipo_pista` e
  `uso_solo`? Interação com a causa `"Velocidade Incompatível"` (proxy, C1).
- H16 — causa × `condicao_metereologica` × gravidade (3-way). V1 indica taxa
  quase plana; testar formalmente, foco em Nevoeiro/Neblina. `sem sinal` com
  número é entregável.

Base: `apenas_vitimas(com_desfecho=True)`.

Uso: ``python -m src.eda.hipoteses.via``
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

from src.const import CAUSA_PROXY_VELOCIDADE, FIGURES_PATH  # noqa: E402
from src.eda import inferencia as inf  # noqa: E402
from src.eda.dataset import (  # noqa: E402
    apenas_vitimas,
    load_enriched,
    por_acidente,
    por_pessoa,
)

DEST = FIGURES_PATH / "hipoteses" / "via"
TIPOS_FREQUENTES = [
    "Colisão frontal", "Colisão traseira", "Saída de leito carroçável",
    "Colisão transversal", "Atropelamento de Pedestre", "Tombamento",
]


def base(df: pd.DataFrame | None = None) -> pd.DataFrame:
    if df is None:
        df = load_enriched()
    return apenas_vitimas(por_pessoa(df), com_desfecho=True)


# --- H14 --------------------------------------------------------------
def h14_pista_dentro_de_tipo(b: pd.DataFrame) -> pd.DataFrame:
    """Letalidade por `tipo_pista` dentro de cada `tipo_acidente` frequente."""
    sub = b[b["tipo_acidente"].isin(TIPOS_FREQUENTES)]
    return sub.pivot_table("mortos", index="tipo_acidente", columns="tipo_pista", aggfunc="mean")


def h14_contraste(b: pd.DataFrame) -> dict:
    """Pista simples vs. resto, bruto e padronizado por `tipo_acidente`."""
    return inf.contraste(
        b, b["tipo_pista"].eq("Simples"), "mortos", eixos=["tipo_acidente"],
        rotulo="pista simples vs dupla/múltipla",
    )


def h14_share_frontal_por_pista(b: pd.DataFrame) -> pd.Series:
    frontal = b[b["tipo_acidente"] == "Colisão frontal"]
    return (frontal.groupby("tipo_pista", observed=True).size()
            / b.groupby("tipo_pista", observed=True).size())


# --- H15 ------------------------------------------------------------
def h15_geometria_ajustada(b: pd.DataFrame) -> pd.DataFrame:
    linhas = {}
    for ind in ["tem_declive", "tem_curva", "tem_aclive", "tem_ponte"]:
        r = inf.contraste(b, b[ind], "mortos", eixos=["tipo_pista", "uso_solo"], rotulo=ind)
        linhas[ind.removeprefix("tem_")] = {
            "delta_pp": r["delta_pp"], "delta_pp_ajustado": r["delta_pp_ajustado"],
            "rr": r["rr"], "veredito": r["veredito"],
        }
    return pd.DataFrame(linhas).T


def h15_interacao_velocidade(b: pd.DataFrame, df: pd.DataFrame) -> pd.DataFrame:
    ac = por_acidente(df)
    vel_ids = set(ac.loc[ac["causa_acidente"] == CAUSA_PROXY_VELOCIDADE, "id"])
    tmp = b.assign(vel_incompativel=b["id"].isin(vel_ids))
    return tmp.pivot_table("mortos", index="tem_declive", columns="vel_incompativel", aggfunc="mean")


# --- H16 ----------------------------------------------------------
def h16_letalidade_por_meteoro(b: pd.DataFrame) -> pd.DataFrame:
    return inf.tabela_estratificada(b, "condicao_metereologica", "mortos").sort_values(
        "taxa", ascending=False
    )


def h16_3way_causa_meteoro(b: pd.DataFrame) -> pd.DataFrame:
    piv = b.pivot_table("mortos", index="causa_macro", columns="condicao_metereologica", aggfunc="mean")
    cnt = b.pivot_table("mortos", index="causa_macro", columns="condicao_metereologica", aggfunc="size")
    return piv.where(cnt >= 100)


def h16_contraste_condicao(b: pd.DataFrame, condicao: str) -> dict:
    return inf.contraste(
        b, b["condicao_metereologica"].eq(condicao), "mortos",
        eixos=["tipo_acidente", "uso_solo"], rotulo=condicao,
    )


# --- figuras / resumo -------------------------------------------------
def _salvar(fig: plt.Figure, nome: str, dest: Path) -> Path:
    dest.mkdir(parents=True, exist_ok=True)
    caminho = dest / nome
    fig.savefig(caminho, dpi=120, bbox_inches="tight")
    plt.close(fig)
    return caminho


def gerar_figuras(b: pd.DataFrame, df: pd.DataFrame, dest: Path = DEST) -> list[Path]:
    figs = []

    h14 = h14_pista_dentro_de_tipo(b)[["Dupla", "Múltipla", "Simples"]]
    fig, ax = plt.subplots(figsize=(8, 4.5))
    h14.plot(kind="bar", ax=ax)
    ax.set_ylabel("letalidade"); ax.set_title("H14 — letalidade por tipo de pista, dentro do tipo de acidente")
    ax.tick_params(axis="x", rotation=25)
    figs.append(_salvar(fig, "h14_pista_dentro_de_tipo.png", dest))

    h15 = h15_geometria_ajustada(b)
    fig, ax = plt.subplots(figsize=(7, 4))
    x = range(len(h15))
    ax.bar([i - 0.2 for i in x], h15["delta_pp"], 0.4, label="Δ bruto", color="#4C72B0")
    ax.bar([i + 0.2 for i in x], h15["delta_pp_ajustado"], 0.4, label="Δ ajustado (pista+solo)", color="#C44E52")
    ax.axhline(1.0, color="gray", ls=":", label="MIN_DELTA_PP")
    ax.set_xticks(list(x)); ax.set_xticklabels(h15.index)
    ax.set_ylabel("Δ letalidade (pp)"); ax.set_title("H15 — geometria: efeito bruto × ajustado")
    ax.legend()
    figs.append(_salvar(fig, "h15_geometria_ajustada.png", dest))

    h16 = h16_letalidade_por_meteoro(b)
    fig, ax = plt.subplots(figsize=(7, 4))
    cores = ["#C44E52" if i == "Nevoeiro/Neblina" else "#4C72B0" for i in h16.index]
    ax.bar([str(i) for i in h16.index], h16["taxa"], color=cores)
    ax.set_ylabel("letalidade"); ax.set_title("H16 — letalidade por condição meteorológica (só Nevoeiro agrava)")
    ax.tick_params(axis="x", rotation=25)
    figs.append(_salvar(fig, "h16_meteoro.png", dest))

    return figs


def resumo(df: pd.DataFrame | None = None) -> dict:
    if df is None:
        df = load_enriched()
    b = base(df)
    h14 = h14_contraste(b)
    h14p = h14_pista_dentro_de_tipo(b)
    h15 = h15_geometria_ajustada(b)
    nevoeiro = h16_contraste_condicao(b, "Nevoeiro/Neblina")
    chuva = h16_contraste_condicao(b, "Chuva")
    return {
        "H14": {k: h14[k] for k in ("taxa_exposto", "taxa_controle", "delta_pp",
                                    "delta_pp_ajustado", "rr", "ic_rr", "veredito")},
        "H14_frontal_simples_vs_dupla": (
            float(h14p.loc["Colisão frontal", "Simples"]),
            float(h14p.loc["Colisão frontal", "Dupla"]),
        ),
        "H15_declive_veredito": h15.loc["declive", "veredito"],
        "H15_declive_delta_ajustado": float(h15.loc["declive", "delta_pp_ajustado"]),
        "H15_curva_veredito": h15.loc["curva", "veredito"],
        "H15_curva_delta_ajustado": float(h15.loc["curva", "delta_pp_ajustado"]),
        "H16_nevoeiro": {k: nevoeiro[k] for k in ("n_exposto", "taxa_exposto", "delta_pp",
                                                  "delta_pp_ajustado", "rr", "ic_rr", "veredito")},
        "H16_chuva_veredito": chuva["veredito"],
        "H16_chuva_delta_pp": chuva["delta_pp"],
    }


def main() -> None:
    df = load_enriched()
    b = base(df)
    import pprint

    pprint.pp(resumo(df))
    print("\nH14 letalidade por pista dentro do tipo:\n", h14_pista_dentro_de_tipo(b).round(4))
    print("\nH14 share frontal por pista:\n", h14_share_frontal_por_pista(b).round(3))
    print("\nH15 geometria ajustada:\n", h15_geometria_ajustada(b).round(4))
    print("\nH15 interação declive × velocidade incompatível:\n", h15_interacao_velocidade(b, df).round(4))
    print("\nH16 letalidade por meteoro:\n", h16_letalidade_por_meteoro(b).round(4))
    print("\nH16 3-way causa × meteoro:\n", h16_3way_causa_meteoro(b).round(3))
    for f in gerar_figuras(b, df):
        print("figura:", f)


if __name__ == "__main__":
    main()
