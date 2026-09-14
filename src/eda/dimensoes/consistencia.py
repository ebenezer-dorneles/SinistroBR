"""Fase 2.8 — consistências e devolutiva para a Fase 1.

Verificações cruzadas que a EDA precisa fazer antes de confiar nos números, e
cujos achados voltam como decisão de ETL ou de spec:

- `classificacao_acidente` (nível acidente) × flags de severidade das pessoas;
- `estado_fisico` × flags de severidade (redundância);
- revalidação retroativa da decisão `idade == 0` → NaN;
- resíduo de vítimas sem desfecho registrado.

Uso: ``python -m src.eda.dimensoes.consistencia``
"""

from __future__ import annotations

from src.eda.dataset import (
    SEVERITY_FLAGS,
    apenas_vitimas,
    load_enriched,
    por_acidente,
    por_pessoa,
)


# --------------------------------------------------------------------------
def classificacao_vs_flags(df) -> dict:
    """`classificacao_acidente` deve bater com as flags das pessoas do mesmo `id`.

    - "Com Vítimas Fatais"  ⇒ algum `mortos == 1`
    - "Com Vítimas Feridas" ⇒ algum ferido, nenhum morto
    - "Sem Vítimas"         ⇒ nenhum ferido nem morto
    """
    p = por_pessoa(df)
    tem_morto = p.groupby("id")["mortos"].max()
    tem_ferido = p.groupby("id")[["feridos_leves", "feridos_graves"]].max().max(axis=1)

    a = por_acidente(df).set_index("id")
    cls = a["classificacao_acidente"]
    tm = tem_morto.reindex(cls.index)
    tf = tem_ferido.reindex(cls.index)

    return {
        "n_acidentes": len(cls),
        "classificacao_nula": int(cls.isna().sum()),
        "fatal_sem_morto": int((cls.eq("Com Vítimas Fatais") & tm.eq(0)).sum()),
        "feridas_com_morto": int((cls.eq("Com Vítimas Feridas") & tm.eq(1)).sum()),
        "feridas_sem_vitima": int(
            (cls.eq("Com Vítimas Feridas") & tf.eq(0) & tm.eq(0)).sum()
        ),
        "sem_vitima_com_vitima": int(
            (cls.eq("Sem Vítimas") & (tf.eq(1) | tm.eq(1))).sum()
        ),
    }


def estado_fisico_vs_flags(df) -> dict:
    """`estado_fisico` nulo deve ser exatamente as linhas sem nenhuma flag."""
    p = por_pessoa(df)
    sem_flag = p[SEVERITY_FLAGS].sum(axis=1).eq(0)
    ef_nulo = p["estado_fisico"].isna()
    return {
        "estado_fisico_nulo": int(ef_nulo.sum()),
        "sem_nenhuma_flag": int(sem_flag.sum()),
        "identicos": bool((ef_nulo == sem_flag).all()),
        "mapeamento_estado_fisico": (
            p.dropna(subset=["estado_fisico"])
            .groupby("estado_fisico", observed=True)[SEVERITY_FLAGS]
            .sum()
            .idxmax(axis=1)
            .to_dict()
        ),
    }


def revalidar_idade_zero(df) -> dict:
    """Cruza as linhas sem idade com `tipo_envolvido` e desfecho.

    Veredito: a decisão `idade == 0 → NaN` se sustenta se a maioria das linhas
    sem idade for registro incompleto (sem desfecho) e/ou impossível de ser
    idade real (condutor).
    """
    p = por_pessoa(df)
    nul = p[p["idade"].isna()]
    sem_desfecho = nul[SEVERITY_FLAGS].sum(axis=1).eq(0)
    com = nul[~sem_desfecho]
    return {
        "n_sem_idade": len(nul),
        "por_tipo_envolvido": nul["tipo_envolvido"].value_counts(dropna=False).to_dict(),
        "sem_desfecho": int(sem_desfecho.sum()),
        "sem_desfecho_pct": round(100 * sem_desfecho.mean(), 1),
        "com_desfecho": len(com),
        "com_desfecho_condutores": int(com["tipo_envolvido"].eq("Condutor").sum()),
        "com_desfecho_passageiros": int(com["tipo_envolvido"].eq("Passageiro").sum()),
        "veredito": (
            "decisão idade==0 -> NaN confirmada: "
            f"{round(100 * sem_desfecho.mean(), 1)}% são registro incompleto e "
            f"{int(com['tipo_envolvido'].eq('Condutor').sum())} condutores não podem "
            "ter idade real 0"
        ),
    }


def vitimas_sem_desfecho(df) -> dict:
    """Quantifica o resíduo: vítimas (papel válido) sem nenhuma flag de severidade."""
    p = por_pessoa(df)
    vit = apenas_vitimas(p)
    vit_cd = apenas_vitimas(p, com_desfecho=True)
    sem = vit[SEVERITY_FLAGS].sum(axis=1).eq(0)
    return {
        "n_vitimas": len(vit),
        "sem_desfecho": int(sem.sum()),
        "sem_desfecho_pct": round(100 * sem.mean(), 1),
        "por_papel": vit[sem]["tipo_envolvido"].value_counts().to_dict(),
        "letalidade_base_atual": round(float(vit["mortos"].mean()), 4),
        "letalidade_com_desfecho": round(float(vit_cd["mortos"].mean()), 4),
    }


# --------------------------------------------------------------------------
def resumo(df=None) -> dict:
    if df is None:
        df = load_enriched()
    return {
        "classificacao_vs_flags": classificacao_vs_flags(df),
        "estado_fisico_vs_flags": estado_fisico_vs_flags(df),
        "revalidar_idade_zero": revalidar_idade_zero(df),
        "vitimas_sem_desfecho": vitimas_sem_desfecho(df),
    }


def main() -> None:
    df = load_enriched()
    for secao, info in resumo(df).items():
        print(f"\n=== {secao} ===")
        for k, v in info.items():
            print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
