"""Testes da Fase 3.4 — src/eda/hipoteses/via.py (H14–H16)."""

import pytest

from src.eda.dataset import load_enriched
from src.eda.hipoteses import via


@pytest.fixture(scope="module")
def df():
    return load_enriched()


@pytest.fixture(scope="module")
def b(df):
    return via.base(df)


def test_h14_pista_simples_agrava_por_dois_caminhos(b):
    c = via.h14_contraste(b)
    # composição explica parte (Δ cai), mas sobra efeito
    assert c["delta_pp_ajustado"] < c["delta_pp"]
    assert c["delta_pp_ajustado"] > 1.0
    assert c["veredito"] == "confirmado"
    # e dentro da colisão frontal, pista simples ~2× a dupla
    p = via.h14_pista_dentro_de_tipo(b)
    assert p.loc["Colisão frontal", "Simples"] > 1.8 * p.loc["Colisão frontal", "Dupla"]


def test_h15_declive_confirma_curva_confunde(b):
    h15 = via.h15_geometria_ajustada(b)
    assert h15.loc["declive", "veredito"] == "confirmado"
    assert h15.loc["declive", "delta_pp_ajustado"] > 1.0
    assert h15.loc["curva", "veredito"] == "confundido"
    assert h15.loc["curva", "delta_pp_ajustado"] < 1.0


def test_h16_meteoro_so_nevoeiro_agrava(b):
    m = via.h16_letalidade_por_meteoro(b).dropna(subset=["taxa"])
    m = m[m.index.notna()]
    assert m.index[0] == "Nevoeiro/Neblina"
    # chuva não agrava (V1)
    assert m.loc["Chuva", "taxa"] < m.loc["Céu Claro", "taxa"]


def test_h16_nevoeiro_confirma_chuva_sem_sinal(b):
    nev = via.h16_contraste_condicao(b, "Nevoeiro/Neblina")
    chu = via.h16_contraste_condicao(b, "Chuva")
    assert nev["veredito"] == "confirmado"
    assert nev["delta_pp_ajustado"] > 1.0
    assert chu["veredito"] in {"sem sinal", "rejeitado"}
    assert chu["delta_pp"] < 1.0


def test_resumo(df):
    r = via.resumo(df)
    assert r["H14"]["veredito"] == "confirmado"
    assert r["H15_declive_veredito"] == "confirmado"
    assert r["H15_curva_veredito"] == "confundido"


def test_gerar_figuras(tmp_path, b, df):
    figs = via.gerar_figuras(b, df, dest=tmp_path)
    assert len(figs) == 3
    assert all(f.exists() and f.stat().st_size > 0 for f in figs)
