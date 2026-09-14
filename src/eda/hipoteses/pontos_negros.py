"""Fase 3.5 — pontos negros (F3-1; spec §2.8 C). H17–H19.

- H17 — os trechos com ≥20 acidentes/ano são estáveis? Split-half por semestre +
  correlação de postos. **Devolutiva:** a chave `(br, km)` de G6 não é única entre
  UFs — 508 dos 623 "trechos negros" da Fase 2.2 misturavam estados. A chave
  correta é `(uf, br, km)`, que dá **382** trechos negros, não 623.
- H18 — o trecho negro tem assinatura própria de via (`tipo_pista`, `uso_solo`,
  `tipo_acidente`)? Caracterizar o cluster BR-101 km 205–208.
- H19 — concentração de **volume** ≠ concentração de **mortes**: as duas listas e
  a interseção. Decide se o dashboard mostra um mapa ou dois.

Entregável: `reports/pontos_negros.csv` (`gerar_csv`).

Uso: ``python -m src.eda.hipoteses.pontos_negros``
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

from src.const import FIGURES_PATH, REPORTS_PATH  # noqa: E402
from src.eda import inferencia as inf  # noqa: E402
from src.eda.dataset import load_enriched, por_acidente, por_pessoa  # noqa: E402
from src.eda.dimensoes.geografico import com_trecho  # noqa: E402

DEST = FIGURES_PATH / "hipoteses" / "pontos_negros"
CSV_PATH = REPORTS_PATH / "pontos_negros.csv"
MIN_ACIDENTES_TRECHO = 20  # limiar G6
CHAVE = ["uf", "br", "km_trecho"]  # (br, km) NÃO é único entre UFs — devolutiva 3.5→G6
CARACTERISTICAS = ["tipo_pista", "uso_solo", "tem_curva", "tem_reta", "tem_intersecao_de_vias"]


def _spearman(x: pd.Series, y: pd.Series) -> float:
    """Correlação de postos (Pearson sobre os ranks — sem depender de scipy)."""
    return float(x.rank().corr(y.rank()))


def _trechos_acidente(df: pd.DataFrame) -> pd.DataFrame:
    a = com_trecho(por_acidente(df))
    a["s1"] = a["data_inversa"].dt.month <= 6
    return a


def trechos_negros(df: pd.DataFrame) -> pd.Index:
    a = _trechos_acidente(df)
    n = a.groupby(CHAVE).size()
    return n[n >= MIN_ACIDENTES_TRECHO].index


# --- H17 --------------------------------------------------------------
def h17_estabilidade(df: pd.DataFrame) -> dict:
    a = _trechos_acidente(df)
    negros = trechos_negros(df)
    h1 = a[a["s1"]].groupby(CHAVE).size()
    h2 = a[~a["s1"]].groupby(CHAVE).size()
    m = pd.DataFrame({"h1": h1, "h2": h2}).fillna(0)
    mn = m.loc[m.index.isin(negros)]
    return {
        "n_negros": len(negros),
        "spearman_todos_trechos": _spearman(m["h1"], m["h2"]),
        "spearman_entre_negros": _spearman(mn["h1"], mn["h2"]),
        "negros_presentes_nos_dois_semestres": int(((mn["h1"] > 0) & (mn["h2"] > 0)).sum()),
        "negros_ge5_nos_dois_semestres": int(((mn["h1"] >= 5) & (mn["h2"] >= 5)).sum()),
    }


# --- H18 ------------------------------------------------------------
def h18_assinatura(df: pd.DataFrame) -> pd.DataFrame:
    a = _trechos_acidente(df)
    negros = set(trechos_negros(df))
    a = a.assign(negro=[t in negros for t in zip(a["uf"], a["br"], a["km_trecho"])])
    linhas = {}
    for col in ["tipo_pista", "uso_solo"]:
        for val, s in a.groupby(col, observed=True):
            linhas[f"{col}={val}"] = {
                "share_negro": float((a.loc[a["negro"], col] == val).mean()),
                "share_base": float((a.loc[~a["negro"], col] == val).mean()),
            }
    out = pd.DataFrame(linhas).T
    out["razao"] = out["share_negro"] / out["share_base"]
    return out


def h18_tipo_acidente(df: pd.DataFrame) -> pd.DataFrame:
    a = _trechos_acidente(df)
    negros = set(trechos_negros(df))
    a = a.assign(negro=[t in negros for t in zip(a["uf"], a["br"], a["km_trecho"])])
    return pd.DataFrame({
        "negro": a.loc[a["negro"], "tipo_acidente"].value_counts(normalize=True),
        "base": a.loc[~a["negro"], "tipo_acidente"].value_counts(normalize=True),
    }).fillna(0.0).sort_values("negro", ascending=False)


def h18_cluster_br101(df: pd.DataFrame) -> dict:
    a = _trechos_acidente(df)
    cl = a[(a["uf"] == "SC") & (a["br"] == 101) & (a["km_trecho"].between(205, 208))]
    return {
        "n_acidentes": len(cl),
        "municipio_top": cl["municipio"].value_counts().head(2).to_dict(),
        "uso_solo": cl["uso_solo"].value_counts(normalize=True).round(2).to_dict(),
        "tipo_pista": cl["tipo_pista"].value_counts(normalize=True).round(2).to_dict(),
    }


# --- H19 ----------------------------------------------------------
def _trechos_com_metricas(df: pd.DataFrame) -> pd.DataFrame:
    pt = com_trecho(por_pessoa(df))
    g = pt.groupby(CHAVE).agg(
        acidentes=("id", "nunique"),
        mortos=("mortos", "sum"),
        feridos_graves=("feridos_graves", "sum"),
        pessoas=("mortos", "size"),
    )
    ics = [inf.taxa_com_ic(int(s), int(n)) for s, n in zip(g["mortos"], g["pessoas"])]
    g["letalidade"] = [t.p for t in ics]
    g["letalidade_ic_baixo"] = [t.ic_baixo for t in ics]
    g["letalidade_ic_alto"] = [t.ic_alto for t in ics]
    # via é ~constante no trecho: o valor modal do acidente mais frequente basta
    via = pt.drop_duplicates(CHAVE).set_index(CHAVE)
    g["municipio"] = via["municipio"]
    g["tipo_pista"] = via["tipo_pista"]
    g["uso_solo"] = via["uso_solo"]
    return g


def h19_volume_vs_mortes(df: pd.DataFrame, k: int = 50) -> dict:
    g = _trechos_com_metricas(df)
    top_ac = set(g.sort_values("acidentes", ascending=False).head(k).index)
    top_mo = set(g.sort_values("mortos", ascending=False).head(k).index)
    return {
        "k": k,
        "intersecao": len(top_ac & top_mo),
        "top_acidentes": g.loc[list(top_ac)].sort_values("acidentes", ascending=False).head(3)[
            ["acidentes", "mortos", "municipio"]
        ],
        "top_mortos": g.loc[list(top_mo)].sort_values("mortos", ascending=False).head(3)[
            ["acidentes", "mortos", "municipio"]
        ],
    }


# --- entregável -----------------------------------------------------
def gerar_csv(df: pd.DataFrame | None = None, path: Path = CSV_PATH) -> Path:
    """`reports/pontos_negros.csv` — os 382 trechos `(uf, br, km)` com ≥20
    acidentes, com município, contagem, mortos, letalidade com IC e via."""
    if df is None:
        df = load_enriched()
    g = _trechos_com_metricas(df)
    negros = g.loc[g.index.isin(trechos_negros(df))].reset_index()
    negros = negros.sort_values("acidentes", ascending=False)
    cols = [
        "br", "km_trecho", "uf", "municipio", "acidentes", "mortos", "feridos_graves",
        "pessoas", "letalidade", "letalidade_ic_baixo", "letalidade_ic_alto",
        "tipo_pista", "uso_solo",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    negros[cols].to_csv(path, index=False)
    return path


# --- figuras / resumo -------------------------------------------------
def _salvar(fig: plt.Figure, nome: str, dest: Path) -> Path:
    dest.mkdir(parents=True, exist_ok=True)
    caminho = dest / nome
    fig.savefig(caminho, dpi=120, bbox_inches="tight")
    plt.close(fig)
    return caminho


def gerar_figuras(df: pd.DataFrame, dest: Path = DEST) -> list[Path]:
    figs = []
    a = _trechos_acidente(df)
    negros = trechos_negros(df)
    h1 = a[a["s1"]].groupby(CHAVE).size()
    h2 = a[~a["s1"]].groupby(CHAVE).size()
    m = pd.DataFrame({"h1": h1, "h2": h2}).fillna(0)
    mn = m.loc[m.index.isin(negros)]
    fig, ax = plt.subplots(figsize=(5.5, 5.5))
    ax.scatter(mn["h1"], mn["h2"], s=12, alpha=0.5, color="#4C72B0")
    lim = max(mn["h1"].max(), mn["h2"].max())
    ax.plot([0, lim], [0, lim], "--", color="gray")
    ax.set_xlabel("acidentes 1º semestre"); ax.set_ylabel("acidentes 2º semestre")
    ax.set_title("H17 — estabilidade dos 623 trechos negros entre semestres")
    figs.append(_salvar(fig, "h17_estabilidade.png", dest))

    h18 = h18_tipo_acidente(df).head(8)
    fig, ax = plt.subplots(figsize=(7, 4.5))
    x = range(len(h18))
    ax.barh([i + 0.2 for i in x], h18["negro"], 0.4, label="trecho negro", color="#C44E52")
    ax.barh([i - 0.2 for i in x], h18["base"], 0.4, label="base", color="#4C72B0")
    ax.set_yticks(list(x)); ax.set_yticklabels(h18.index)
    ax.set_xlabel("share"); ax.set_title("H18 — tipo de acidente: trecho negro × base")
    ax.legend()
    figs.append(_salvar(fig, "h18_assinatura_tipo.png", dest))

    g = _trechos_com_metricas(df)
    fig, ax = plt.subplots(figsize=(6, 5))
    ax.scatter(g["acidentes"], g["mortos"], s=8, alpha=0.3, color="#4C72B0")
    ax.set_xlabel("acidentes no trecho"); ax.set_ylabel("mortos no trecho")
    ax.set_title("H19 — volume × mortes por trecho (quase ortogonais)")
    figs.append(_salvar(fig, "h19_volume_vs_mortes.png", dest))

    return figs


def resumo(df: pd.DataFrame | None = None) -> dict:
    if df is None:
        df = load_enriched()
    h17 = h17_estabilidade(df)
    h18 = h18_assinatura(df)
    h19 = h19_volume_vs_mortes(df, k=50)
    return {
        "H17": h17,
        "H18_urbano_razao": float(h18.loc["uso_solo=Sim", "razao"]),
        "H18_pista_simples_razao": float(h18.loc["tipo_pista=Simples", "razao"]),
        "H18_cluster_br101": h18_cluster_br101(df),
        "H19_intersecao_top50": h19["intersecao"],
    }


def main() -> None:
    df = load_enriched()
    import pprint

    pprint.pp(resumo(df))
    print("\nH18 assinatura:\n", h18_assinatura(df).round(3))
    print("\nH18 tipo de acidente:\n", h18_tipo_acidente(df).head(8).round(3))
    h19 = h19_volume_vs_mortes(df)
    print("\nH19 top acidentes:\n", h19["top_acidentes"])
    print("\nH19 top mortos:\n", h19["top_mortos"])
    csv = gerar_csv(df)
    print(f"\nentregável: {csv} ({sum(1 for _ in open(csv)) - 1} trechos)")
    for f in gerar_figuras(df):
        print("figura:", f)


if __name__ == "__main__":
    main()
