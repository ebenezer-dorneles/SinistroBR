"""Fase 2.7 — condutor (unidade: pessoa, `tipo_envolvido == "Condutor"`, n = 122.367).

Perfil demográfico do condutor e sua severidade **comparada contra passageiro e
pedestre** — sem grupo de controle não dá para separar o efeito do papel do
efeito da população que dirige. Também investiga os veículos sem linha de
condutor (hipótese de evasão da spec §2.7).

Uso: ``python -m src.eda.dimensoes.condutor``
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

from src.const import FIGURES_PATH  # noqa: E402
from src.eda.dataset import (  # noqa: E402
    apenas_condutores,
    apenas_vitimas,
    load_enriched,
    por_pessoa,
    por_veiculo,
)

DEST = FIGURES_PATH / "condutor"

# Tipos de veículo autopropelidos — têm condutor por definição. Semirreboque e
# reboque são a metade rebocada de um conjunto articulado: não têm condutor
# próprio, e é isso que explica quase todos os `tipo_envolvido` nulos.
VEICULOS_MOTORIZADOS = [
    "Automóvel", "Motocicleta", "Caminhonete", "Camioneta", "Utilitário",
    "Caminhão-trator", "Caminhão", "Motoneta", "Ônibus", "Micro-ônibus",
    "Ciclomotor", "Triciclo", "Trator de rodas", "Motor-casa", "Quadriciclo",
]


# --------------------------------------------------------------------------
def perfil(condutores: pd.DataFrame) -> dict:
    idade = condutores["idade"].dropna()
    return {
        "n": len(condutores),
        "cobertura_idade_pct": round(100 * condutores["idade"].notna().mean(), 1),
        "idade_mediana": float(idade.median()),
        "idade_media": round(float(idade.mean()), 1),
        "sexo": condutores["sexo"].value_counts(dropna=False).to_dict(),
        "masc_pct": round(100 * condutores["sexo"].eq("Masculino").sum()
                          / condutores["sexo"].notna().sum(), 1),
        "menor_de_idade": int((condutores["idade"] < 18).sum()),
    }


def letalidade_papel(vitimas: pd.DataFrame) -> pd.DataFrame:
    """Letalidade e ferido grave por papel (Condutor / Passageiro / Pedestre)."""
    papeis = ["Condutor", "Passageiro", "Pedestre"]
    g = vitimas[vitimas["tipo_envolvido"].isin(papeis)].groupby("tipo_envolvido", observed=True)
    out = pd.DataFrame(
        {
            "n_pessoas": g.size(),
            "taxa_letalidade": g["mortos"].mean(),
            "taxa_ferido_grave": g["feridos_graves"].mean(),
        }
    )
    return out.reindex(papeis)


def letalidade_condutor_vs_passageiro(vitimas: pd.DataFrame, por: str) -> pd.DataFrame:
    """Letalidade Condutor × Passageiro estratificada por `por` (faixa_etaria/sexo).

    Isola o efeito do papel: se o condutor morre mais **dentro de cada estrato**,
    não é só porque a população que dirige é mais velha/masculina.
    """
    sub = vitimas[vitimas["tipo_envolvido"].isin(["Condutor", "Passageiro"])]
    return sub.pivot_table(
        index=por, columns="tipo_envolvido", values="mortos",
        aggfunc="mean", observed=True,
    ).round(4)


def letalidade_condutor_por_veiculo(condutores: pd.DataFrame, top: int = 8) -> pd.DataFrame:
    g = condutores.groupby("tipo_veiculo", observed=True)
    out = pd.DataFrame({"n": g.size(), "taxa_letalidade": g["mortos"].mean()})
    return out.sort_values("n", ascending=False).head(top)


def veiculos_sem_condutor(df: pd.DataFrame) -> dict:
    """Quantifica e caracteriza os veículos sem nenhuma linha `"Condutor"`.

    Achado: quase todos são semirreboque/reboque (metade rebocada, sem condutor
    próprio) — a hipótese de "condutor evadido" da spec §2.7 vale só para as
    ~500 linhas de veículo motorizado.
    """
    pessoas = por_pessoa(df)
    pv = pessoas.dropna(subset=["id_veiculo"])
    tem_cond = (
        pv.assign(_c=pv["tipo_envolvido"].eq("Condutor"))
        .groupby(["id", "id_veiculo"])["_c"].max()
    )
    sem = tem_cond[~tem_cond].index
    veic = por_veiculo(df).set_index(["id", "id_veiculo"]).loc[sem]
    motorizados = veic[veic["tipo_veiculo"].isin(VEICULOS_MOTORIZADOS)]

    return {
        "n_veiculos_sem_condutor": len(veic),
        "pct_da_frota": round(100 * len(veic) / len(por_veiculo(df)), 1),
        "por_tipo_veiculo": veic["tipo_veiculo"].value_counts().head(6).to_dict(),
        "reboques_e_semi": int(veic["tipo_veiculo"].isin(["Semireboque", "Reboque"]).sum()),
        "motorizados_sem_condutor": len(motorizados),
        "fatal_rate_motorizados": round(
            float(motorizados["classificacao_acidente"].eq("Com Vítimas Fatais").mean()), 3
        ),
        "fatal_rate_frota": round(
            float(por_veiculo(df)["classificacao_acidente"].eq("Com Vítimas Fatais").mean()), 3
        ),
    }


# --------------------------------------------------------------------------
def _salvar(fig: plt.Figure, nome: str, dest: Path) -> Path:
    dest.mkdir(parents=True, exist_ok=True)
    caminho = dest / nome
    fig.savefig(caminho, dpi=120, bbox_inches="tight")
    plt.close(fig)
    return caminho


def gerar_figuras(df: pd.DataFrame, dest: Path = DEST) -> list[Path]:
    vitimas = apenas_vitimas(por_pessoa(df))
    condutores = apenas_condutores(por_pessoa(df))
    figuras = []

    # perfil etário: condutor vs passageiro
    fig, ax = plt.subplots(figsize=(9, 4))
    for papel, cor in [("Condutor", "#4C72B0"), ("Passageiro", "#DD8452")]:
        s = (vitimas[vitimas["tipo_envolvido"] == papel]["faixa_etaria"]
             .value_counts(normalize=True).sort_index())
        ax.plot(s.index.astype(str), s.values, marker="o", label=papel, color=cor)
    ax.set_title("Distribuição etária: condutor vs passageiro")
    ax.set_ylabel("proporção")
    ax.legend()
    figuras.append(_salvar(fig, "perfil_etario.png", dest))

    # letalidade por papel
    lp = letalidade_papel(vitimas)
    fig, ax = plt.subplots(figsize=(7, 4))
    x = range(len(lp))
    ax.bar([i - 0.2 for i in x], lp["taxa_letalidade"], 0.4, label="letalidade", color="#C44E52")
    ax.bar([i + 0.2 for i in x], lp["taxa_ferido_grave"], 0.4, label="ferido grave", color="#DD8452")
    ax.set_xticks(list(x), lp.index)
    ax.set_title("Severidade por papel (base: vítimas)")
    ax.legend()
    figuras.append(_salvar(fig, "letalidade_papel.png", dest))

    # condutor vs passageiro estratificado por faixa etária
    piv = letalidade_condutor_vs_passageiro(vitimas, "faixa_etaria")
    fig, ax = plt.subplots(figsize=(9, 4))
    piv.plot(kind="bar", ax=ax, color={"Condutor": "#4C72B0", "Passageiro": "#DD8452"})
    ax.set_title("Letalidade condutor × passageiro, por faixa etária")
    ax.set_ylabel("mortos por pessoa")
    ax.tick_params(axis="x", rotation=20)
    figuras.append(_salvar(fig, "condutor_vs_passageiro_faixa.png", dest))

    # letalidade do condutor por tipo de veículo
    lv = letalidade_condutor_por_veiculo(condutores)
    fig, ax = plt.subplots(figsize=(9, 4))
    ax.barh(lv.index[::-1], lv["taxa_letalidade"][::-1], color="#C44E52")
    ax.set_title("Letalidade do condutor por tipo de veículo")
    ax.set_xlabel("mortos por condutor")
    figuras.append(_salvar(fig, "letalidade_condutor_veiculo.png", dest))

    return figuras


# --------------------------------------------------------------------------
def resumo(df: pd.DataFrame | None = None) -> dict:
    if df is None:
        df = load_enriched()
    pessoas = por_pessoa(df)
    vitimas = apenas_vitimas(pessoas)
    condutores = apenas_condutores(pessoas)

    lp = letalidade_papel(vitimas)
    fe = letalidade_condutor_vs_passageiro(vitimas, "faixa_etaria")
    sx = letalidade_condutor_vs_passageiro(vitimas, "sexo")

    return {
        "perfil": perfil(condutores),
        "letalidade_por_papel": lp["taxa_letalidade"].round(4).to_dict(),
        "condutor_vs_passageiro_por_faixa": fe.to_dict("index"),
        "condutor_vs_passageiro_por_sexo": sx.to_dict("index"),
        "condutor_mais_letal_dentro_do_estrato": bool(
            (fe["Condutor"] > fe["Passageiro"]).drop("Não informado", errors="ignore").all()
        ),
        "sem_condutor": veiculos_sem_condutor(df),
    }


def main() -> None:
    df = load_enriched()
    for k, v in resumo(df).items():
        print(f"{k}: {v}")
    figs = gerar_figuras(df)
    print("\nfiguras:")
    for f in figs:
        print(f"  {f}")


if __name__ == "__main__":
    main()
