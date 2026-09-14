"""Fase 2.1 — dimensão temporal (unidade: acidente).

Distribuição dos 72.529 acidentes de 2025 por mês, dia da semana e hora cheia,
matriz dia×hora, e `fase_dia` normalizada pela exposição (nº de horas que cada
fase representa) — sem essa normalização a conclusão "mais acidentes de dia" é
só reflexo de o dia ter mais horas.

Todas as funções recebem o recorte `por_acidente(load_enriched())` — um registro
por `id`. `gerar_figuras()` salva os PNGs; `resumo()` devolve os números para o
`achados-eda.md`.

Uso: ``python -m src.eda.dimensoes.temporal``
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

from src.const import DIAS_NO_PERIODO, DIAS_SEMANA_ORDEM, FIGURES_PATH  # noqa: E402
from src.eda.dataset import load_enriched, por_acidente  # noqa: E402

DEST = FIGURES_PATH / "temporal"

MESES_PT = [
    "jan", "fev", "mar", "abr", "mai", "jun",
    "jul", "ago", "set", "out", "nov", "dez",
]


# --------------------------------------------------------------------------
# Agregações
# --------------------------------------------------------------------------
def acidentes_por_mes(acidentes: pd.DataFrame) -> pd.Series:
    """Contagem por mês (1–12), reindexada para cobrir o ano todo."""
    s = acidentes["mes"].value_counts().reindex(range(1, 13), fill_value=0)
    s.index = MESES_PT
    return s.rename("acidentes")


def acidentes_por_dia_semana(acidentes: pd.DataFrame) -> pd.Series:
    """Contagem por dia da semana, na ordem segunda→domingo."""
    return (
        acidentes["dia_semana_ord"]
        .value_counts()
        .reindex(DIAS_SEMANA_ORDEM, fill_value=0)
        .rename("acidentes")
    )


def acidentes_por_hora(acidentes: pd.DataFrame) -> pd.Series:
    """Contagem por hora cheia (0–23)."""
    return (
        acidentes["hora"]
        .value_counts()
        .reindex(range(24), fill_value=0)
        .rename("acidentes")
    )


def matriz_dia_hora(acidentes: pd.DataFrame) -> pd.DataFrame:
    """Matriz dia da semana (linhas, seg→dom) × hora (colunas, 0–23)."""
    m = pd.crosstab(acidentes["dia_semana_ord"], acidentes["hora"])
    return m.reindex(index=DIAS_SEMANA_ORDEM, columns=range(24), fill_value=0)


def exposicao_horas_por_fase_dia(acidentes: pd.DataFrame) -> pd.Series:
    """Estima quantas horas do dia cada `fase_dia` representa, em média no ano.

    `fase_dia` é atribuída por data/hora real (nascer/pôr do sol variam com a
    estação), então a duração de cada fase não é fixa. Estimativa: para cada
    hora cheia, P(fase | hora) observada; somando sobre as 24 horas obtém-se o
    nº médio de horas/dia de cada fase. Some ≈ 24.
    """
    p = pd.crosstab(acidentes["hora"], acidentes["fase_dia"], normalize="index")
    return p.sum(axis=0).rename("horas_por_dia")


def fase_dia_normalizada(acidentes: pd.DataFrame) -> pd.DataFrame:
    """Acidentes por fase do dia, absolutos e normalizados pela exposição.

    `taxa` = acidentes por hora de exposição da fase. `indice` = taxa da fase ÷
    taxa média (todas as fases) — > 1 significa risco acima da média para o
    tempo que se passa naquela fase.
    """
    n = acidentes["fase_dia"].value_counts()
    horas_dia = exposicao_horas_por_fase_dia(acidentes)
    horas_periodo = horas_dia * DIAS_NO_PERIODO

    out = pd.DataFrame({"n_acidentes": n, "horas_dia": horas_dia})
    out["horas_exposicao"] = horas_periodo
    out["taxa_por_hora"] = out["n_acidentes"] / out["horas_exposicao"]
    out["indice_vs_media"] = out["taxa_por_hora"] / (
        out["n_acidentes"].sum() / out["horas_exposicao"].sum()
    )
    return out.sort_values("indice_vs_media", ascending=False)


# --------------------------------------------------------------------------
# Figuras
# --------------------------------------------------------------------------
def _salvar(fig: plt.Figure, nome: str, dest: Path) -> Path:
    dest.mkdir(parents=True, exist_ok=True)
    caminho = dest / nome
    fig.savefig(caminho, dpi=120, bbox_inches="tight")
    plt.close(fig)
    return caminho


def gerar_figuras(acidentes: pd.DataFrame, dest: Path = DEST) -> list[Path]:
    figuras = []

    s = acidentes_por_mes(acidentes)
    fig, ax = plt.subplots(figsize=(9, 4))
    ax.bar(s.index, s.values, color="#4C72B0")
    ax.set_title("Acidentes por mês — 2025 (unidade: acidente)")
    ax.set_ylabel("acidentes")
    ax.margins(y=0.15)
    figuras.append(_salvar(fig, "acidentes_por_mes.png", dest))

    s = acidentes_por_dia_semana(acidentes)
    fig, ax = plt.subplots(figsize=(9, 4))
    ax.bar([d.split("-")[0] for d in s.index], s.values, color="#4C72B0")
    ax.set_title("Acidentes por dia da semana (unidade: acidente)")
    ax.set_ylabel("acidentes")
    figuras.append(_salvar(fig, "acidentes_por_dia_semana.png", dest))

    s = acidentes_por_hora(acidentes)
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.bar(s.index, s.values, color="#4C72B0")
    ax.set_title("Acidentes por hora do dia (unidade: acidente)")
    ax.set_xlabel("hora")
    ax.set_ylabel("acidentes")
    ax.set_xticks(range(0, 24, 2))
    figuras.append(_salvar(fig, "acidentes_por_hora.png", dest))

    m = matriz_dia_hora(acidentes)
    fig, ax = plt.subplots(figsize=(12, 4.5))
    im = ax.imshow(m.values, aspect="auto", cmap="magma")
    ax.set_yticks(range(len(m.index)), [d.split("-")[0] for d in m.index])
    ax.set_xticks(range(0, 24, 2), range(0, 24, 2))
    ax.set_xlabel("hora")
    ax.set_title("Acidentes por dia da semana × hora (unidade: acidente)")
    fig.colorbar(im, ax=ax, label="acidentes")
    figuras.append(_salvar(fig, "matriz_dia_hora.png", dest))

    fd = fase_dia_normalizada(acidentes)
    fig, axes = plt.subplots(1, 2, figsize=(12, 4))
    axes[0].bar(fd.index, fd["n_acidentes"], color="#C44E52")
    axes[0].set_title("Acidentes por fase do dia — contagem absoluta")
    axes[0].set_ylabel("acidentes")
    axes[1].bar(fd.index, fd["indice_vs_media"], color="#55A868")
    axes[1].axhline(1.0, color="gray", ls="--", lw=1)
    axes[1].set_title("Índice de risco por hora de exposição (1 = média)")
    figuras.append(_salvar(fig, "fase_dia_exposicao.png", dest))

    return figuras


# --------------------------------------------------------------------------
def resumo(acidentes: pd.DataFrame | None = None) -> dict:
    """Números-chave da dimensão temporal, para o achados-eda.md."""
    if acidentes is None:
        acidentes = por_acidente(load_enriched())

    mes = acidentes_por_mes(acidentes)
    dsem = acidentes_por_dia_semana(acidentes)
    hora = acidentes_por_hora(acidentes)
    fd = fase_dia_normalizada(acidentes)

    return {
        "n_acidentes": len(acidentes),
        "mes_pico": (mes.idxmax(), int(mes.max())),
        "mes_vale": (mes.idxmin(), int(mes.min())),
        "amplitude_mensal_pct": round(100 * (mes.max() / mes.min() - 1), 1),
        "dia_semana_pico": (dsem.idxmax(), int(dsem.max())),
        "dia_semana_vale": (dsem.idxmin(), int(dsem.min())),
        "hora_pico": (int(hora.idxmax()), int(hora.max())),
        "hora_vale": (int(hora.idxmin()), int(hora.min())),
        "fase_dia_maior_indice": (fd.index[0], round(float(fd["indice_vs_media"].iloc[0]), 2)),
        "fase_dia_menor_indice": (fd.index[-1], round(float(fd["indice_vs_media"].iloc[-1]), 2)),
        "fase_dia_tabela": fd.round(3).to_dict("index"),
    }


def main() -> None:
    acidentes = por_acidente(load_enriched())
    info = resumo(acidentes)
    for k, v in info.items():
        if k != "fase_dia_tabela":
            print(f"{k}: {v}")
    print("\nfase_dia (normalizada pela exposição):")
    print(fase_dia_normalizada(acidentes).round(3))
    figs = gerar_figuras(acidentes)
    print("\nfiguras:")
    for f in figs:
        print(f"  {f}")


if __name__ == "__main__":
    main()
