"""Fase 2.2 — dimensão geográfica (unidade: acidente).

Rankings por UF, BR e município; concentração por trecho `(uf, br, km)` arredondado
(insumo dos "pontos negros" da Fase 3; a chave inclui `uf` porque `(br, km)` não é
única entre estados); densidade espacial por lat/long; e o recorte operacional da
PRF (`regional`/`delegacia`/`uop`).

**Limitação de denominador:** rankings absolutos medem *volume*, não *risco* — não
há frota, malha rodoviária nem tráfego neste dataset para normalizar. Um estado
com mais acidentes pode simplesmente ter mais rodovia federal.

Uso: ``python -m src.eda.dimensoes.geografico``
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

from src.const import (  # noqa: E402
    BRAZIL_LAT_RANGE,
    BRAZIL_LON_RANGE,
    FIGURES_PATH,
    KM_TRECHO_ROUND,
    TOP_N,
)
from src.eda.dataset import load_enriched, por_acidente  # noqa: E402

DEST = FIGURES_PATH / "geografico"


# --------------------------------------------------------------------------
# Rankings (volume, não risco)
# --------------------------------------------------------------------------
def ranking_uf(acidentes: pd.DataFrame, top: int | None = None) -> pd.Series:
    s = acidentes["uf"].value_counts().rename("acidentes")
    return s.head(top) if top else s


def ranking_br(acidentes: pd.DataFrame, top: int | None = None) -> pd.Series:
    s = acidentes["br"].dropna().astype(int).value_counts().rename("acidentes")
    s.index = s.index.astype(int)
    return s.head(top) if top else s


def ranking_municipio(acidentes: pd.DataFrame, top: int | None = TOP_N) -> pd.Series:
    s = acidentes["municipio"].value_counts().rename("acidentes")
    return s.head(top) if top else s


# --------------------------------------------------------------------------
# Concentração por trecho (uf, br, km)
# --------------------------------------------------------------------------
def com_trecho(acidentes: pd.DataFrame) -> pd.DataFrame:
    """Adiciona `km_trecho` (km arredondado por `KM_TRECHO_ROUND`) e descarta
    acidentes sem `br` identificada (br/km nulo do ETL)."""
    a = acidentes.dropna(subset=["br", "km"]).copy()
    a["km_trecho"] = (a["km"] / KM_TRECHO_ROUND).round().astype(int) * KM_TRECHO_ROUND
    return a


def concentracao_trecho(
    acidentes: pd.DataFrame, min_acidentes: int = 1, top: int | None = None
) -> pd.DataFrame:
    """Acidentes por trecho `(uf, br, km_trecho)`, ordenado desc.

    A chave inclui `uf` porque `(br, km)` não é única entre estados — a mesma BR
    cruza o país inteiro e o mesmo km se repete em UFs diferentes (devolutiva
    Fase 3.5 → G6, ver `src/eda/hipoteses/pontos_negros.py`).
    `min_acidentes` filtra trechos com poucos casos; `top` limita a saída.
    Cada linha é um candidato a "ponto negro" para a Fase 3.
    """
    a = com_trecho(acidentes)
    g = (
        a.groupby(["uf", "br", "km_trecho"])
        .size()
        .rename("acidentes")
        .reset_index()
        .query("acidentes >= @min_acidentes")
        .sort_values("acidentes", ascending=False)
        .reset_index(drop=True)
    )
    return g.head(top) if top else g


# --------------------------------------------------------------------------
# Recorte operacional PRF
# --------------------------------------------------------------------------
def cobertura_operacional(acidentes: pd.DataFrame) -> dict:
    """Cardinalidade e concentração de `regional`/`delegacia`/`uop`.

    `regional` (29) não bate 1:1 com `uf` (27): UOPs de divisa registram
    ocorrências do estado vizinho. Recorte útil para a PRF, mas redundante com
    UF/BR para o público geral do dashboard — decisão registrada em achados-eda.
    """
    out = {}
    for col in ["regional", "delegacia", "uop"]:
        vc = acidentes[col].value_counts()
        out[col] = {
            "n_distintos": int(acidentes[col].nunique()),
            "top": vc.head(5).to_dict(),
            "share_top10_pct": round(100 * vc.head(10).sum() / len(acidentes), 1),
        }
    return out


# --------------------------------------------------------------------------
# Figuras
# --------------------------------------------------------------------------
def _salvar(fig: plt.Figure, nome: str, dest: Path) -> Path:
    dest.mkdir(parents=True, exist_ok=True)
    caminho = dest / nome
    fig.savefig(caminho, dpi=120, bbox_inches="tight")
    plt.close(fig)
    return caminho


def _barh(serie: pd.Series, titulo: str, dest: Path, nome: str) -> Path:
    fig, ax = plt.subplots(figsize=(9, max(3, 0.32 * len(serie))))
    ax.barh([str(i) for i in serie.index[::-1]], serie.values[::-1], color="#4C72B0")
    ax.set_title(titulo)
    ax.set_xlabel("acidentes")
    return _salvar(fig, nome, dest)


def gerar_figuras(acidentes: pd.DataFrame, dest: Path = DEST) -> list[Path]:
    figuras = [
        _barh(ranking_uf(acidentes), "Acidentes por UF (volume, não risco)", dest, "ranking_uf.png"),
        _barh(ranking_br(acidentes, top=TOP_N), f"Acidentes por BR — top {TOP_N}", dest, "ranking_br.png"),
        _barh(ranking_municipio(acidentes), f"Acidentes por município — top {TOP_N}", dest, "ranking_municipio.png"),
    ]

    tr = concentracao_trecho(acidentes, top=TOP_N)
    rotulos = tr["uf"] + " " + tr["br"].astype(str) + " km " + tr["km_trecho"].astype(str)
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.barh(rotulos[::-1], tr["acidentes"][::-1], color="#C44E52")
    ax.set_title(f"Trechos (uf, br, km) com mais acidentes — top {TOP_N}")
    ax.set_xlabel("acidentes")
    figuras.append(_salvar(fig, "concentracao_trecho.png", dest))

    fig, ax = plt.subplots(figsize=(7, 7))
    hb = ax.hexbin(
        acidentes["longitude"], acidentes["latitude"],
        gridsize=60, cmap="inferno", bins="log", mincnt=1,
    )
    ax.set_xlim(*BRAZIL_LON_RANGE)
    ax.set_ylim(*BRAZIL_LAT_RANGE)
    ax.set_aspect("equal")
    ax.set_title("Densidade espacial dos acidentes (escala log)")
    ax.set_xlabel("longitude")
    ax.set_ylabel("latitude")
    fig.colorbar(hb, ax=ax, label="acidentes (log)")
    figuras.append(_salvar(fig, "densidade_espacial.png", dest))

    return figuras


# --------------------------------------------------------------------------
def resumo(acidentes: pd.DataFrame | None = None) -> dict:
    if acidentes is None:
        acidentes = por_acidente(load_enriched())

    uf = ranking_uf(acidentes)
    br = ranking_br(acidentes)
    mun = ranking_municipio(acidentes, top=None)
    tr = concentracao_trecho(acidentes)

    return {
        "n_acidentes": len(acidentes),
        "sem_georreferenciamento": int(acidentes["latitude"].isna().sum()),
        "sem_br_identificada": int(acidentes["br"].isna().sum()),
        "uf_top3": uf.head(3).to_dict(),
        "uf_share_top5_pct": round(100 * uf.head(5).sum() / len(acidentes), 1),
        "br_top3": br.head(3).to_dict(),
        "br_share_top2_pct": round(100 * br.head(2).sum() / len(acidentes), 1),
        "municipio_top3": mun.head(3).to_dict(),
        "municipio_share_top10_pct": round(100 * mun.head(10).sum() / len(acidentes), 1),
        "n_trechos": len(tr),
        "trechos_ge_10": int((tr["acidentes"] >= 10).sum()),
        "trechos_ge_20": int((tr["acidentes"] >= 20).sum()),
        "trecho_top": tr.iloc[0].to_dict(),
        "operacional": cobertura_operacional(acidentes),
    }


def main() -> None:
    acidentes = por_acidente(load_enriched())
    for k, v in resumo(acidentes).items():
        if k != "operacional":
            print(f"{k}: {v}")
    print("\noperacional:")
    for col, info in resumo(acidentes)["operacional"].items():
        print(f"  {col}: {info['n_distintos']} distintos, top10 = {info['share_top10_pct']}%")
    figs = gerar_figuras(acidentes)
    print("\nfiguras:")
    for f in figs:
        print(f"  {f}")


if __name__ == "__main__":
    main()
