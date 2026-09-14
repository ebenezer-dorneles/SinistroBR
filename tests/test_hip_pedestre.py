"""Testes da Fase 3.1 — src/eda/hipoteses/pedestre.py (H1–H4)."""

import pytest

from src.eda.dataset import load_enriched
from src.eda.hipoteses import pedestre as ped


@pytest.fixture(scope="module")
def b():
    return ped.base(load_enriched())


def test_base_e_apenas_vitimas_com_desfecho(b):
    assert (b[["ilesos", "feridos_leves", "feridos_graves", "mortos"]].sum(axis=1) > 0).all()
    assert set(b["tipo_envolvido"].unique()) <= {"Condutor", "Passageiro", "Pedestre", "Cavaleiro"}


def test_h1_letalidade_pedestre_sobrevive_ao_ajuste_por_idade(b):
    r = ped.h1_pedestre_ajustado_idade(b)
    assert r["veredito"] == "confirmado"
    # o ajuste por idade encolhe o Δ (pedestre é mais velho) mas ele continua enorme
    assert r["delta_pp_ajustado"] < r["delta_pp"]
    assert r["delta_pp_ajustado"] > 15


def test_h2_atropelamento_mais_letal_a_noite(b):
    t = ped.h2_atropelamento_por_fase_dia(b)
    assert t.loc["Plena Noite", "taxa"] > 1.8 * t.loc["Pleno dia", "taxa"]
    r = ped.h2_contraste_noite_dia(b)
    assert r["veredito"] == "confirmado"


def test_h3_efeito_rural_maior_no_pedestre_em_escala_absoluta(b):
    h3 = ped.h3_interacao_rural_pedestre(b)
    # absoluto: penalidade rural do pedestre >> a do ocupante
    assert h3.loc["pedestre", "delta_pp"] > 4 * h3.loc["ocupante", "delta_pp"]
    # relativo: o RR rural do ocupante é maior (a interação inverte de escala)
    assert h3.loc["ocupante", "rr"] > h3.loc["pedestre", "rr"]


def test_h4_pedestre_skew_para_mais_velho(b):
    p = ped.h4_perfil_pedestre(b)
    assert p.loc["60+", "pedestre"] > 1.5 * p.loc["60+", "demais_vitimas"]
    s = ped.h4_sexo(b)
    assert abs(s.loc["Masculino", "pedestre"] - s.loc["Masculino", "demais_vitimas"]) < 0.03


def test_resumo(b):
    r = ped.resumo()
    assert r["n_pedestre"] > 3000
    assert r["H1"]["veredito"] == "confirmado"


def test_gerar_figuras(tmp_path, b):
    figs = ped.gerar_figuras(b, dest=tmp_path)
    assert len(figs) == 4
    assert all(f.exists() and f.stat().st_size > 0 for f in figs)
