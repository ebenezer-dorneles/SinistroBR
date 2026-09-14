"""Testes da Fase 2.4 — condições da via e ambiente (src/eda/dimensoes/via_ambiente.py)."""

import pytest

from src.eda.dataset import load_enriched, por_acidente, por_pessoa
from src.eda.dimensoes import via_ambiente as va


@pytest.fixture(scope="module")
def df():
    return load_enriched()


@pytest.fixture(scope="module")
def acidentes(df):
    return por_acidente(df)


@pytest.fixture(scope="module")
def pessoas(df):
    return por_pessoa(df)


def test_distribuicao_inclui_nulos(acidentes):
    s = va.distribuicao(acidentes, "condicao_metereologica")
    assert s.sum() == len(acidentes)
    assert s.isna().sum() == 0  # nulos entram como categoria NaN, não somem


def test_gravidade_por_condicao_tem_taxa_e_contagem(pessoas):
    g = va.gravidade_por_condicao(pessoas, "tipo_pista")
    assert {"n_acidentes", "taxa_letalidade", "taxa_ferido_grave"} <= set(g.columns)
    assert g["n_pessoas"].sum() == len(pessoas)


def test_pista_simples_e_mais_letal_que_dupla(pessoas):
    g = va.gravidade_por_condicao(pessoas, "tipo_pista")
    assert g.loc["Simples", "taxa_letalidade"] > g.loc["Dupla", "taxa_letalidade"]
    assert g.loc["Simples", "taxa_letalidade"] > g.loc["Múltipla", "taxa_letalidade"]


def test_chuva_nao_e_mais_letal_que_ceu_claro(pessoas):
    """A 'maioria em céu claro' é exposição: normalizando, chuva não agrava."""
    g = va.gravidade_por_condicao(pessoas, "condicao_metereologica")
    assert g.loc["Chuva", "taxa_letalidade"] <= g.loc["Céu Claro", "taxa_letalidade"]


def test_rural_mais_letal_que_urbano(pessoas):
    g = va.gravidade_por_condicao(pessoas, "uso_solo")
    assert g.loc["Não", "taxa_letalidade"] > g.loc["Sim", "taxa_letalidade"]


def test_tracado_frequencia_reta_domina(acidentes):
    freq = va.tracado_frequencia(acidentes)
    assert freq.index[0] == "tem_reta"
    assert freq["tem_reta"] > len(acidentes) / 2


def test_tracado_gravidade_declive_agrava_rotatoria_alivia(pessoas):
    tg = va.tracado_gravidade(pessoas)
    assert tg.loc["declive", "delta"] > 0
    assert tg.loc["rotatoria", "delta"] < 0
    assert tg.index[0] in {"declive", "curva"}  # o pior é geometria vertical/horizontal


def test_resumo(df):
    r = va.resumo(df)
    assert r["sentido_via_nulos"] == 167
    assert r["sentido_via_nulos_sao_br_nula"] is True
    assert r["chuva_vs_ceu_claro"][0] <= r["chuva_vs_ceu_claro"][1]


def test_gerar_figuras(tmp_path, acidentes, pessoas):
    figs = va.gerar_figuras(acidentes, pessoas, dest=tmp_path)
    assert len(figs) == 5
    assert all(p.exists() and p.stat().st_size > 0 for p in figs)
