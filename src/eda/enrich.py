"""Derivações de análise da Fase 2.0 (plan.md §2.0).

Passos que a Fase 1 não fez porque são decisões de **análise**, não de qualidade
de dado. Todas as funções recebem e devolvem um DataFrame (cópia), para poderem
ser encadeadas ou testadas isoladamente. `enriquecer()` aplica todas na ordem certa.
"""

from __future__ import annotations

import unicodedata
import warnings

import pandas as pd

from src.const import (
    CAUSA_MACRO,
    CAUSA_MACRO_DEFAULT,
    DIAS_SEMANA_ORDEM,
    FAIXA_ETARIA_BINS,
    FAIXA_ETARIA_LABELS,
    MARCA_PREFIXOS_CLASSIFICADORES,
    MARCA_SINONIMOS,
)

FAIXA_ETARIA_NULO = "Não informado"


def _slug(texto: str) -> str:
    """'Interseção de Vias' -> 'intersecao_de_vias' (para nomear colunas booleanas)."""
    sem_acento = "".join(
        c for c in unicodedata.normalize("NFKD", texto) if not unicodedata.combining(c)
    )
    return "_".join(sem_acento.lower().split())


def add_temporal_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Deriva `mes`, `dia_semana_ord` (categórica ordenada) e `hora` cheia.

    `dia_semana` bruto já vem em pt-BR ("segunda-feira", ...); só falta impor a
    ordem. `hora` sai de `horario` (timedelta) — nenhum gráfico temporal deve
    ordenar dia da semana alfabeticamente.
    """
    df = df.copy()
    df["mes"] = df["data_inversa"].dt.month
    df["dia_semana_ord"] = pd.Categorical(
        df["dia_semana"], categories=DIAS_SEMANA_ORDEM, ordered=True
    )
    df["hora"] = (df["horario"].dt.total_seconds() // 3600).astype("Int64")
    return df


def add_faixa_etaria(df: pd.DataFrame) -> pd.DataFrame:
    """Deriva `faixa_etaria` (categórica ordenada) a partir de `idade`.

    Cortes vêm de const.md. Idade nula vira um bucket próprio (`FAIXA_ETARIA_NULO`)
    em vez de sumir — a proporção de "não informado" é ela mesma um achado.
    """
    df = df.copy()
    faixa = pd.cut(
        df["idade"],
        bins=FAIXA_ETARIA_BINS,
        labels=FAIXA_ETARIA_LABELS,
        include_lowest=True,
    )
    faixa = faixa.cat.add_categories([FAIXA_ETARIA_NULO]).fillna(FAIXA_ETARIA_NULO)
    df["faixa_etaria"] = faixa
    return df


def canonicalize_tracado_via(df: pd.DataFrame) -> pd.DataFrame:
    """Canonicaliza `tracado_via` (multivalorado, sem ordem canônica).

    605 valores distintos só porque a ordem varia ("Reta;Declive" vs.
    "Declive;Reta" são o mesmo caso). Produz:
    - `tracado_via_canon`: características separadas por `;`, ordenadas
    - `tem_<caracteristica>`: uma coluna booleana por característica atômica
    """
    df = df.copy()
    listas = df["tracado_via"].fillna("").apply(
        lambda s: sorted(p.strip() for p in s.split(";") if p.strip())
    )
    df["tracado_via_canon"] = listas.apply(lambda xs: ";".join(xs)).replace("", pd.NA)

    atomos = sorted({a for xs in listas for a in xs})
    for atomo in atomos:
        df[f"tem_{_slug(atomo)}"] = listas.apply(lambda xs, a=atomo: a in xs)
    return df


def _marca_modelo(valor: object) -> tuple[object, object]:
    """"SCANIA/R500 A6X4" -> ("SCANIA", "R500 A6X4").

    Prefixos classificadores da PRF (const.MARCA_PREFIXOS_CLASSIFICADORES): em
    "I/M.BENZ 415 REVESC" o 2º segmento traz fabricante + modelo colados por
    espaço -> ("M.BENZ", "415 REVESC"). Sinônimos de const.MARCA_SINONIMOS são
    unificados. "NA" (isolado ou "NA/NA") vira ausência.
    """
    if not isinstance(valor, str):
        return pd.NA, pd.NA
    segmentos = [s.strip() for s in valor.split("/") if s.strip()]
    if not segmentos:
        return pd.NA, pd.NA

    if segmentos[0].upper() in MARCA_PREFIXOS_CLASSIFICADORES:
        resto = " ".join(segmentos[1:]).split()
        marca = resto[0].upper() if resto else None
        modelo = " ".join(resto[1:]) or pd.NA
    else:
        marca = segmentos[0].upper()
        modelo = "/".join(segmentos[1:]) or pd.NA

    if not marca or marca == "NA":
        return pd.NA, pd.NA
    return MARCA_SINONIMOS.get(marca, marca), modelo


def split_marca_modelo(df: pd.DataFrame) -> pd.DataFrame:
    """Separa `marca` (campo é `MARCA/MODELO`, ex.: "SCANIA/R500 A6X4").

    `marca_normalizada` = fabricante em maiúsculas, com prefixos I/SR/REB
    resolvidos e sinônimos unificados (Fase 2.5); `modelo` = o restante.
    """
    df = df.copy()
    pares = df["marca"].map(_marca_modelo)
    df["marca_normalizada"] = pares.str[0]
    df["modelo"] = pares.str[1]
    return df


def add_causa_macro(df: pd.DataFrame) -> pd.DataFrame:
    """Agrupa `causa_acidente` (69 valores) nas macro-categorias de const.md.

    A causa original é preservada. Causa fora do mapa vira `CAUSA_MACRO_DEFAULT`
    e dispara warning — sinal de taxonomia nova a mapear em const.py.
    """
    df = df.copy()
    presentes = set(df["causa_acidente"].dropna().unique())
    nao_mapeadas = presentes - set(CAUSA_MACRO)
    if nao_mapeadas:
        warnings.warn(
            f"causa_acidente sem macro-categoria em const.CAUSA_MACRO: {sorted(nao_mapeadas)}",
            stacklevel=2,
        )
    df["causa_macro"] = (
        df["causa_acidente"].map(CAUSA_MACRO).fillna(CAUSA_MACRO_DEFAULT)
    )
    return df


def enriquecer(df: pd.DataFrame) -> pd.DataFrame:
    """Aplica todas as derivações da Fase 2.0 na ordem correta."""
    df = add_temporal_columns(df)
    df = add_faixa_etaria(df)
    df = canonicalize_tracado_via(df)
    df = split_marca_modelo(df)
    df = add_causa_macro(df)
    return df
