"""ETL da Fase 1 (docs/specs/analise-exploratoria/plan.md).

Cobre os sete passos do pipeline descrito em spec.md §3.7:
1-3 leitura/normalização/tipagem, 4 sentinelas numéricos (`idade == 0` e
`ano_fabricacao_veiculo == 0` → NaN, decisão registrada em task.md),
5 outliers geo/km, 6 unicidade `(id, pesid)`, 7 persistência em parquet.

Devolutivas da Fase 2: `id_veiculo == 0` (pessoas sem veículo), `idade > 122`
(ano no lugar da idade) e `br == 0` / `km == 0` (localização na malha não
identificada) são sentinelas do mesmo tipo de `pesid == 0` e também são
normalizados aqui.
"""

from pathlib import Path

import pandas as pd

from src.const import (
    BRAZIL_LAT_RANGE,
    BRAZIL_LON_RANGE,
    MAX_PLAUSIBLE_AGE,
    MAX_PLAUSIBLE_KM,
    MIN_PLAUSIBLE_VEHICLE_YEAR,
    PROCESSED_DATA_PATH,
    RAW_DATA_PATH,
)

RAW_PATH = RAW_DATA_PATH
PROCESSED_PATH = PROCESSED_DATA_PATH

NA_VALUES = ["", "NA", "Não Informado", "Não Informado/Não Informado", "Ignorado"]

# Colunas onde 0 é um valor legítimo (indicador binário por pessoa), não sentinela.
SEVERITY_COLUMNS = ["ilesos", "feridos_leves", "feridos_graves", "mortos"]

# Colunas onde `0` é sentinela de "não informado", não valor real (spec §3.5).
# Decisão de negócio (task.md): converter para NaN. O relatório de qualidade
# registra quantas linhas foram afetadas antes da conversão.
SUSPECTED_SENTINEL_COLUMNS = ["idade", "ano_fabricacao_veiculo"]


def load_raw(path: Path = RAW_PATH) -> pd.DataFrame:
    """Lê o CSV bruto respeitando encoding, delimitador, aspas e decimal (spec §3.1-3.3)."""
    return pd.read_csv(
        path,
        sep=";",
        encoding="latin-1",
        quotechar='"',
        decimal=",",
        na_values=NA_VALUES,
        keep_default_na=False,
    )


def convert_types(df: pd.DataFrame) -> pd.DataFrame:
    """Converte data e horário (spec §3.7 passo 3). Campos numéricos já saem
    tipados corretamente de load_raw() via decimal="," e na_values."""
    df = df.copy()
    df["data_inversa"] = pd.to_datetime(df["data_inversa"], format="%Y-%m-%d", errors="coerce")
    df["horario"] = pd.to_timedelta(df["horario"], errors="coerce")
    return df


def normalize_pesid_sentinel(df: pd.DataFrame) -> pd.DataFrame:
    """Normaliza o sentinel numérico de `pesid` (spec §3.4: ~17k "ausentes").

    Ao contrário de idade/ano_fabricacao_veiculo (spec §3.5, bloqueado), o
    valor sentinela de `pesid` é `0` representando "sem informação", não um
    caso ambíguo pendente de regra de negócio — o próprio spec já contabiliza
    esses casos como ausentes na tabela de sentinelas (§3.4). Sem essa
    normalização, linhas distintas com pesid=0 no mesmo `id` colidem na
    checagem de unicidade (id, pesid) e são erroneamente tratadas como
    duplicatas exatas.
    """
    df = df.copy()
    df["pesid"] = df["pesid"].mask(df["pesid"] == 0)
    return df


