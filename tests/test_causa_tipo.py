"""Testes da Fase 2.3 — causa e tipo do acidente (src/eda/dimensoes/causa_tipo.py)."""

import pandas as pd
import pytest

from src.eda.dataset import load_enriched, por_acidente, por_pessoa
from src.eda.dimensoes import causa_tipo as ct


@pytest.fixture(scope="module")
def df():
    return load_enriched()


@pytest.fixture(scope="module")
def acidentes(df):
    return por_acidente(df)


@pytest.fixture(scope="module")
def pessoas(df):
    return por_pessoa(df)


def test_frequencia_tipo_completa(acidentes):
    s = ct.frequencia_tipo(acidentes)
    assert len(s) == 17
    assert s.sum() == len(acidentes)
    assert s.index[0] == "Colisão traseira"


def test_frequencia_causa_macro_5_categorias(acidentes):
    s = ct.frequencia_causa_macro(acidentes)
    assert set(s.index) == {"Falha do condutor", "Via / ambiente", "Veículo", "Pedestre", "Outros"}
    assert s.sum() == len(acidentes)
    assert s.idxmax() == "Falha do condutor"


def test_frequencia_causa_bruta(acidentes):
    s = ct.frequencia_causa(acidentes, top=None)
    assert len(s) == 69
    assert s.sum() == len(acidentes)


def test_distribuicao_classificacao_um_nulo(acidentes):
    s = ct.distribuicao_classificacao(acidentes)
    assert s.get("Com Vítimas Feridas") == 56181
    assert acidentes["classificacao_acidente"].isna().sum() == 1


def test_classificacao_nula_tem_morto(df):
    det = ct.classificacao_nula(df)
    # o único acidente com classificação nula tem uma vítima fatal
    assert det["id"].nunique() == 1
    assert det["mortos"].sum() == 1


def test_letalidade_por_tipo_duas_unidades(pessoas):
    let = ct.letalidade_por(pessoas, "tipo_acidente")
    assert {"n_acidentes", "n_pessoas", "mortos", "mortos_por_acidente", "mortos_por_pessoa"} <= set(let.columns)
    assert let["n_pessoas"].sum() == len(pessoas)
    assert let.index[0] == "Atropelamento de Pedestre"
    # as duas unidades discordam do ranking: colisão frontal mata mais por
    # acidente do que atropelamento, mas menos por pessoa
    assert let.loc["Colisão frontal", "mortos_por_acidente"] > let.loc["Atropelamento de Pedestre", "mortos_por_acidente"]
    assert let.loc["Colisão frontal", "mortos_por_pessoa"] < let.loc["Atropelamento de Pedestre", "mortos_por_pessoa"]


def test_letalidade_por_causa_macro(pessoas):
    let = ct.letalidade_por(pessoas, "causa_macro")
    assert let.loc["Veículo", "mortos_por_pessoa"] < let.loc["Falha do condutor", "mortos_por_pessoa"]


def test_resumo(df):
    r = ct.resumo(df)
    assert r["classificacao_nulos"] == 1
    assert r["tipo_mais_frequente"][0] == "Colisão traseira"
    assert r["tipo_mais_letal"][0] == "Atropelamento de Pedestre"


def test_gerar_figuras(tmp_path, acidentes, pessoas):
    figs = ct.gerar_figuras(acidentes, pessoas, dest=tmp_path)
    assert len(figs) == 5
    assert all(p.exists() and p.stat().st_size > 0 for p in figs)
