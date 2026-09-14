"""Testes da Fase 2.2 — dimensão geográfica (src/eda/dimensoes/geografico.py)."""

import pandas as pd
import pytest

from src.eda.dataset import load_enriched, por_acidente
from src.eda.dimensoes import geografico


@pytest.fixture(scope="module")
def acidentes():
    return por_acidente(load_enriched())


def test_ranking_uf_completo_e_soma(acidentes):
    s = geografico.ranking_uf(acidentes)
    assert len(s) == 27
    assert s.sum() == len(acidentes)
    assert s.index[0] == "MG"


def test_ranking_br_ignora_br_nula(acidentes):
    s = geografico.ranking_br(acidentes)
    assert s.sum() == acidentes["br"].notna().sum()
    assert 101 in s.index and s.index[0] == 101


def test_ranking_municipio_top_n(acidentes):
    s = geografico.ranking_municipio(acidentes, top=15)
    assert len(s) == 15
    assert s.is_monotonic_decreasing


def test_com_trecho_descarta_sem_br(acidentes):
    a = geografico.com_trecho(acidentes)
    assert a["br"].notna().all()
    assert a["km"].notna().all()
    assert (a["km_trecho"] % 1 == 0).all()


def test_concentracao_trecho_ordenada_e_filtrada(acidentes):
    tr = geografico.concentracao_trecho(acidentes, min_acidentes=20)
    assert (tr["acidentes"] >= 20).all()
    assert tr["acidentes"].is_monotonic_decreasing
    assert len(tr) == 382  # chave (uf, br, km) — devolutiva Fase 3.5 → G6
    # o trecho de topo é conhecido: SC, BR-101 km 208
    assert tr.iloc[0]["uf"] == "SC"
    assert tr.iloc[0]["br"] == 101


def test_concentracao_trecho_soma_bate_com_acidentes_localizados(acidentes):
    tr = geografico.concentracao_trecho(acidentes)
    assert tr["acidentes"].sum() == acidentes["br"].notna().sum()


def test_cobertura_operacional_cardinalidades(acidentes):
    op = geografico.cobertura_operacional(acidentes)
    assert op["regional"]["n_distintos"] == 29
    assert op["uop"]["n_distintos"] == 396
    # regional é mais concentrado que uop
    assert op["regional"]["share_top10_pct"] > op["uop"]["share_top10_pct"]


def test_resumo(acidentes):
    r = geografico.resumo(acidentes)
    assert r["sem_georreferenciamento"] == 0
    assert r["sem_br_identificada"] == 167


def test_gerar_figuras(tmp_path, acidentes):
    figs = geografico.gerar_figuras(acidentes, dest=tmp_path)
    assert len(figs) == 5
    assert all(p.exists() and p.stat().st_size > 0 for p in figs)