def normalize_numeric_sentinels(df: pd.DataFrame) -> pd.DataFrame:
    """Converte sentinelas numéricos de `idade` e `ano_fabricacao_veiculo` para NaN (spec §3.7 passo 4).

    - `idade == 0` / `ano_fabricacao_veiculo == 0`: implausíveis; o dataset os usa
      como "não informado" (spec §3.5). Decisão de negócio (task.md): tratar como
      ausência.
    - `idade > MAX_PLAUSIBLE_AGE` (~139 linhas com valores como 2024, 914, 125):
      erro de digitação, ano no lugar da idade. Devolutiva da Fase 2 (task.md 2.8).
    - `ano_fabricacao_veiculo < MIN_PLAUSIBLE_VEHICLE_YEAR` (~19 linhas, quase todas
      "1900"): sentinela de "não informado". Devolutiva da Fase 2 (task.md 2.5).

    Análises que precisarem do cenário "com zeros" partem do dado bruto.
    """
    df = df.copy()
    for col in SUSPECTED_SENTINEL_COLUMNS:
        df[col] = df[col].mask(df[col] == 0)
    df["idade"] = df["idade"].mask(df["idade"] > MAX_PLAUSIBLE_AGE)
    df["ano_fabricacao_veiculo"] = df["ano_fabricacao_veiculo"].mask(
        df["ano_fabricacao_veiculo"] < MIN_PLAUSIBLE_VEHICLE_YEAR
    )
    return df


def normalize_idveiculo_sentinel(df: pd.DataFrame) -> pd.DataFrame:
    """Normaliza o sentinel `id_veiculo == 0` (~6,3k linhas).

    Mesma natureza de `pesid == 0` (normalize_pesid_sentinel): `0` não é um
    identificador de veículo, é "esta pessoa não estava num veículo" — são
    exatamente as linhas `tipo_envolvido` ∈ {Pedestre, Testemunha, Cavaleiro}.
    Sem nulificar, um `groupby("id_veiculo")` cria um "veículo 0" fantasma com
    milhares de linhas e a deduplicação por veículo (Fase 2, unidade veículo)
    conta esse fantasma como um veículo por acidente.
    """
    df = df.copy()
    df["id_veiculo"] = df["id_veiculo"].mask(df["id_veiculo"] == 0)
    return df


def normalize_br_km_sentinel(df: pd.DataFrame) -> pd.DataFrame:
    """Normaliza `br == 0` (e o `km` que o acompanha) para NaN.

    `0` não é uma BR federal — são acidentes cuja localização na malha não foi
    identificada (mantêm `municipio` e `latitude`/`longitude` válidos). Devolutiva
    da Fase 2 (task.md 2.2): sem nulificar, o par `(br=0, km=0)` vira o maior
    "trecho" no ranking de concentração, sem significado. `km` sem `br` não
    localiza nada, então cai junto; `km == 0` com `br` real (início de rodovia)
    é preservado.
    """
    df = df.copy()
    sem_br = df["br"] == 0
    df["br"] = df["br"].mask(sem_br).astype("Int64")
    df["km"] = df["km"].mask(sem_br)
    return df


def check_geo_outliers(df: pd.DataFrame) -> pd.Series:
    """Marca linhas com latitude/longitude fora dos limites geográficos do Brasil (spec §3.5)."""
    lat_ok = df["latitude"].between(*BRAZIL_LAT_RANGE) | df["latitude"].isna()
    lon_ok = df["longitude"].between(*BRAZIL_LON_RANGE) | df["longitude"].isna()
    return ~(lat_ok & lon_ok)


def check_km_outliers(df: pd.DataFrame) -> pd.Series:
    """Marca linhas com km negativo ou implausivelmente alto (spec §3.5).

    Não há um limite oficial por BR neste dataset; usa-se um teto conservador
    (maior BR federal tem pouco mais de 4000 km) só para pegar erros grosseiros
    de digitação.
    """
    return (df["km"] < 0) | (df["km"] > MAX_PLAUSIBLE_KM)


