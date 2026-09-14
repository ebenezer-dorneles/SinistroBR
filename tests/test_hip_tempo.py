"""Testes da Fase 3.3 — src/eda/hipoteses/tempo.py (H10–H13)."""

import pytest

from src.const import CAUSA_ALCOOL_CONDUTOR
from src.eda.dataset import apenas_vitimas, load_enriched, por_acidente, por_pessoa
from src.eda.hipoteses import tempo as tp


@pytest.fixture(scope="module")
def df():
    return load_enriched()


@pytest.fixture(scope="module")
def ac(df):
    return por_acidente(df)


@pytest.fixture(scope="module")
def b(df):
    return apenas_vitimas(por_pessoa(df), com_desfecho=True)


@pytest.fixture(scope="module")
def pp(df):
    return por_pessoa(df)


def test_h10_alcool_concentra_na_madrugada_de_fim_de_semana(ac):
    h10 = tp.h10_composicao_causa_madrugada_fds(ac)
    assert h10.loc[CAUSA_ALCOOL_CONDUTOR, "razao"] > 3
    assert h10.loc["Condutor Dormindo", "razao"] > 2


def test_h11_letalidade_noturna_atenua_mas_sobrevive_ao_ajuste(b):
    h11 = tp.h11_letalidade_noturna_ajustada(b)
    c = h11["contraste"]
    assert c["delta_pp_ajustado"] < c["delta_pp"]  # composição explica parte
    assert c["delta_pp_ajustado"] > 1.0  # mas sobra efeito
    assert c["veredito"] == "confirmado"


def test_h12_tipo_de_acidente_difere_entre_janelas(ac):
    h12 = tp.h12_tipo_por_janela(ac)
    # fim de semana à noite: saída de leito (perda de controle) lidera
    assert h12.index[0] == "Saída de leito carroçável"
    # segunda de dia: colisão traseira (congestionamento) domina
    top_seg = h12.sort_values("segunda_dia", ascending=False).index[0]
    assert top_seg == "Colisão traseira"
    assert h12.loc["Colisão traseira", "segunda_dia"] > h12.loc["Colisão traseira", "fds_noite"]


def test_h13_unidades_discordam_e_tipos_letais_migram_para_noite(pp):
    h13 = tp.h13_mortes_por_tipo_e_hora(pp)
    # frontal mata mais por acidente; atropelamento, mais por pessoa
    assert h13.loc["Colisão frontal", "mortos_por_acidente"] > h13.loc["Atropelamento de Pedestre", "mortos_por_acidente"]
    assert h13.loc["Atropelamento de Pedestre", "mortos_por_pessoa"] > h13.loc["Colisão frontal", "mortos_por_pessoa"]
    mig = tp.h13_migracao_horaria(pp, ["Colisão frontal", "Atropelamento"])
    assert mig.loc["18-23", "Atropelamento"] > 2 * mig.loc["12-17", "Atropelamento"]


def test_resumo(df):
    r = tp.resumo(df)
    assert r["H10_alcool_razao"] > 3
    assert r["H11_veredito"] == "confirmado"


def test_gerar_figuras(tmp_path, ac, b, pp):
    figs = tp.gerar_figuras(ac, b, pp, dest=tmp_path)
    assert len(figs) == 4
    assert all(f.exists() and f.stat().st_size > 0 for f in figs)
