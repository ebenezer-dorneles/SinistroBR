"""Testes da Fase 2.8 — consistências e devolutiva (src/eda/dimensoes/consistencia.py)."""

import pytest

from src.eda.dataset import apenas_vitimas, load_enriched, por_pessoa
from src.eda.dimensoes import consistencia as cs


@pytest.fixture(scope="module")
def df():
    return load_enriched()


def test_classificacao_acidente_sem_divergencia(df):
    r = cs.classificacao_vs_flags(df)
    assert r["fatal_sem_morto"] == 0
    assert r["feridas_com_morto"] == 0
    assert r["feridas_sem_vitima"] == 0
    assert r["sem_vitima_com_vitima"] == 0
    assert r["classificacao_nula"] == 1


def test_estado_fisico_redundante_com_flags(df):
    r = cs.estado_fisico_vs_flags(df)
    assert r["identicos"] is True
    assert r["estado_fisico_nulo"] == 28630
    assert r["mapeamento_estado_fisico"]["Óbito"] == "mortos"
    assert r["mapeamento_estado_fisico"]["Ileso"] == "ilesos"


def test_revalidacao_idade_zero_confirma_decisao(df):
    r = cs.revalidar_idade_zero(df)
    assert r["sem_desfecho_pct"] > 80
    assert r["com_desfecho_condutores"] > 1000  # condutores não têm idade real 0
    assert "confirmada" in r["veredito"]


def test_vitimas_sem_desfecho_residuo(df):
    r = cs.vitimas_sem_desfecho(df)
    assert r["sem_desfecho"] == 8487
    assert r["sem_desfecho_pct"] < 6
    # excluir os sem-desfecho eleva a letalidade
    assert r["letalidade_com_desfecho"] > r["letalidade_base_atual"]


def test_apenas_vitimas_com_desfecho(df):
    p = por_pessoa(df)
    base = apenas_vitimas(p)
    cd = apenas_vitimas(p, com_desfecho=True)
    assert len(cd) == len(base) - 8487
    assert (cd[["ilesos", "feridos_leves", "feridos_graves", "mortos"]].sum(axis=1) > 0).all()
