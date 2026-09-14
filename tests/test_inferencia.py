"""Testes da Fase 3.0 — src/eda/inferencia.py.

IC de Wilson e RR de Katz contra valores publicados; padronização direta com um
caso sintético em que bruto e ajustado divergem de propósito.
"""

import math

import pandas as pd
import pytest

from src.eda import inferencia as inf


def test_wilson_contra_valor_publicado():
    # 3/100, Wilson 95% -> ~(0.0102, 0.0849) (Newcombe 1998)
    t = inf.taxa_com_ic(3, 100)
    assert t.p == pytest.approx(0.03)
    assert t.ic_baixo == pytest.approx(0.0102, abs=1e-3)
    assert t.ic_alto == pytest.approx(0.0849, abs=1e-3)


def test_wilson_nao_escapa_do_intervalo_com_zero_sucesso():
    t = inf.taxa_com_ic(0, 50)
    assert t.ic_baixo == 0.0
    assert 0 < t.ic_alto < 1


def test_wilson_n_zero_e_nan():
    t = inf.taxa_com_ic(0, 0)
    assert math.isnan(t.p)


def test_rr_katz_contra_valor_publicado():
    # 20/100 vs 10/100 -> RR 2.0, IC 95% ~ (0.99, 4.04)
    r = inf.rr_com_ic(20, 100, 10, 100)
    assert r.rr == pytest.approx(2.0)
    assert r.ic_baixo == pytest.approx(0.99, abs=0.03)
    assert r.ic_alto == pytest.approx(4.04, abs=0.05)
    assert r.delta_pp == pytest.approx(10.0)
    assert r.ic_cruza_1 is True


def test_rr_ic_nao_cruza_1_quando_efeito_e_claro():
    r = inf.rr_com_ic(200, 1000, 50, 1000)
    assert r.rr == pytest.approx(4.0)
    assert r.ic_cruza_1 is False


def test_tabela_estratificada_marca_celula_pequena_sem_deletar():
    df = pd.DataFrame(
        {
            "g": ["a"] * 200 + ["b"] * 10,
            "mortos": [1] * 20 + [0] * 180 + [1] * 2 + [0] * 8,
        }
    )
    t = inf.tabela_estratificada(df, "g", "mortos")
    assert set(t.index) == {"a", "b"}
    assert t.loc["a", "n_baixo"] == False  # noqa: E712
    assert t.loc["b", "n_baixo"] == True  # noqa: E712
    assert t.loc["a", "taxa"] == pytest.approx(0.1)


def test_padronizacao_direta_diverge_do_bruto_por_composicao():
    """Caso sintético: grupo B só tem idosos (risco alto). O bruto acusa B, o
    ajustado (mesma composição etária) quase iguala os dois."""
    def grupo(nome, n_j, n_i):
        j = pd.DataFrame({"faixa_etaria": ["j"] * n_j,
                          "mortos": [1] * round(0.05 * n_j) + [0] * (n_j - round(0.05 * n_j))})
        i = pd.DataFrame({"faixa_etaria": ["i"] * n_i,
                          "mortos": [1] * round(0.20 * n_i) + [0] * (n_i - round(0.20 * n_i))})
        return pd.concat([j, i]).assign(exp=nome)

    # mesmos riscos por estrato (j=0.05, i=0.20); só a composição etária difere
    df = pd.concat([grupo("A", 900, 100), grupo("B", 100, 900)], ignore_index=True)

    out = inf.padronizacao_direta(df, "exp", "mortos", eixos=["faixa_etaria"])
    assert out.loc["B", "taxa_bruta"] > out.loc["A", "taxa_bruta"] + 0.05
    assert out.loc["A", "taxa_ajustada"] == pytest.approx(out.loc["B", "taxa_ajustada"], abs=1e-9)


def test_veredito_cobre_os_cinco():
    assert inf.veredito(10, 2.0, (1.3, 3.1), True) == "confirmado"
    assert inf.veredito(0.2, 1.05, (0.9, 1.2), True, houve_efeito_bruto=True) == "rejeitado"
    assert inf.veredito(0.2, 1.05, (0.9, 1.2), True) == "sem sinal"
    assert inf.veredito(5, 2, (1.2, 3), False) == "inconclusivo (n)"
    assert inf.veredito(5, 2, (1.2, 3), True, efeito_bruto_sumiu=True) == "confundido"


def test_veredito_efeito_protetor_confirma():
    # RR 0.6 (protetor forte), IC não cruza 1, Δ além do limiar
    assert inf.veredito(-2.0, 0.6, (0.4, 0.85), True) == "confirmado"
