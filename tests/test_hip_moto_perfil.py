"""Testes da Fase 3.2 — src/eda/hipoteses/moto_perfil.py (H5–H9)."""

import pytest

from src.eda.dataset import load_enriched
from src.eda.hipoteses import moto_perfil as mp


@pytest.fixture(scope="module")
def df():
    return load_enriched()


@pytest.fixture(scope="module")
def b(df):
    return mp.base(df)


def test_h5_inversao_sexo_por_papel_sobrevive_ao_ajuste(b):
    """Mulher condutora continua mais segura que mulher passageira; homem
    condutor continua mais letal que homem passageiro — mesmo após padronizar
    por idade E tipo de veículo (não é só a moto)."""
    fem = mp.h5_condutor_vs_passageiro_padronizado(b, "Feminino")
    masc = mp.h5_condutor_vs_passageiro_padronizado(b, "Masculino")
    assert fem.loc["Condutor", "taxa_ajustada"] < fem.loc["Passageiro", "taxa_ajustada"]
    assert masc.loc["Condutor", "taxa_ajustada"] > masc.loc["Passageiro", "taxa_ajustada"]


def test_h6_letalidade_moto_sobrevive_ao_ajuste(b):
    r = mp.h6_moto_vs_auto_condutor(b)
    assert r["veredito"] == "confirmado"
    # o Δ não encolhe com o ajuste — moto driver é mais jovem, ajustar reforça
    assert r["delta_pp_ajustado"] >= r["delta_pp"] - 0.2
    assert r["rr"] > 2


def test_h7_grupo_vulneravel_nao_e_coerente(b):
    h7 = mp.h7_vulneravel_sem_carroceria(b)
    # pedestre é ~5× a letalidade da moto — não é uma categoria única
    assert h7.loc["Pedestre (papel)", "razao_vs_moto"] > 4
    assert h7.loc["Bicicleta", "razao_vs_moto"] > 2


def test_h8_causa_nao_concentra_em_condutor_jovem(b):
    h8 = mp.h8_causa_por_faixa_etaria(b)
    # álcool não concentra no jovem — mediana de idade ~40, delta negativo
    assert h8.loc["Ingestão de álcool pelo condutor", "delta_vs_base_pp"] < 1
    assert h8.loc["Velocidade Incompatível", "delta_vs_base_pp"] < 5


def test_h9_motorizados_sem_condutor_acidente_mais_fatal(df):
    h9 = mp.h9_motorizados_sem_condutor(df)
    assert h9["n"] > 400
    assert h9["fatalidade_acidente"] > 1.5 * h9["fatalidade_acidente_base"]
    assert h9["pct_rural"] > 0.7


def test_resumo(df):
    r = mp.resumo(df)
    assert r["H6"]["veredito"] == "confirmado"
    assert r["H5_fem_condutora_ajust"] < r["H5_fem_passageira_ajust"]


def test_gerar_figuras(tmp_path, b):
    figs = mp.gerar_figuras(b, dest=tmp_path)
    assert len(figs) == 3
    assert all(f.exists() and f.stat().st_size > 0 for f in figs)
