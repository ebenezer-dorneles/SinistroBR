"""Fase 3.3 — tempo: noite, madrugada e álcool (F3-4 + F3-6; spec B/E). H10–H13.

- H10 — a madrugada de sexta/sábado (T4) tem mais "Ingestão de álcool" na
  composição de causas que o resto da semana? (composição, não taxa; álcool é
  sub-registrado — piso, não prevalência)
- H11 — a letalidade noturna (T6) sobrevive ao ajuste por `tipo_acidente` e
  `uso_solo`? Ou é composição (noite = mais rural = mais frontal)?
- H12 — dia da semana × `fase_dia` × `tipo_acidente`: o tipo de acidente do fim
  de semana à noite é diferente do da segunda de manhã?
- H13 — horário × `tipo_acidente` × mortes: mortos/acidente vs mortos/pessoa.

Base de severidade: `apenas_vitimas(com_desfecho=True)`. Composição de causa:
nível acidente (`por_acidente`).

Uso: ``python -m src.eda.hipoteses.tempo``
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

from src.const import CAUSA_ALCOOL_CONDUTOR, FIGURES_PATH  # noqa: E402
from src.eda import inferencia as inf  # noqa: E402
from src.eda.dataset import (  # noqa: E402
    apenas_vitimas,
    load_enriched,
    por_acidente,
    por_pessoa,
)

DEST = FIGURES_PATH / "hipoteses" / "tempo"
HORAS_MADRUGADA = [0, 1, 2, 3, 4]
DIAS_FDS = ["sexta-feira", "sábado", "domingo"]
FASES_NOITE = ["Plena Noite", "Amanhecer"]
CAUSAS_NOTURNAS = [
    CAUSA_ALCOOL_CONDUTOR,
    "Condutor Dormindo",
    "Velocidade Incompatível",
    "Ausência de reação do condutor",
]


# --- H10 --------------------------------------------------------------
def h10_composicao_causa_madrugada_fds(ac: pd.DataFrame) -> pd.DataFrame:
    """% de acidentes com cada causa: madrugada de fim de semana vs. resto."""
    madru_fds = ac["hora"].isin(HORAS_MADRUGADA) & ac["dia_semana"].isin(DIAS_FDS)
    linhas = {}
    for c in CAUSAS_NOTURNAS:
        linhas[c] = {
            "share_madru_fds": float((ac.loc[madru_fds, "causa_acidente"] == c).mean()),
            "share_resto": float((ac.loc[~madru_fds, "causa_acidente"] == c).mean()),
        }
    out = pd.DataFrame(linhas).T
    out["razao"] = out["share_madru_fds"] / out["share_resto"]
    out.attrs["n_madru_fds"] = int(madru_fds.sum())
    return out


# --- H11 ------------------------------------------------------------
def h11_letalidade_noturna_ajustada(b: pd.DataFrame) -> dict:
    bruta = b.groupby("fase_dia", observed=True)["mortos"].mean()
    ajust_comp = inf.padronizacao_direta(
        b, "fase_dia", "mortos", eixos=["tipo_acidente", "uso_solo"]
    )
    ajust_padrao = inf.padronizacao_direta(
        b, "fase_dia", "mortos", eixos=["faixa_etaria", "tipo_veiculo"]
    )
    noite = b["fase_dia"].isin(FASES_NOITE)
    contraste = inf.contraste(
        b, noite, "mortos", eixos=["tipo_acidente", "uso_solo"],
        rotulo="noite/amanhecer vs anoitecer/dia",
    )
    return {
        "bruta": bruta,
        "ajustada_composicao": ajust_comp,
        "ajustada_padrao": ajust_padrao,
        "contraste": contraste,
    }


# --- H12 -----------------------------------------------------------
def h12_tipo_por_janela(ac: pd.DataFrame) -> pd.DataFrame:
    fds_noite = ac["dia_semana"].isin(["sábado", "domingo"]) & ac["fase_dia"].eq("Plena Noite")
    seg_dia = ac["dia_semana"].eq("segunda-feira") & ac["fase_dia"].eq("Pleno dia")
    return pd.DataFrame({
        "fds_noite": ac.loc[fds_noite, "tipo_acidente"].value_counts(normalize=True),
        "segunda_dia": ac.loc[seg_dia, "tipo_acidente"].value_counts(normalize=True),
    }).fillna(0.0).sort_values("fds_noite", ascending=False)


# --- H13 -----------------------------------------------------------
def h13_mortes_por_tipo_e_hora(pp: pd.DataFrame) -> pd.DataFrame:
    g = pp.groupby("tipo_acidente", observed=True).agg(
        mortos=("mortos", "sum"), pessoas=("mortos", "size"), acidentes=("id", "nunique")
    )
    g["mortos_por_acidente"] = g["mortos"] / g["acidentes"]
    g["mortos_por_pessoa"] = g["mortos"] / g["pessoas"]
    return g.sort_values("mortos_por_pessoa", ascending=False)


def h13_migracao_horaria(pp: pd.DataFrame, tipos: list[str]) -> pd.DataFrame:
    janela = pd.cut(pp["hora"], [-1, 5, 11, 17, 23], labels=["0-5", "6-11", "12-17", "18-23"])
    total = pp.groupby(janela, observed=True)["id"].nunique()
    linhas = {}
    for t in tipos:
        m = pp["tipo_acidente"].str.contains(t, na=False)
        linhas[t] = (pp[m].groupby(janela, observed=True)["id"].nunique() / total)
    return pd.DataFrame(linhas)


# --- figuras / resumo -------------------------------------------------
def _salvar(fig: plt.Figure, nome: str, dest: Path) -> Path:
    dest.mkdir(parents=True, exist_ok=True)
    caminho = dest / nome
    fig.savefig(caminho, dpi=120, bbox_inches="tight")
    plt.close(fig)
    return caminho


def gerar_figuras(ac: pd.DataFrame, b: pd.DataFrame, pp: pd.DataFrame, dest: Path = DEST) -> list[Path]:
    figs = []

    h10 = h10_composicao_causa_madrugada_fds(ac)
    fig, ax = plt.subplots(figsize=(7, 4))
    x = range(len(h10))
    ax.bar([i - 0.2 for i in x], h10["share_madru_fds"], 0.4, label="madrugada fim de semana", color="#C44E52")
    ax.bar([i + 0.2 for i in x], h10["share_resto"], 0.4, label="resto da semana", color="#4C72B0")
    ax.set_xticks(list(x)); ax.set_xticklabels([c[:22] for c in h10.index], rotation=25, ha="right")
    ax.set_ylabel("share dos acidentes"); ax.set_title("H10 — composição de causa: madrugada FDS")
    ax.legend()
    figs.append(_salvar(fig, "h10_composicao_causa.png", dest))

    h11 = h11_letalidade_noturna_ajustada(b)
    fig, ax = plt.subplots(figsize=(7, 4))
    idx = list(h11["bruta"].index)
    ax.plot(idx, h11["bruta"].values, "o-", label="bruta", color="#4C72B0")
    ax.plot(idx, h11["ajustada_composicao"]["taxa_ajustada"].reindex(idx).values, "s--",
            label="ajustada (tipo acidente + uso solo)", color="#C44E52")
    ax.set_ylabel("letalidade"); ax.set_title("H11 — letalidade por fase do dia: bruta × ajustada")
    ax.legend()
    figs.append(_salvar(fig, "h11_letalidade_noturna.png", dest))

    h12 = h12_tipo_por_janela(ac).head(7)
    fig, ax = plt.subplots(figsize=(7, 4.5))
    x = range(len(h12))
    ax.barh([i + 0.2 for i in x], h12["fds_noite"], 0.4, label="fim de semana noite", color="#C44E52")
    ax.barh([i - 0.2 for i in x], h12["segunda_dia"], 0.4, label="segunda pleno dia", color="#4C72B0")
    ax.set_yticks(list(x)); ax.set_yticklabels(h12.index)
    ax.set_xlabel("share"); ax.set_title("H12 — tipo de acidente por janela")
    ax.legend()
    figs.append(_salvar(fig, "h12_tipo_por_janela.png", dest))

    mig = h13_migracao_horaria(pp, ["Colisão frontal", "Atropelamento", "Colisão traseira"])
    fig, ax = plt.subplots(figsize=(7, 4))
    for col in mig.columns:
        ax.plot(mig.index, mig[col], "o-", label=col)
    ax.set_ylabel("share dos acidentes na janela"); ax.set_title("H13 — migração horária do tipo de acidente")
    ax.legend()
    figs.append(_salvar(fig, "h13_migracao_horaria.png", dest))

    return figs


def resumo(df: pd.DataFrame | None = None) -> dict:
    if df is None:
        df = load_enriched()
    ac = por_acidente(df)
    b = apenas_vitimas(por_pessoa(df), com_desfecho=True)
    pp = por_pessoa(df)

    h10 = h10_composicao_causa_madrugada_fds(ac)
    h11 = h11_letalidade_noturna_ajustada(b)
    h12 = h12_tipo_por_janela(ac)
    h13 = h13_mortes_por_tipo_e_hora(pp)

    return {
        "H10_alcool_share_madru_fds": float(h10.loc[CAUSA_ALCOOL_CONDUTOR, "share_madru_fds"]),
        "H10_alcool_share_resto": float(h10.loc[CAUSA_ALCOOL_CONDUTOR, "share_resto"]),
        "H10_alcool_razao": float(h10.loc[CAUSA_ALCOOL_CONDUTOR, "razao"]),
        "H10_n_madru_fds": h10.attrs["n_madru_fds"],
        "H11_bruta_noite": float(h11["bruta"]["Plena Noite"]),
        "H11_bruta_dia": float(h11["bruta"]["Pleno dia"]),
        "H11_ajust_noite": float(h11["ajustada_composicao"].loc["Plena Noite", "taxa_ajustada"]),
        "H11_ajust_dia": float(h11["ajustada_composicao"].loc["Pleno dia", "taxa_ajustada"]),
        "H11_veredito": h11["contraste"]["veredito"],
        "H11_delta_pp": h11["contraste"]["delta_pp"],
        "H11_delta_pp_ajustado": h11["contraste"]["delta_pp_ajustado"],
        "H12_top_fds_noite": h12.index[0],
        "H12_top_segunda_dia": h12.sort_values("segunda_dia", ascending=False).index[0],
        "H13_frontal_mortos_por_acidente": float(h13.loc["Colisão frontal", "mortos_por_acidente"]),
        "H13_atropelamento_mortos_por_pessoa": float(h13.loc["Atropelamento de Pedestre", "mortos_por_pessoa"]),
    }


def main() -> None:
    df = load_enriched()
    ac = por_acidente(df)
    b = apenas_vitimas(por_pessoa(df), com_desfecho=True)
    pp = por_pessoa(df)
    import pprint

    pprint.pp(resumo(df))
    print("\nH10:\n", h10_composicao_causa_madrugada_fds(ac).round(4))
    h11 = h11_letalidade_noturna_ajustada(b)
    print("\nH11 bruta:\n", h11["bruta"].round(4))
    print("H11 ajustada (composição):\n", h11["ajustada_composicao"].round(4))
    print("\nH12:\n", h12_tipo_por_janela(ac).head(8).round(3))
    print("\nH13:\n", h13_mortes_por_tipo_e_hora(pp).head(8).round(3))
    print("\nH13 migração:\n", h13_migracao_horaria(pp, ["Colisão frontal", "Atropelamento"]).round(3))
    for f in gerar_figuras(ac, b, pp):
        print("figura:", f)


if __name__ == "__main__":
    main()
