"""Ponto de entrada de dados da EDA (Fase 2).

`load_enriched()` devolve o DataFrame da Fase 1 (em memória, via `run_pipeline`,
ou lido do parquet) já com as derivações da Fase 2.0 aplicadas.

`por_acidente` / `por_veiculo` / `por_pessoa` são os três recortes por unidade de
análise (plan.md "Premissa metodológica"). Toda estatística da Fase 2 passa por
uma dessas três funções — nunca por `len(df)` direto.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.const import (
    DENOMINADOR_ACIDENTES,
    DENOMINADOR_PESSOAS,
    DENOMINADOR_VEICULOS,
    PROCESSED_DATA_PATH,
)
from src.eda.enrich import enriquecer
from src.etl.pipeline import run_pipeline


def load_enriched(
    *, from_parquet: bool = False, path: Path = PROCESSED_DATA_PATH
) -> pd.DataFrame:
    """DataFrame tratado (Fase 1) + enriquecido (Fase 2.0).

    Por padrão roda `run_pipeline(persist_output=False)` em memória, sem depender
    do parquet. `from_parquet=True` lê o arquivo já persistido (mais rápido em
    iterações de notebook).
    """
    if from_parquet:
        df = pd.read_parquet(path)
    else:
        df, _ = run_pipeline(persist_output=False)
    return enriquecer(df)


def por_acidente(df: pd.DataFrame) -> pd.DataFrame:
    """Um registro por acidente (`id`). Unidade das dimensões temporal, geográfica,
    causa/tipo e via/ambiente."""
    return df.drop_duplicates("id").reset_index(drop=True)


def por_veiculo(df: pd.DataFrame) -> pd.DataFrame:
    """Um registro por veículo (`id`, `id_veiculo`). Pessoas sem veículo
    (`id_veiculo` nulo: pedestre/testemunha/cavaleiro) não entram."""
    return (
        df.dropna(subset=["id_veiculo"])
        .drop_duplicates(["id", "id_veiculo"])
        .reset_index(drop=True)
    )


def por_pessoa(df: pd.DataFrame) -> pd.DataFrame:
    """Um registro por pessoa (linha bruta). Unidade das dimensões vítima e
    condutor."""
    return df.reset_index(drop=True)


# Papéis que podem ser vítima. `Testemunha` e `tipo_envolvido` nulo entram no
# acidente mas nunca têm desfecho de severidade — incluí-los no denominador de
# qualquer taxa de letalidade/gravidade a subestima (achado 2.6/Vi5).
PAPEIS_VITIMA = ["Condutor", "Passageiro", "Pedestre", "Cavaleiro"]


SEVERITY_FLAGS = ["ilesos", "feridos_leves", "feridos_graves", "mortos"]


def apenas_vitimas(pessoas: pd.DataFrame, com_desfecho: bool = False) -> pd.DataFrame:
    """Filtra `por_pessoa` para os papéis que podem ser vítima (`PAPEIS_VITIMA`).

    Use como base de toda taxa de severidade por pessoa. Remove ~20k linhas
    (testemunhas + `tipo_envolvido` nulo), todas sem desfecho registrado.

    `com_desfecho=True` também exclui as ~8,5k vítimas sem nenhuma flag de
    severidade (`estado_fisico` nulo) — registro incompleto que deprime a
    letalidade em ~5% relativo (achado 2.8/Cn3). É a base recomendada para
    modelagem na Fase 3; o padrão `False` preserva o comportamento da Fase 2.
    """
    vit = pessoas[pessoas["tipo_envolvido"].isin(PAPEIS_VITIMA)]
    if com_desfecho:
        vit = vit[vit[SEVERITY_FLAGS].sum(axis=1) > 0]
    return vit.reset_index(drop=True)


def apenas_condutores(pessoas: pd.DataFrame) -> pd.DataFrame:
    """Filtra `por_pessoa` para `tipo_envolvido == "Condutor"` (unidade da 2.7).

    Verificado (CLAUDE.md): há no máximo um "Condutor" por `(id, id_veiculo)`,
    então cada linha é um condutor único por veículo/acidente.
    """
    return pessoas[pessoas["tipo_envolvido"] == "Condutor"].reset_index(drop=True)


DENOMINADORES = {
    "por_acidente": DENOMINADOR_ACIDENTES,
    "por_veiculo": DENOMINADOR_VEICULOS,
    "por_pessoa": DENOMINADOR_PESSOAS,
}


def checar_denominadores(df: pd.DataFrame) -> dict[str, int]:
    """Confere que os três recortes batem com os denominadores de const.py.

    Levanta AssertionError com o diff se algum divergir — trava cedo se o ETL
    mudar de forma inesperada.
    """
    obtidos = {
        "por_acidente": len(por_acidente(df)),
        "por_veiculo": len(por_veiculo(df)),
        "por_pessoa": len(por_pessoa(df)),
    }
    divergentes = {
        k: (obtidos[k], DENOMINADORES[k])
        for k in obtidos
        if obtidos[k] != DENOMINADORES[k]
    }
    assert not divergentes, f"denominadores divergentes (obtido, esperado): {divergentes}"
    return obtidos
