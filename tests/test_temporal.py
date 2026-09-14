"""Testes da Fase 2.1 — dimensão temporal (src/eda/dimensoes/temporal.py)."""

import pandas as pd
import pytest

from src.const import DIAS_SEMANA_ORDEM
from src.eda.dataset import load_enriched, por_acidente
from src.eda.dimensoes import temporal


@pytest.fixture(scope="module")
def acidentes():
    return por_acidente(load_enriched())


def test_por_mes_cobre_12_meses_e_soma_o_total(acidentes):
    s = temporal.acidentes_por_mes(acidentes)
    assert len(s) == 12
    assert s.sum() == len(acidentes)


def test_por_dia_semana_ordenado_e_completo(acidentes):
    s = temporal.acidentes_por_dia_semana(acidentes)
    assert list(s.index) == DIAS_SEMANA_ORDEM
    assert s.sum() == len(acidentes)


def test_por_hora_cobre_0_a_23(acidentes):
    s = temporal.acidentes_por_hora(acidentes)
    assert list(s.index) == list(range(24))
    assert s.sum() == len(acidentes)
    assert s.idxmax() == 18  # pico de fim de tarde


def test_matriz_dia_hora_shape_e_total(acidentes):
    m = temporal.matriz_dia_hora(acidentes)
    assert m.shape == (7, 24)
    assert m.values.sum() == len(acidentes)


def test_exposicao_soma_24_horas(acidentes):
    horas = temporal.exposicao_horas_por_fase_dia(acidentes)
    assert horas.sum() == pytest.approx(24.0, abs=1e-6)


def test_fase_dia_normalizada_muda_o_ranking(acidentes):
    fd = temporal.fase_dia_normalizada(acidentes)
    # em contagem absoluta "Pleno dia" domina; normalizado, "Anoitecer" lidera
    assert acidentes["fase_dia"].value_counts().idxmax() == "Pleno dia"
    assert fd.index[0] == "Anoitecer"
    assert fd["indice_vs_media"].iloc[0] > 1


def test_resumo_bate_com_agregacoes(acidentes):
    r = temporal.resumo(acidentes)
    assert r["n_acidentes"] == len(acidentes)
    assert r["hora_pico"][0] == 18
    assert r["dia_semana_pico"][0] == "sábado"


def test_gerar_figuras(tmp_path, acidentes):
    figs = temporal.gerar_figuras(acidentes, dest=tmp_path)
    assert len(figs) == 5
    assert all(p.exists() and p.stat().st_size > 0 for p in figs)