def check_duplicates(df: pd.DataFrame) -> pd.Series:
    """Retorna a máscara de linhas duplicadas por (id, pesid) (spec §3.6).

    Linhas com `pesid` nulo (sentinel normalizado por normalize_pesid_sentinel)
    representam pessoas sem identificador — nunca são consideradas duplicatas
    entre si, mesmo compartilhando o mesmo `id`.
    """
    has_pesid = df["pesid"].notna()
    dup = pd.Series(False, index=df.index)
    dup.loc[has_pesid] = df.loc[has_pesid].duplicated(subset=["id", "pesid"], keep="first")
    return dup


def drop_exact_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    """Remove duplicatas exatas por (id, pesid), se houver."""
    return df.loc[~check_duplicates(df)].reset_index(drop=True)


def build_quality_report(df: pd.DataFrame) -> dict:
    """Gera o relatório de qualidade de dados exigido como saída da Fase 1.

    Recebe o DataFrame **já tratado** — `null_counts_by_column` reflete o
    dataset persistido. As contagens do que foi corrigido durante o pipeline
    (sentinelas convertidos, duplicatas removidas) são injetadas por
    run_pipeline(), que as mede antes das respectivas etapas.
    """
    # SEVERITY_COLUMNS ficam inclusas: 0 é valor legítimo e não conta como
    # nulo, então isna() já reflete corretamente que elas não têm ausentes.
    null_counts = {col: int(df[col].isna().sum()) for col in df.columns}

    return {
        "total_rows": len(df),
        "null_counts_by_column": null_counts,
        "geo_outliers": int(check_geo_outliers(df).sum()),
        "km_outliers": int(check_km_outliers(df).sum()),
    }


def persist(df: pd.DataFrame, path: Path = PROCESSED_PATH) -> Path:
    """Grava o dataset tratado em parquet, separado do bruto (spec §3.7 passo 7).

    Parquet preserva os dtypes (datas, timedelta de `horario`, nullable ints das
    colunas com sentinela convertido) que um CSV perderia na releitura.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False)
    return path


def run_pipeline(
    path: Path = RAW_PATH, persist_output: bool = True
) -> tuple[pd.DataFrame, dict]:
    """Executa os sete passos da Fase 1 e retorna (df tratado, relatório).

    Com ``persist_output=True`` grava o resultado em ``PROCESSED_PATH``. A Fase 2
    consome esta função em memória com ``persist_output=False``.
    """
    df = load_raw(path)
    df = convert_types(df)
    df = normalize_pesid_sentinel(df)

    sentinel_zeros = {
        col: int((df[col] == 0).sum()) for col in SUSPECTED_SENTINEL_COLUMNS
    }
    implausible_ages = int((df["idade"] > MAX_PLAUSIBLE_AGE).sum())
    implausible_years = int(
        (df["ano_fabricacao_veiculo"].between(1, MIN_PLAUSIBLE_VEHICLE_YEAR - 1)).sum()
    )
    idveiculo_zeros = int((df["id_veiculo"] == 0).sum())
    br_zeros = int((df["br"] == 0).sum())

    df = normalize_idveiculo_sentinel(df)
    df = normalize_br_km_sentinel(df)
    duplicate_rows = int(check_duplicates(df).sum())

    df = normalize_numeric_sentinels(df)
    df = drop_exact_duplicates(df)

    report = build_quality_report(df)
    report["sentinel_zeros_converted_to_nan"] = sentinel_zeros
    report["implausible_ages_nulled"] = implausible_ages
    report["implausible_vehicle_years_nulled"] = implausible_years
    report["idveiculo_zeros_nulled"] = idveiculo_zeros
    report["br_zeros_nulled"] = br_zeros
    report["duplicate_rows_removed_id_pesid"] = duplicate_rows
    if persist_output:
        report["persisted_to"] = str(persist(df))
    return df, report


if __name__ == "__main__":
    treated_df, quality_report = run_pipeline()
    print(f"Linhas após remoção de duplicatas exatas: {len(treated_df)}")
    print()
    print("Relatório de qualidade de dados:")
    for key, value in quality_report.items():
        print(f"  {key}: {value}")
