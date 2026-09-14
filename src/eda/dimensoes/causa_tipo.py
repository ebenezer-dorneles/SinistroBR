"""Fase 2.3 — causa e tipo do acidente (unidade: acidente).

Frequência de `causa_acidente` (69 valores) e da macro-categoria `causa_macro`
(5); frequência de `tipo_acidente` (17); distribuição de `classificacao_acidente`;
e letalidade por causa e por tipo com as **duas unidades lado a lado** — mortos
por acidente e mortos por pessoa envolvida (plan.md "Premissa metodológica":
frequência e severidade vivem em unidades diferentes).

Uso: ``python -m src.eda.dimensoes.causa_tipo``
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

from src.const import FIGURES_PATH, TOP_N  # noqa: E402
from src.eda.dataset import load_enriched, por_acidente, por_pessoa  # noqa: E402

DEST = FIGURES_PATH / "causa_tipo"


# --------------------------------------------------------------------------
# Frequências (unidade: acidente)
# --------------------------------------------------------------------------
def frequencia_causa(acidentes: pd.DataFrame, top: int | None = TOP_N) -> pd.Series:
    s = acidentes["causa_acidente"].value_counts().rename("acidentes")
    return s.head(top) if top else s


def frequencia_causa_macro(acidentes: pd.DataFrame) -> pd.Series:
    return acidentes["causa_macro"].value_counts().rename("acidentes")


def frequencia_tipo(acidentes: pd.DataFrame, top: int | None = None) -> pd.Series:
    s = acidentes["tipo_acidente"].value_counts().rename("acidentes")
    return s.head(top) if top else s


def distribuicao_classificacao(acidentes: pd.DataFrame) -> pd.Series:
    return acidentes["classificacao_acidente"].value_counts(dropna=False).rename("acidentes")


def classificacao_nula(df: pd.DataFrame) -> pd.DataFrame:
    """Detalhe do(s) acidente(s) com `classificacao_acidente` nula.

    Achado: o único caso (id 652519) tem um `mortos == 1` — deveria ser "Com
    Vítimas Fatais". É lacuna de preenchimento, não ambiguidade. A EDA/dashboard
    usam as flags de severidade por pessoa como fonte canônica (task.md 2.8),
    então o impacto é nulo; fica documentado.
    """
    ids = df.loc[df["classificacao_acidente"].isna(), "id"].unique()
    cols = [
        "id", "tipo_acidente", "causa_acidente", "tipo_envolvido",
        "estado_fisico", "mortos", "feridos_graves", "feridos_leves", "ilesos",
    ]
    return df[df["id"].isin(ids)][cols].reset_index(drop=True)


# --------------------------------------------------------------------------
# Letalidade — duas unidades lado a lado
# --------------------------------------------------------------------------
def letalidade_por(pessoas: pd.DataFrame, coluna: str) -> pd.DataFrame:
    """Letalidade por categoria de `coluna` (atributo de acidente), nas duas óticas.

    Entrada no nível pessoa. Colunas de saída:
    - `n_acidentes`, `n_pessoas`, `mortos`
    - `mortos_por_acidente` = mortos ÷ acidentes distintos
    - `mortos_por_pessoa`   = mortos ÷ pessoas envolvidas (taxa de letalidade)
    Ordenado por `mortos_por_pessoa` desc.
    """
    g = pessoas.groupby(coluna, observed=True, dropna=False)
    out = pd.DataFrame(
        {
            "n_acidentes": g["id"].nunique(),
            "n_pessoas": g.size(),
            "mortos": g["mortos"].sum().astype(int),
        }
    )
    out["mortos_por_acidente"] = out["mortos"] / out["n_acidentes"]
    out["mortos_por_pessoa"] = out["mortos"] / out["n_pessoas"]
    return out.sort_values("mortos_por_pessoa", ascending=False)


# --------------------------------------------------------------------------
# Figuras
# --------------------------------------------------------------------------
def _salvar(fig: plt.Figure, nome: str, dest: Path) -> Path:
    dest.mkdir(parents=True, exist_ok=True)
    caminho = dest / nome
    fig.savefig(caminho, dpi=120, bbox_inches="tight")
    plt.close(fig)
    return caminho


def _barh(serie: pd.Series, titulo: str, dest: Path, nome: str, cor: str = "#4C72B0") -> Path:
    fig, ax = plt.subplots(figsize=(9, max(3, 0.34 * len(serie))))
    ax.barh([str(i) for i in serie.index[::-1]], serie.values[::-1], color=cor)
    ax.set_title(titulo)
    ax.set_xlabel("acidentes")
    return _salvar(fig, nome, dest)


def gerar_figuras(acidentes: pd.DataFrame, pessoas: pd.DataFrame, dest: Path = DEST) -> list[Path]:
    figuras = [
        _barh(frequencia_causa(acidentes), f"Causas de acidente — top {TOP_N} (unidade: acidente)", dest, "frequencia_causa.png"),
        _barh(frequencia_causa_macro(acidentes), "Acidentes por macro-categoria de causa", dest, "frequencia_causa_macro.png"),
        _barh(frequencia_tipo(acidentes), "Acidentes por tipo (unidade: acidente)", dest, "frequencia_tipo.png"),
    ]

    # frequência x letalidade por tipo — o ponto central da seção
    let = letalidade_por(pessoas, "tipo_acidente")
    fig, ax = plt.subplots(figsize=(9, 6))
    ax.scatter(let["n_acidentes"], let["mortos_por_pessoa"], s=40, color="#C44E52")
    for nome, row in let.iterrows():
        ax.annotate(str(nome), (row["n_acidentes"], row["mortos_por_pessoa"]),
                    fontsize=7, xytext=(4, 2), textcoords="offset points")
    ax.set_xlabel("nº de acidentes (frequência)")
    ax.set_ylabel("mortos por pessoa (letalidade)")
    ax.set_title("Tipo de acidente: frequência × letalidade")
    figuras.append(_salvar(fig, "tipo_frequencia_vs_letalidade.png", dest))

    let_causa = letalidade_por(pessoas, "causa_macro")
    fig, axes = plt.subplots(1, 2, figsize=(12, 4))
    axes[0].bar(let_causa.index, let_causa["n_acidentes"], color="#4C72B0")
    axes[0].set_title("Acidentes por macro-causa")
    axes[0].tick_params(axis="x", rotation=30)
    axes[1].bar(let_causa.index, let_causa["mortos_por_pessoa"], color="#C44E52")
    axes[1].set_title("Letalidade (mortos por pessoa) por macro-causa")
    axes[1].tick_params(axis="x", rotation=30)
    figuras.append(_salvar(fig, "causa_macro_frequencia_vs_letalidade.png", dest))

    return figuras


# --------------------------------------------------------------------------
def resumo(df: pd.DataFrame | None = None) -> dict:
    if df is None:
        df = load_enriched()
    acidentes = por_acidente(df)
    pessoas = por_pessoa(df)

    causa = frequencia_causa(acidentes, top=None)
    macro = frequencia_causa_macro(acidentes)
    tipo = frequencia_tipo(acidentes)
    cls = distribuicao_classificacao(acidentes)
    let_tipo = letalidade_por(pessoas, "tipo_acidente")
    let_macro = letalidade_por(pessoas, "causa_macro")

    return {
        "n_acidentes": len(acidentes),
        "causa_top3": causa.head(3).to_dict(),
        "causa_macro": macro.to_dict(),
        "causa_macro_falha_condutor_pct": round(100 * macro["Falha do condutor"] / macro.sum(), 1),
        "tipo_mais_frequente": (tipo.index[0], int(tipo.iloc[0])),
        "classificacao": cls.to_dict(),
        "classificacao_nulos": int(acidentes["classificacao_acidente"].isna().sum()),
        "tipo_mais_letal": (let_tipo.index[0], round(float(let_tipo["mortos_por_pessoa"].iloc[0]), 3)),
        "tipo_menos_letal_com_mortos": (
            let_tipo[let_tipo["mortos"] > 0].index[-1],
            round(float(let_tipo[let_tipo["mortos"] > 0]["mortos_por_pessoa"].iloc[-1]), 3),
        ),
        "macro_mais_letal": (let_macro.index[0], round(float(let_macro["mortos_por_pessoa"].iloc[0]), 3)),
        "letalidade_tipo_tabela": let_tipo.round(4).to_dict("index"),
    }


def main() -> None:
    df = load_enriched()
    acidentes, pessoas = por_acidente(df), por_pessoa(df)

    info = resumo(df)
    for k, v in info.items():
        if k != "letalidade_tipo_tabela":
            print(f"{k}: {v}")

    print("\nclassificacao_acidente nula — detalhe:")
    print(classificacao_nula(df).to_string())

    print("\nletalidade por tipo_acidente (duas unidades):")
    print(letalidade_por(pessoas, "tipo_acidente").round(4).to_string())

    figs = gerar_figuras(acidentes, pessoas)
    print("\nfiguras:")
    for f in figs:
        print(f"  {f}")


if __name__ == "__main__":
    main()
