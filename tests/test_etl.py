"""Testes da Fase 1 — ETL (src/etl/pipeline.py)."""

import numpy as np
import pandas as pd
import pytest

from src.const import MAX_PLAUSIBLE_AGE
from src.etl import pipeline


@pytest.fixture(scope="module")
def treated():
    df, report = pipeline.run_pipeline(persist_output=False)
    return df, report


def test_encoding_e_decimal(treated):
    df, _ = treated
    # acento preservado (ISO-8859-1) e latitude como float (decimal ",")
    assert df["latitude"].dtype.kind == "f"
    assert df["causa_acidente"].str.contains("ã").any()


def test_sentinelas_textuais_viraram_nan(treated):
    df, _ = treated
    for col in ["sexo", "estado_fisico", "condicao_metereologica"]:
        assert not (df[col] == "Não Informado").any()
        assert not (df[col] == "Ignorado").any()


def test_idade_e_ano_zero_convertidos(treated):
    df, report = treated
    assert not (df["idade"] == 0).any()
    assert not (df["ano_fabricacao_veiculo"] == 0).any()
    assert report["sentinel_zeros_converted_to_nan"]["idade"] == 33685
    assert report["sentinel_zeros_converted_to_nan"]["ano_fabricacao_veiculo"] == 17394


def test_idade_implausivel_nulificada(treated):
    df, report = treated
    assert df["idade"].max() <= MAX_PLAUSIBLE_AGE
    assert report["implausible_ages_nulled"] == 139


def test_ano_fabricacao_implausivel_nulificado(treated):
    df, report = treated
    anos = df["ano_fabricacao_veiculo"].dropna()
    assert anos.min() >= 1950
    assert report["implausible_vehicle_years_nulled"] == 32


def test_id_veiculo_zero_normalizado(treated):
    df, report = treated
    assert not (df["id_veiculo"] == 0).any()
    assert report["idveiculo_zeros_nulled"] == 6341
    # as linhas nulificadas são exatamente pessoas sem veículo
    sem_veiculo = df[df["id_veiculo"].isna()]["tipo_envolvido"].dropna().unique()
    assert set(sem_veiculo) <= {"Pedestre", "Testemunha", "Cavaleiro"}


def test_br_zero_normalizado(treated):
    df, report = treated
    assert not (df["br"] == 0).any()
    assert report["br_zeros_nulled"] == 517
    assert df.loc[df["br"].isna(), "km"].isna().all()
    assert (df["km"] == 0).any()  # km==0 com br real (início de rodovia) preservado


def test_normalize_br_km_isolada():
    df = pd.DataFrame({"br": [0, 116, 0, 70], "km": [0.0, 0.0, 5.0, 12.0]})
    out = pipeline.normalize_br_km_sentinel(df)
    assert out["br"].isna().tolist() == [True, False, True, False]
    # km sem br cai junto; km==0 com br real é mantido
    assert out["km"].isna().tolist() == [True, False, True, False]
    assert out["km"].iloc[1] == 0.0


def test_unicidade_id_pesid(treated):
    df, _ = treated
    com_pesid = df[df["pesid"].notna()]
    assert not com_pesid.duplicated(subset=["id", "pesid"]).any()


def test_sem_outliers_geo_km(treated):
    _, report = treated
    assert report["geo_outliers"] == 0
    assert report["km_outliers"] == 0


def test_normalize_idveiculo_isolada():
    df = pd.DataFrame({"id_veiculo": [0, 1, 2, 0]})
    out = pipeline.normalize_idveiculo_sentinel(df)
    assert out["id_veiculo"].isna().tolist() == [True, False, False, True]
    assert df["id_veiculo"].tolist() == [0, 1, 2, 0]  # não muta o original


def test_normalize_numeric_sentinels_isolada():
    df = pd.DataFrame(
        {"idade": [0, 30, 2024, np.nan], "ano_fabricacao_veiculo": [0, 2010, 2020, 0]}
    )
    out = pipeline.normalize_numeric_sentinels(df)
    assert out["idade"].tolist()[1] == 30
    assert np.isnan(out["idade"].tolist()[0])
    assert np.isnan(out["idade"].tolist()[2])  # > MAX_PLAUSIBLE_AGE
    assert out["ano_fabricacao_veiculo"].isna().sum() == 2
