"""Fase 2.6 — vítima / pessoa (unidade: pessoa, n = 194.629).

Perfil demográfico (`idade`, `sexo`, `tipo_envolvido`), distribuição de severidade
e taxa de letalidade por faixa etária, sexo e papel. Toda taxa de severidade usa
`apenas_vitimas()` como base — `Testemunha` e `tipo_envolvido` nulo entram no
acidente mas nunca têm desfecho, e diluem qualquer denominador (achado Vi5).

Uso: ``python -m src.eda.dimensoes.vitima``
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

from src.const import FIGURES_PATH  # noqa: E402
from src.eda.dataset import apenas_vitimas, load_enriched, por_pessoa  # noqa: E402
from src.eda.severity import SEVERITY_COLUMNS, resumo_severidade  # noqa: E402

DEST = FIGURES_PATH / "vitima"


# --------------------------------------------------------------------------
# Perfil demográfico
# --------------------------------------------------------------------------
def perfil_idade(pessoas: pd.DataFrame) -> dict:
    idade = pessoas["idade"].dropna()
    return {
        "cobertura_pct": round(100 * pessoas["idade"].notna().mean(), 1),
        "sem_idade": int(pessoas["idade"].isna().sum()),
        "media": round(float(idade.mean()), 1),
        "mediana": float(idade.median()),
        "p25": float(idade.quantile(0.25)),
        "p75": float(idade.quantile(0.75)),
    }


def distribuicao_sexo(pessoas: pd.DataFrame) -> pd.Series:
    return pessoas["sexo"].value_counts(dropna=False).rename("pessoas")


def distribuicao_tipo_envolvido(pessoas: pd.DataFrame) -> pd.Series:
    return pessoas["tipo_envolvido"].value_counts(dropna=False).rename("pessoas")


def distribuicao_severidade(pessoas: pd.DataFrame) -> pd.Series:
    """Contagem de cada flag de severidade + os registros sem desfecho.

    `estado_fisico` nulo ⟺ nenhuma flag marcada (verificado): são pessoas
    presentes sem desfecho registrado (testemunha, condutor evadido, etc.).
    """
    counts = {c: int(pessoas[c].sum()) for c in SEVERITY_COLUMNS}
    counts["sem_desfecho"] = int((pessoas[SEVERITY_COLUMNS].sum(axis=1) == 0).sum())
    return pd.Series(counts, name="pessoas")


# --------------------------------------------------------------------------
# Letalidade (base: apenas vítimas)
# --------------------------------------------------------------------------
def letalidade_por(vitimas: pd.DataFrame, coluna: str) -> pd.DataFrame:
    """Contagem + taxa de letalidade + taxa de ferido grave por valor de `coluna`."""
    return resumo_severidade(vitimas, por=coluna)


def impacto_testemunha(pessoas: pd.DataFrame) -> dict:
    """Quantifica a diluição do denominador ao incluir não-vítimas."""
    vit = apenas_vitimas(pessoas)
    return {
        "n_todas": len(pessoas),
        "n_vitimas": len(vit),
        "n_removidas": len(pessoas) - len(vit),
        "letalidade_todas": round(float(pessoas["mortos"].mean()), 4),
        "letalidade_vitimas": round(float(vit["mortos"].mean()), 4),
    }


# --------------------------------------------------------------------------
def _salvar(fig: plt.Figure, nome: str, dest: Path) -> Path:
    dest.mkdir(parents=True, exist_ok=True)
    caminho = dest / nome
    fig.savefig(caminho, dpi=120, bbox_inches="tight")
    plt.close(fig)
    return caminho


def _contagem_x_letalidade(g: pd.DataFrame, titulo: str, dest: Path, nome: str) -> Path:
    fig, ax = plt.subplots(figsize=(9, 4.2))
    idx = [str(i) for i in g.index]
    ax.bar(idx, g["n_pessoas"], color="#4C72B0")
    ax.set_ylabel("vítimas", color="#4C72B0")
    ax.tick_params(axis="x", rotation=20)
    ax2 = ax.twinx()
    ax2.plot(idx, g["taxa_letalidade"], color="#C44E52", marker="o", label="letalidade")
    ax2.plot(idx, g["taxa_ferido_grave"], color="#DD8452", marker="s", label="ferido grave")
    ax2.set_ylabel("taxa", color="#C44E52")
    ax2.set_ylim(bottom=0)
    ax2.legend(loc="upper right", fontsize=8)
    ax.set_title(titulo)
    return _salvar(fig, nome, dest)


def gerar_figuras(pessoas: pd.DataFrame, dest: Path = DEST) -> list[Path]:
    vitimas = apenas_vitimas(pessoas)
    figuras = []

    idade = pessoas["idade"].dropna()
    fig, ax = plt.subplots(figsize=(9, 4))
    ax.hist(idade, bins=range(0, 105, 5), color="#4C72B0")
    ax.axvline(idade.median(), color="#C44E52", ls="--", label=f"mediana {idade.median():.0f}")
    ax.set_title(f"Idade das pessoas envolvidas (cobertura {perfil_idade(pessoas)['cobertura_pct']}%)")
    ax.set_xlabel("idade")
    ax.set_ylabel("pessoas")
    ax.legend()
    figuras.append(_salvar(fig, "distribuicao_idade.png", dest))

    sev = distribuicao_severidade(pessoas)
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.bar(sev.index, sev.values, color=["#55A868", "#DD8452", "#C44E52", "#8172B2", "#999999"])
    ax.set_title("Distribuição de severidade (unidade: pessoa)")
    ax.set_ylabel("pessoas")
    figuras.append(_salvar(fig, "distribuicao_severidade.png", dest))

    figuras.append(_contagem_x_letalidade(
        letalidade_por(vitimas, "faixa_etaria"), "Faixa etária: vítimas × letalidade", dest, "letalidade_faixa_etaria.png"))
    figuras.append(_contagem_x_letalidade(
        letalidade_por(vitimas, "tipo_envolvido"), "Papel: vítimas × letalidade", dest, "letalidade_tipo_envolvido.png"))

    g = letalidade_por(vitimas, "sexo")
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.bar([str(i) for i in g.index], g["taxa_letalidade"], color="#C44E52")
    ax.set_title("Letalidade por sexo (base: vítimas)")
    ax.set_ylabel("mortos por pessoa")
    figuras.append(_salvar(fig, "letalidade_sexo.png", dest))

    return figuras


# --------------------------------------------------------------------------
def resumo(df: pd.DataFrame | None = None) -> dict:
    if df is None:
        df = load_enriched()
    pessoas = por_pessoa(df)
    vitimas = apenas_vitimas(pessoas)

    sexo = distribuicao_sexo(pessoas)
    tenv = distribuicao_tipo_envolvido(pessoas)
    sev = distribuicao_severidade(pessoas)
    fe = letalidade_por(vitimas, "faixa_etaria")
    sx = letalidade_por(vitimas, "sexo")
    tp = letalidade_por(vitimas, "tipo_envolvido")

    return {
        "n_pessoas": len(pessoas),
        "perfil_idade": perfil_idade(pessoas),
        "sexo_masc_pct": round(100 * sexo.get("Masculino", 0) / len(pessoas), 1),
        "sexo_nulo": int(sexo.get(pd.NA, 0) if pd.NA in sexo.index else pessoas["sexo"].isna().sum()),
        "tipo_envolvido": tenv.to_dict(),
        "severidade": sev.to_dict(),
        "impacto_testemunha": impacto_testemunha(pessoas),
        "letalidade_60mais": round(float(fe.loc["60+", "taxa_letalidade"]), 4),
        "letalidade_18a24": round(float(fe.loc["18-24", "taxa_letalidade"]), 4),
        "ferido_grave_pico_faixa": (fe["taxa_ferido_grave"].idxmax(), round(float(fe["taxa_ferido_grave"].max()), 4)),
        "letalidade_masc_vs_fem": (
            round(float(sx.loc["Masculino", "taxa_letalidade"]), 4),
            round(float(sx.loc["Feminino", "taxa_letalidade"]), 4),
        ),
        "letalidade_pedestre": round(float(tp.loc["Pedestre", "taxa_letalidade"]), 4),
    }


def main() -> None:
    df = load_enriched()
    pessoas = por_pessoa(df)
    vitimas = apenas_vitimas(pessoas)

    for k, v in resumo(df).items():
        print(f"{k}: {v}")

    for col in ["faixa_etaria", "sexo", "tipo_envolvido"]:
        print(f"\n=== letalidade por {col} (base: vítimas) ===")
        print(letalidade_por(vitimas, col).round(4).to_string())

    figs = gerar_figuras(pessoas)
    print("\nfiguras:")
    for f in figs:
        print(f"  {f}")


if __name__ == "__main__":
    main()
