"""Módulo de EDA da Fase 2 (docs/specs/analise-exploratoria/plan.md §2).

Submódulos: `enrich` (derivações), `dataset` (entrada + recortes por unidade),
`severity` (métricas de severidade reutilizáveis).
"""

from src.eda import dataset, enrich, severity
from src.eda.dataset import (
    apenas_condutores,
    apenas_vitimas,
    checar_denominadores,
    load_enriched,
    por_acidente,
    por_pessoa,
    por_veiculo,
)
from src.eda.enrich import enriquecer
from src.eda.severity import (
    mortos_por_acidente,
    resumo_severidade,
    taxa_ferido_grave_por_pessoa,
    taxa_letalidade_por_pessoa,
)

__all__ = [
    "dataset",
    "enrich",
    "severity",
    "load_enriched",
    "enriquecer",
    "por_acidente",
    "por_veiculo",
    "por_pessoa",
    "apenas_vitimas",
    "apenas_condutores",
    "checar_denominadores",
    "taxa_letalidade_por_pessoa",
    "taxa_ferido_grave_por_pessoa",
    "mortos_por_acidente",
    "resumo_severidade",
]
