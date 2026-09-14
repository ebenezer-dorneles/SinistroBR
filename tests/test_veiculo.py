"""Testes da Fase 2.5 — dimensão veículo (src/eda/dimensoes/veiculo.py)."""

import pandas as pd
import pytest

from src.eda.dataset import load_enriched, por_pessoa, por_veiculo
from src.eda.dimensoes import veiculo as vd


@pytest.fixture(scope="module")
def df():
    return load_enriched()


@pytest.fixture(scope="module")
def veiculos(df):
    return por_veiculo(df)


@pytest.fixture(scope="module")
def pessoas(df):
    return por_pessoa(df)


def test_constancia_atributos_todos_zero(pessoas):
    """Pré-requisito da dedup por_veiculo: atributos constantes dentro do veículo."""
    div = vd.constancia_por_veiculo(pessoas)
    assert (div == 0).all(), div[div > 0].to_dict()


def test_distribuicao_tipo_sem_nulos_e_soma(veiculos):
    s = vd.distribuicao_tipo(veiculos)
    assert s.sum() == len(veiculos)
    assert veiculos["tipo_veiculo"].isna().sum() == 0  # nulos eram id_veiculo==0
    assert s.index[0] == "Automóvel"


def test_ranking_marca_top_limpo(veiculos):
    s = vd.ranking_marca(veiculos, top=15)
    assert len(s) == 15
    # prefixos classificadores não podem aparecer como marca
    assert not ({"I", "SR", "REB", "R", "NA"} & set(s.index))
    # sinônimos unificados
    assert "CHEVROLET" in s.index and "CHEV" not in s.index
    assert s.index[0] == "HONDA"


def test_idade_frota(veiculos):
    info = vd.idade_frota(veiculos)
    assert 85 <= info["cobertura_pct"] <= 100
    assert 5 <= info["idade_mediana"] <= 15
    assert info["serie_idade"].min() >= 0


def test_severidade_por_tipo_moto_lidera_obitos(pessoas):
    sev = vd.severidade_por_tipo(pessoas, top=None)
    assert sev["n_pessoas"].sum() == pessoas["id_veiculo"].notna().sum()
    # motocicleta é a maior fatia dos óbitos e ~2x a letalidade do automóvel
    assert sev.sort_values("mortos", ascending=False).index[0] == "Motocicleta"
    assert sev.loc["Motocicleta", "taxa_letalidade"] > 1.8 * sev.loc["Automóvel", "taxa_letalidade"]


def test_resumo(df):
    r = vd.resumo(df)
    assert all(v == 0 for v in r["constancia_divergencias"].values())
    assert r["moto_share_mortos_pct"] > 30
    assert r["bicicleta_letalidade"] > r["moto_letalidade"]


def test_split_marca_prefixo_importado():
    from src.eda.enrich import split_marca_modelo

    df = pd.DataFrame({"marca": ["I/M.BENZ 415 REVESC AMB", "SR/RANDON SR CA", "VW/GOL", "NA/NA"]})
    out = split_marca_modelo(df)
    assert out["marca_normalizada"].tolist()[:3] == ["M.BENZ", "RANDON", "VW"]
    assert out["modelo"].iloc[0] == "415 REVESC AMB"
    assert pd.isna(out["marca_normalizada"].iloc[3])


def test_gerar_figuras(tmp_path, veiculos, pessoas):
    figs = vd.gerar_figuras(veiculos, pessoas, dest=tmp_path)
    assert len(figs) == 4
    assert all(p.exists() and p.stat().st_size > 0 for p in figs)
