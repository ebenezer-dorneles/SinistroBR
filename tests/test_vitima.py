"""Testes da Fase 2.6 — vítima / pessoa (src/eda/dimensoes/vitima.py)."""

import pytest

from src.eda.dataset import apenas_vitimas, load_enriched, por_pessoa
from src.eda.dimensoes import vitima as vt


@pytest.fixture(scope="module")
def df():
    return load_enriched()


@pytest.fixture(scope="module")
def pessoas(df):
    return por_pessoa(df)


def test_apenas_vitimas_remove_testemunha_e_nulo(pessoas):
    vit = apenas_vitimas(pessoas)
    assert "Testemunha" not in vit["tipo_envolvido"].unique()
    assert vit["tipo_envolvido"].notna().all()
    assert len(vit) == 174486


def test_perfil_idade(pessoas):
    info = vt.perfil_idade(pessoas)
    assert info["sem_idade"] == 33824
    assert 80 <= info["cobertura_pct"] <= 90
    assert 35 <= info["mediana"] <= 42


def test_distribuicao_severidade_soma_e_sem_desfecho(pessoas):
    s = vt.distribuicao_severidade(pessoas)
    # ilesos + feridos + mortos + sem_desfecho = total de pessoas
    assert s["ilesos"] + s["feridos_leves"] + s["feridos_graves"] + s["mortos"] + s["sem_desfecho"] == len(pessoas)
    assert s["sem_desfecho"] == 28630
    # sem_desfecho == estado_fisico nulo (verificação da 2.8 antecipada)
    assert s["sem_desfecho"] == pessoas["estado_fisico"].isna().sum()


def test_letalidade_cresce_com_idade(pessoas):
    fe = vt.letalidade_por(apenas_vitimas(pessoas), "faixa_etaria")
    assert fe.loc["60+", "taxa_letalidade"] > fe.loc["25-34", "taxa_letalidade"]
    assert fe.loc["60+", "taxa_letalidade"] > fe.loc["0-17", "taxa_letalidade"]


def test_ferido_grave_pico_jovem_adulto(pessoas):
    fe = vt.letalidade_por(apenas_vitimas(pessoas), "faixa_etaria")
    faixas_reais = fe.drop(index="Não informado", errors="ignore")
    assert faixas_reais["taxa_ferido_grave"].idxmax() == "18-24"


def test_letalidade_homem_maior_que_mulher(pessoas):
    sx = vt.letalidade_por(apenas_vitimas(pessoas), "sexo")
    assert sx.loc["Masculino", "taxa_letalidade"] > sx.loc["Feminino", "taxa_letalidade"]


def test_pedestre_e_o_papel_mais_letal(pessoas):
    tp = vt.letalidade_por(apenas_vitimas(pessoas), "tipo_envolvido")
    assert tp.index[0] == "Pedestre"
    assert tp.loc["Pedestre", "taxa_letalidade"] > 0.25


def test_impacto_testemunha_infla_denominador(pessoas):
    imp = vt.impacto_testemunha(pessoas)
    assert imp["n_removidas"] == 20143
    assert imp["letalidade_vitimas"] > imp["letalidade_todas"]


def test_resumo(df):
    r = vt.resumo(df)
    assert r["letalidade_pedestre"] > 0.25
    assert r["letalidade_masc_vs_fem"][0] > r["letalidade_masc_vs_fem"][1]


def test_gerar_figuras(tmp_path, pessoas):
    figs = vt.gerar_figuras(pessoas, dest=tmp_path)
    assert len(figs) == 5
    assert all(p.exists() and p.stat().st_size > 0 for p in figs)
