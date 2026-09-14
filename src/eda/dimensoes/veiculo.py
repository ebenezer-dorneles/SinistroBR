"""Fase 2.5 — dimensão veículo (unidade: veículo, n = 139.517).

Distribuição de `tipo_veiculo`, ranking de `marca_normalizada` (refinada nesta
fase: prefixos I/SR/REB/R e sinônimos), idade da frota acidentada
(`ANO_REFERENCIA − ano_fabricacao_veiculo`), e a checagem de consistência dos
atributos de veículo dentro de um mesmo `(id, id_veiculo)` — pré-requisito para
confiar na deduplicação `por_veiculo`.

A severidade por tipo de veículo é medida no nível **pessoa** (quem morre é a
pessoa, não o veículo), filtrando as linhas ligadas a um veículo.

Uso: ``python -m src.eda.dimensoes.veiculo``
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

from src.const import ANO_REFERENCIA, FIGURES_PATH, TOP_N  # noqa: E402
from src.eda.dataset import load_enriched, por_pessoa, por_veiculo  # noqa: E402

DEST = FIGURES_PATH / "veiculo"

ATRIBUTOS_VEICULO = ["tipo_veiculo", "marca", "marca_normalizada", "ano_fabricacao_veiculo"]


# --------------------------------------------------------------------------
def constancia_por_veiculo(pessoas: pd.DataFrame) -> pd.Series:
    """Nº de veículos `(id, id_veiculo)` com valor divergente em cada atributo.

    Se algum for > 0, a deduplicação `por_veiculo` precisa de regra de desempate
    antes de qualquer estatística de frota. (Verificado: todos 0.)
    """
    g = pessoas.dropna(subset=["id_veiculo"]).groupby(["id", "id_veiculo"])
    return pd.Series(
        {col: int((g[col].nunique(dropna=False) > 1).sum()) for col in ATRIBUTOS_VEICULO}
    )


def distribuicao_tipo(veiculos: pd.DataFrame) -> pd.Series:
    return veiculos["tipo_veiculo"].value_counts(dropna=False).rename("veiculos")


def ranking_marca(veiculos: pd.DataFrame, top: int | None = TOP_N) -> pd.Series:
    s = veiculos["marca_normalizada"].value_counts().rename("veiculos")
    return s.head(top) if top else s


def idade_frota(veiculos: pd.DataFrame) -> dict:
    """Descritivas da idade da frota acidentada + cobertura do campo."""
    ano = veiculos["ano_fabricacao_veiculo"]
    idade = (ANO_REFERENCIA - ano).dropna()
    idade = idade[idade >= 0]
    return {
        "cobertura_pct": round(100 * ano.notna().mean(), 1),
        "sem_ano": int(ano.isna().sum()),
        "idade_mediana": float(idade.median()),
        "idade_media": round(float(idade.mean()), 1),
        "idade_p90": float(idade.quantile(0.9)),
        "pct_ate_5_anos": round(100 * (idade <= 5).mean(), 1),
        "pct_mais_15_anos": round(100 * (idade > 15).mean(), 1),
        "serie_idade": idade,
    }


def severidade_por_tipo(pessoas: pd.DataFrame, top: int | None = TOP_N) -> pd.DataFrame:
    """Letalidade e participação nos óbitos por `tipo_veiculo` (nível pessoa)."""
    p = pessoas.dropna(subset=["id_veiculo"])
    g = p.groupby("tipo_veiculo", observed=True)
    out = pd.DataFrame(
        {
            "n_veiculos": g["id_veiculo"].nunique(),
            "n_pessoas": g.size(),
            "mortos": g["mortos"].sum().astype(int),
        }
    )
    out["taxa_letalidade"] = out["mortos"] / out["n_pessoas"]
    out["share_mortos_pct"] = (100 * out["mortos"] / out["mortos"].sum()).round(1)
    out = out.sort_values("mortos", ascending=False)
    return out.head(top) if top else out


# --------------------------------------------------------------------------
def _salvar(fig: plt.Figure, nome: str, dest: Path) -> Path:
    dest.mkdir(parents=True, exist_ok=True)
    caminho = dest / nome
    fig.savefig(caminho, dpi=120, bbox_inches="tight")
    plt.close(fig)
    return caminho


def gerar_figuras(veiculos: pd.DataFrame, pessoas: pd.DataFrame, dest: Path = DEST) -> list[Path]:
    figuras = []

    tipo = distribuicao_tipo(veiculos).head(TOP_N)
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.barh(tipo.index[::-1], tipo.values[::-1], color="#4C72B0")
    ax.set_title(f"Veículos acidentados por tipo — top {TOP_N} (unidade: veículo)")
    ax.set_xlabel("veículos")
    figuras.append(_salvar(fig, "distribuicao_tipo.png", dest))

    marca = ranking_marca(veiculos)
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.barh(marca.index[::-1], marca.values[::-1], color="#4C72B0")
    ax.set_title(f"Marcas mais frequentes — top {TOP_N}")
    ax.set_xlabel("veículos")
    figuras.append(_salvar(fig, "ranking_marca.png", dest))

    info = idade_frota(veiculos)
    fig, ax = plt.subplots(figsize=(9, 4))
    ax.hist(info["serie_idade"], bins=range(0, 41), color="#4C72B0")
    ax.axvline(info["idade_mediana"], color="#C44E52", ls="--", label=f"mediana {info['idade_mediana']:.0f}")
    ax.set_title(f"Idade da frota acidentada (cobertura {info['cobertura_pct']}%)")
    ax.set_xlabel("anos")
    ax.set_ylabel("veículos")
    ax.legend()
    figuras.append(_salvar(fig, "idade_frota.png", dest))

    sev = severidade_por_tipo(pessoas)
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.scatter(sev["n_pessoas"], sev["taxa_letalidade"], s=sev["share_mortos_pct"] * 12,
               color="#C44E52", alpha=0.7)
    for nome, row in sev.iterrows():
        ax.annotate(str(nome), (row["n_pessoas"], row["taxa_letalidade"]),
                    fontsize=7, xytext=(4, 2), textcoords="offset points")
    ax.set_xlabel("pessoas envolvidas")
    ax.set_ylabel("letalidade (mortos por pessoa)")
    ax.set_title("Tipo de veículo: exposição × letalidade (área ∝ % dos óbitos)")
    figuras.append(_salvar(fig, "severidade_por_tipo.png", dest))

    return figuras


# --------------------------------------------------------------------------
def resumo(df: pd.DataFrame | None = None) -> dict:
    if df is None:
        df = load_enriched()
    veiculos = por_veiculo(df)
    pessoas = por_pessoa(df)

    tipo = distribuicao_tipo(veiculos)
    marca = ranking_marca(veiculos, top=None)
    idade = idade_frota(veiculos)
    sev = severidade_por_tipo(pessoas, top=None)

    pesados = ["Semireboque", "Caminhão-trator", "Caminhão", "Reboque"]
    return {
        "n_veiculos": len(veiculos),
        "constancia_divergencias": constancia_por_veiculo(pessoas).to_dict(),
        "tipo_top3": tipo.head(3).to_dict(),
        "moto_pct": round(100 * tipo.get("Motocicleta", 0) / len(veiculos), 1),
        "carga_pesada_pct": round(100 * tipo.reindex(pesados).sum() / len(veiculos), 1),
        "marca_top5": marca.head(5).to_dict(),
        "marca_distintas": int(veiculos["marca_normalizada"].nunique()),
        "marca_sem": int(veiculos["marca_normalizada"].isna().sum()),
        "idade_frota": {k: v for k, v in idade.items() if k != "serie_idade"},
        "moto_letalidade": round(float(sev.loc["Motocicleta", "taxa_letalidade"]), 4),
        "auto_letalidade": round(float(sev.loc["Automóvel", "taxa_letalidade"]), 4),
        "moto_share_mortos_pct": float(sev.loc["Motocicleta", "share_mortos_pct"]),
        "bicicleta_letalidade": round(float(sev.loc["Bicicleta", "taxa_letalidade"]), 4),
    }


def main() -> None:
    df = load_enriched()
    veiculos, pessoas = por_veiculo(df), por_pessoa(df)

    for k, v in resumo(df).items():
        print(f"{k}: {v}")

    print("\nconstância dos atributos dentro de (id, id_veiculo):")
    print(constancia_por_veiculo(pessoas).to_string())

    print("\nseveridade por tipo_veiculo (nível pessoa):")
    print(severidade_por_tipo(pessoas, top=None).round(4).to_string())

    figs = gerar_figuras(veiculos, pessoas)
    print("\nfiguras:")
    for f in figs:
        print(f"  {f}")


if __name__ == "__main__":
    main()
