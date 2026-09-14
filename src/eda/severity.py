"""Métricas de severidade reutilizáveis (plan.md §2.0, task.md Fase 2.0).

Função única por indicador, para que EDA (Fase 2/3) e dashboard (Fase 5) não
calculem a mesma taxa de dois jeitos.

Cuidado com a unidade (plan.md "Premissa metodológica"): frequência (nº de
acidentes) e severidade (nº de mortos/feridos) vivem em unidades diferentes e
não dividem o mesmo denominador.
- `*_por_pessoa`: entrada no nível **pessoa** (linha bruta). Fração de pessoas
  expostas que morreu / ficou ferida grave.
- `mortos_por_acidente`: total de mortos ÷ nº de acidentes distintos (`id`).
"""

from __future__ import annotations

import pandas as pd

SEVERITY_COLUMNS = ["ilesos", "feridos_leves", "feridos_graves", "mortos"]


def _exige_colunas(df: pd.DataFrame, colunas: list[str]) -> None:
    faltando = [c for c in colunas if c not in df.columns]
    if faltando:
        raise KeyError(f"colunas ausentes para métrica de severidade: {faltando}")


def taxa_letalidade_por_pessoa(df: pd.DataFrame) -> float:
    """`mortos.sum() / n_pessoas`. Entrada no nível pessoa."""
    _exige_colunas(df, ["mortos"])
    return float(df["mortos"].mean()) if len(df) else float("nan")


def taxa_ferido_grave_por_pessoa(df: pd.DataFrame) -> float:
    """`feridos_graves.sum() / n_pessoas`. Entrada no nível pessoa."""
    _exige_colunas(df, ["feridos_graves"])
    return float(df["feridos_graves"].mean()) if len(df) else float("nan")


def mortos_por_acidente(df: pd.DataFrame) -> float:
    """`mortos.sum() / n_acidentes` (`id` distintos). Entrada no nível pessoa."""
    _exige_colunas(df, ["mortos", "id"])
    n_acidentes = df["id"].nunique()
    return float(df["mortos"].sum() / n_acidentes) if n_acidentes else float("nan")


def resumo_severidade(df: pd.DataFrame, por: str | None = None) -> pd.DataFrame:
    """Contagens + taxas de severidade, opcionalmente agrupadas por `por`.

    Entrada no nível pessoa. Colunas de saída: `n_pessoas`, contagem de cada
    indicador, `taxa_letalidade`, `taxa_ferido_grave`. Com `por`, uma linha por
    valor do grupo, ordenada por `taxa_letalidade` desc.
    """
    _exige_colunas(df, SEVERITY_COLUMNS + (["id"] if por is None else []))

    def _linha(g: pd.DataFrame) -> pd.Series:
        return pd.Series(
            {
                "n_pessoas": len(g),
                **{c: int(g[c].sum()) for c in SEVERITY_COLUMNS},
                "taxa_letalidade": taxa_letalidade_por_pessoa(g),
                "taxa_ferido_grave": taxa_ferido_grave_por_pessoa(g),
            }
        )

    if por is None:
        return _linha(df).to_frame().T

    _exige_colunas(df, [por])
    out = (
        df.groupby(por, observed=True, dropna=False)
        .apply(_linha, include_groups=False)
        .sort_values("taxa_letalidade", ascending=False)
    )
    return out
