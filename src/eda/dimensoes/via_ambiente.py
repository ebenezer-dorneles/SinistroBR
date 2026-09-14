"""Fase 2.4 — condições da via e ambiente (unidade: acidente).

Distribuição de `condicao_metereologica`, `tipo_pista`, `uso_solo`, `sentido_via`
e do `tracado_via` canonicalizado (indicadores `tem_*` da Fase 2.0). Para cada
condição, **a taxa de gravidade vai ao lado da contagem** — senão o achado
"a maioria dos acidentes é em céu claro e reta" mede só exposição, não risco.

Uso: ``python -m src.eda.dimensoes.via_ambiente``
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

from src.const import FIGURES_PATH  # noqa: E402
from src.eda.dataset import load_enriched, por_acidente, por_pessoa  # noqa: E402
from src.eda.severity import resumo_severidade  # noqa: E402

DEST = FIGURES_PATH / "via_ambiente"

CONDICOES = ["condicao_metereologica", "tipo_pista", "uso_solo", "sentido_via"]
TRACADO_INDICADORES = [
    "tem_reta", "tem_curva", "tem_declive", "tem_aclive",
    "tem_intersecao_de_vias", "tem_rotatoria", "tem_retorno_regulamentado",
    "tem_em_obras", "tem_viaduto", "tem_ponte", "tem_desvio_temporario", "tem_tunel",
]


# --------------------------------------------------------------------------
def distribuicao(acidentes: pd.DataFrame, col: str) -> pd.Series:
    """Contagem de acidentes por valor de `col`, incluindo nulos."""
    return acidentes[col].value_counts(dropna=False).rename("acidentes")


def gravidade_por_condicao(pessoas: pd.DataFrame, col: str) -> pd.DataFrame:
    """Contagem + taxa de letalidade + taxa de ferido grave por valor de `col`.

    `col` é atributo de acidente; a entrada é o nível pessoa. Acrescenta
    `n_acidentes` ao resumo de severidade e ordena por letalidade desc.
    """
    base = resumo_severidade(pessoas, por=col)
    n_acid = pessoas.groupby(col, observed=True, dropna=False)["id"].nunique()
    base.insert(0, "n_acidentes", n_acid)
    return base.sort_values("taxa_letalidade", ascending=False)


def tracado_frequencia(acidentes: pd.DataFrame) -> pd.Series:
    """Nº de acidentes com cada característica de traçado (não excludentes)."""
    presentes = [c for c in TRACADO_INDICADORES if c in acidentes.columns]
    return acidentes[presentes].sum().sort_values(ascending=False).rename("acidentes")


def tracado_gravidade(pessoas: pd.DataFrame) -> pd.DataFrame:
    """Letalidade das pessoas em acidentes COM vs SEM cada característica de traçado.

    Como as características não são excludentes, cada linha compara o subconjunto
    `tem_X` contra o seu complemento — `delta` positivo = a característica agrava.
    """
    linhas = {}
    for ind in TRACADO_INDICADORES:
        if ind not in pessoas.columns:
            continue
        com = pessoas[pessoas[ind]]
        sem = pessoas[~pessoas[ind]]
        linhas[ind.removeprefix("tem_")] = {
            "n_acidentes": com["id"].nunique(),
            "letalidade_com": com["mortos"].mean(),
            "letalidade_sem": sem["mortos"].mean(),
        }
    out = pd.DataFrame(linhas).T
    out["delta"] = out["letalidade_com"] - out["letalidade_sem"]
    return out.sort_values("delta", ascending=False)


# --------------------------------------------------------------------------
def _salvar(fig: plt.Figure, nome: str, dest: Path) -> Path:
    dest.mkdir(parents=True, exist_ok=True)
    caminho = dest / nome
    fig.savefig(caminho, dpi=120, bbox_inches="tight")
    plt.close(fig)
    return caminho


def _contagem_x_taxa(g: pd.DataFrame, titulo: str, dest: Path, nome: str) -> Path:
    """Barras de contagem + linha de taxa de letalidade no eixo secundário."""
    fig, ax = plt.subplots(figsize=(9, 4.2))
    idx = [str(i) for i in g.index]
    ax.bar(idx, g["n_acidentes"], color="#4C72B0", label="acidentes")
    ax.set_ylabel("acidentes", color="#4C72B0")
    ax.tick_params(axis="x", rotation=30)
    ax2 = ax.twinx()
    ax2.plot(idx, g["taxa_letalidade"], color="#C44E52", marker="o", label="letalidade")
    ax2.set_ylabel("mortos por pessoa", color="#C44E52")
    ax2.set_ylim(bottom=0)
    ax.set_title(titulo)
    return _salvar(fig, nome, dest)


def gerar_figuras(acidentes: pd.DataFrame, pessoas: pd.DataFrame, dest: Path = DEST) -> list[Path]:
    figuras = []
    for col in ["condicao_metereologica", "tipo_pista", "uso_solo"]:
        g = gravidade_por_condicao(pessoas, col)
        figuras.append(_contagem_x_taxa(g, f"{col}: contagem × letalidade", dest, f"{col}.png"))

    freq = tracado_frequencia(acidentes)
    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.barh(freq.index[::-1], freq.values[::-1], color="#4C72B0")
    ax.set_title("Acidentes por característica de traçado (não excludentes)")
    ax.set_xlabel("acidentes")
    figuras.append(_salvar(fig, "tracado_frequencia.png", dest))

    tg = tracado_gravidade(pessoas)
    fig, ax = plt.subplots(figsize=(9, 4.5))
    cores = ["#C44E52" if d > 0 else "#55A868" for d in tg["delta"][::-1]]
    ax.barh(tg.index[::-1], tg["delta"][::-1], color=cores)
    ax.axvline(0, color="gray", lw=1)
    ax.set_title("Traçado: Δ letalidade (com característica − sem)")
    ax.set_xlabel("diferença na taxa de mortos por pessoa")
    figuras.append(_salvar(fig, "tracado_gravidade.png", dest))

    return figuras


# --------------------------------------------------------------------------
def resumo(df: pd.DataFrame | None = None) -> dict:
    if df is None:
        df = load_enriched()
    acidentes = por_acidente(df)
    pessoas = por_pessoa(df)

    met = gravidade_por_condicao(pessoas, "condicao_metereologica")
    pista = gravidade_por_condicao(pessoas, "tipo_pista")
    solo = gravidade_por_condicao(pessoas, "uso_solo")
    freq = tracado_frequencia(acidentes)
    tg = tracado_gravidade(pessoas)

    ceu_claro = int(distribuicao(acidentes, "condicao_metereologica").get("Céu Claro", 0))

    return {
        "n_acidentes": len(acidentes),
        "meteoro_nulos_acidente": int(acidentes["condicao_metereologica"].isna().sum()),
        "sentido_via_nulos": int(acidentes["sentido_via"].isna().sum()),
        "sentido_via_nulos_sao_br_nula": bool(
            (acidentes["sentido_via"].isna() & acidentes["br"].isna()).sum()
            == acidentes["sentido_via"].isna().sum()
        ),
        "ceu_claro_pct": round(100 * ceu_claro / len(acidentes), 1),
        "meteoro_letalidade": {k: round(v, 4) for k, v in met["taxa_letalidade"].items()},
        "chuva_vs_ceu_claro": (
            round(float(met.loc["Chuva", "taxa_letalidade"]), 4),
            round(float(met.loc["Céu Claro", "taxa_letalidade"]), 4),
        ),
        "pista_simples_vs_dupla": (
            round(float(pista.loc["Simples", "taxa_letalidade"]), 4),
            round(float(pista.loc["Dupla", "taxa_letalidade"]), 4),
        ),
        "rural_vs_urbano": (
            round(float(solo.loc["Não", "taxa_letalidade"]), 4),
            round(float(solo.loc["Sim", "taxa_letalidade"]), 4),
        ),
        "tracado_reta_pct": round(100 * freq["tem_reta"] / len(acidentes), 1),
        "tracado_pior_delta": (tg.index[0], round(float(tg["delta"].iloc[0]), 4)),
        "tracado_melhor_delta": (tg.index[-1], round(float(tg["delta"].iloc[-1]), 4)),
    }


def main() -> None:
    df = load_enriched()
    acidentes, pessoas = por_acidente(df), por_pessoa(df)

    for k, v in resumo(df).items():
        print(f"{k}: {v}")

    for col in CONDICOES:
        print(f"\n=== {col} ===")
        if col == "sentido_via":
            print(distribuicao(acidentes, col).to_string())
        else:
            print(gravidade_por_condicao(pessoas, col).round(4).to_string())

    print("\n=== traçado: gravidade com vs sem ===")
    print(tracado_gravidade(pessoas).round(4).to_string())

    figs = gerar_figuras(acidentes, pessoas)
    print("\nfiguras:")
    for f in figs:
        print(f"  {f}")


if __name__ == "__main__":
    main()
