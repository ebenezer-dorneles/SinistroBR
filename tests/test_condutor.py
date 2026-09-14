"""Testes da Fase 2.7 — condutor (src/eda/dimensoes/condutor.py)."""

import pytest

from src.eda.dataset import apenas_condutores, apenas_vitimas, load_enriched, por_pessoa
from src.eda.dimensoes import condutor as cd


@pytest.fixture(scope="module")
def df():
    return load_enriched()


@pytest.fixture(scope="module")
def vitimas(df):
    return apenas_vitimas(por_pessoa(df))


def test_apenas_condutores(df):
    c = apenas_condutores(por_pessoa(df))
    assert len(c) == 122367
    assert (c["tipo_envolvido"] == "Condutor").all()


def test_perfil_condutor_predominio_masculino(df):
    info = cd.perfil(apenas_condutores(por_pessoa(df)))
    assert info["n"] == 122367
    assert info["masc_pct"] > 85  # bem acima dos 74% do total de vítimas
    assert info["idade_mediana"] >= 38


def test_letalidade_papel_pedestre_muito_acima(vitimas):
    lp = cd.letalidade_papel(vitimas)
    assert list(lp.index) == ["Condutor", "Passageiro", "Pedestre"]
    assert lp.loc["Pedestre", "taxa_letalidade"] > 5 * lp.loc["Condutor", "taxa_letalidade"]
    assert lp.loc["Condutor", "taxa_letalidade"] > lp.loc["Passageiro", "taxa_letalidade"]


def test_condutor_mais_letal_que_passageiro_em_cada_faixa(vitimas):
    piv = cd.letalidade_condutor_vs_passageiro(vitimas, "faixa_etaria")
    reais = piv.drop(index="Não informado", errors="ignore")
    assert (reais["Condutor"] > reais["Passageiro"]).all()


def test_flip_de_sexo_por_papel(vitimas):
    piv = cd.letalidade_condutor_vs_passageiro(vitimas, "sexo")
    # mulher condutora é mais segura que passageira; homem, o oposto
    assert piv.loc["Feminino", "Condutor"] < piv.loc["Feminino", "Passageiro"]
    assert piv.loc["Masculino", "Condutor"] > piv.loc["Masculino", "Passageiro"]


def test_veiculos_sem_condutor_sao_reboques(df):
    info = cd.veiculos_sem_condutor(df)
    assert info["n_veiculos_sem_condutor"] == 17150
    # >95% são semirreboque/reboque, não condutores evadidos
    assert info["reboques_e_semi"] / info["n_veiculos_sem_condutor"] > 0.95
    assert info["motorizados_sem_condutor"] < 600
    assert info["fatal_rate_motorizados"] > info["fatal_rate_frota"]


def test_resumo(df):
    r = cd.resumo(df)
    assert r["condutor_mais_letal_dentro_do_estrato"] is True
    assert r["sem_condutor"]["n_veiculos_sem_condutor"] == 17150


def test_gerar_figuras(tmp_path, df):
    figs = cd.gerar_figuras(df, dest=tmp_path)
    assert len(figs) == 4
    assert all(p.exists() and p.stat().st_size > 0 for p in figs)
