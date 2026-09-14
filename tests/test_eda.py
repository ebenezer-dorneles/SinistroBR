"""Testes da Fase 2.0 — preparo comum da EDA (src/eda/)."""

import warnings

import pandas as pd
import pytest

from src.const import (
    CAUSA_MACRO,
    DENOMINADOR_ACIDENTES,
    DENOMINADOR_PESSOAS,
    DENOMINADOR_VEICULOS,
    DIAS_SEMANA_ORDEM,
)
from src.eda import dataset, enrich, severity


@pytest.fixture(scope="module")
def enriched():
    return dataset.load_enriched()


# --- recortes por unidade de análise --------------------------------------


def test_denominadores(enriched):
    obtidos = dataset.checar_denominadores(enriched)
    assert obtidos == {
        "por_acidente": DENOMINADOR_ACIDENTES,
        "por_veiculo": DENOMINADOR_VEICULOS,
        "por_pessoa": DENOMINADOR_PESSOAS,
    }


def test_por_veiculo_exclui_pessoas_sem_veiculo(enriched):
    pv = dataset.por_veiculo(enriched)
    assert pv["id_veiculo"].notna().all()


def test_por_acidente_um_registro_por_id(enriched):
    pa = dataset.por_acidente(enriched)
    assert pa["id"].is_unique


# --- derivações temporais -------------------------------------------------


def test_dia_semana_ordenado(enriched):
    col = enriched["dia_semana_ord"]
    assert col.cat.ordered
    assert list(col.cat.categories) == DIAS_SEMANA_ORDEM


def test_hora_e_mes_no_intervalo(enriched):
    assert enriched["hora"].dropna().between(0, 23).all()
    assert enriched["mes"].dropna().between(1, 12).all()


# --- faixa etária -------------------------------------------------------


def test_faixa_etaria_cobre_nulos(enriched):
    assert enriched["faixa_etaria"].notna().all()
    n_nulo = (enriched["faixa_etaria"] == enrich.FAIXA_ETARIA_NULO).sum()
    assert n_nulo == enriched["idade"].isna().sum()


# --- tracado_via canonicalizado --------------------------------------------


def test_tracado_via_canon_colapsa_ordem():
    df = pd.DataFrame({"tracado_via": ["Reta;Declive", "Declive;Reta", "Curva"]})
    out = enrich.canonicalize_tracado_via(df)
    assert out["tracado_via_canon"].tolist() == ["Declive;Reta", "Declive;Reta", "Curva"]
    assert out["tem_reta"].tolist() == [True, True, False]
    assert out["tem_declive"].tolist() == [True, True, False]
    assert out["tem_curva"].tolist() == [False, False, True]


def test_tracado_via_indicadores_existem(enriched):
    for col in ["tem_reta", "tem_curva", "tem_declive", "tem_ponte"]:
        assert col in enriched.columns
        assert enriched[col].dtype == bool


# --- marca / modelo ----------------------------------------------------


def test_split_marca_modelo():
    df = pd.DataFrame({"marca": ["SCANIA/R500 A6X4", "VW/GOL", None]})
    out = enrich.split_marca_modelo(df)
    assert out["marca_normalizada"].tolist()[:2] == ["SCANIA", "VW"]
    assert out["modelo"].tolist()[0] == "R500 A6X4"
    assert pd.isna(out["marca_normalizada"].tolist()[2])


# --- causa macro -------------------------------------------------------


def test_causa_macro_cobre_todas_as_causas(enriched):
    presentes = set(enriched["causa_acidente"].dropna().unique())
    assert presentes <= set(CAUSA_MACRO), presentes - set(CAUSA_MACRO)


def test_causa_macro_sem_warning(enriched):
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        enrich.add_causa_macro(enriched)


# --- severidade -------------------------------------------------------


def test_taxa_letalidade_por_pessoa():
    df = pd.DataFrame({"mortos": [1, 0, 0, 1]})
    assert severity.taxa_letalidade_por_pessoa(df) == 0.5


def test_mortos_por_acidente():
    df = pd.DataFrame({"mortos": [1, 1, 0], "id": [10, 10, 20]})
    assert severity.mortos_por_acidente(df) == 1.0  # 2 mortos / 2 acidentes


def test_resumo_severidade_agrupado(enriched):
    out = severity.resumo_severidade(dataset.por_pessoa(enriched), por="tipo_envolvido")
    assert "taxa_letalidade" in out.columns
    # pedestre é o papel mais letal
    assert out.index[0] == "Pedestre"
    assert out.loc["Testemunha", "taxa_letalidade"] == 0.0
