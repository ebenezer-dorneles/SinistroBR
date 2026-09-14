"""Testes da Fase 3.5 — src/eda/hipoteses/pontos_negros.py (H17–H19)."""

import pandas as pd
import pytest

from src.eda.dataset import load_enriched
from src.eda.hipoteses import pontos_negros as pn


@pytest.fixture(scope="module")
def df():
    return load_enriched()


def test_chave_de_trecho_inclui_uf(df):
    """Devolutiva: (br, km) não é único entre UFs — a chave correta tem uf."""
    assert pn.CHAVE[0] == "uf"
    negros = pn.trechos_negros(df)
    assert 350 < len(negros) < 420  # 382, não os 623 de G6


def test_h17_conjunto_estavel_ranking_instavel(df):
    h17 = pn.h17_estabilidade(df)
    # todo trecho negro aparece nos dois semestres
    assert h17["negros_presentes_nos_dois_semestres"] == h17["n_negros"]
    assert h17["negros_ge5_nos_dois_semestres"] > 0.95 * h17["n_negros"]
    # mas a ordem fina entre eles é ruído
    assert h17["spearman_entre_negros"] < 0.4


def test_h18_trecho_negro_e_urbano_e_multipista(df):
    a = pn.h18_assinatura(df)
    assert a.loc["uso_solo=Sim", "razao"] > 1.8  # mais urbano que a base
    assert a.loc["tipo_pista=Simples", "razao"] < 0.5  # muito menos pista simples
    t = pn.h18_tipo_acidente(df)
    assert t.index[0] == "Colisão traseira"  # perfil de congestionamento


def test_h19_volume_e_mortes_sao_quase_ortogonais(df):
    h19 = pn.h19_volume_vs_mortes(df, k=50)
    assert h19["intersecao"] <= 5  # top-50 acidentes e top-50 mortos mal se tocam


def test_gerar_csv(tmp_path, df):
    p = pn.gerar_csv(df, path=tmp_path / "pn.csv")
    d = pd.read_csv(p)
    assert 350 < len(d) < 420
    assert (d["acidentes"] >= 20).all()
    assert {"uf", "br", "km_trecho", "mortos", "letalidade", "tipo_pista"} <= set(d.columns)
    assert (d["letalidade_ic_baixo"] >= 0).all()


def test_gerar_figuras(tmp_path, df):
    figs = pn.gerar_figuras(df, dest=tmp_path)
    assert len(figs) == 3
    assert all(f.exists() and f.stat().st_size > 0 for f in figs)
