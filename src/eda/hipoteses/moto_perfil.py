"""Fase 3.2 — motocicleta, sexo e papel (F3-3, Co2, Co3, F3-9; spec D/F). H5–H9.

Base fixa: `apenas_vitimas(com_desfecho=True)` (Cn3).

- H5 — a inversão de sinal do sexo por papel (Co3) some ao estratificar por
  `tipo_veiculo`? (esperado `confundido`; se sobreviver, é o achado mais forte)
- H6 — a letalidade 2× da moto (Ve3) sobrevive ao ajuste por idade e sexo?
- H7 — "vulnerável sem carroceria" é um grupo coerente ou riscos de ordens diferentes?
- H8 — perfil do condutor (idade) × causa: álcool/velocidade no jovem?
- H9 — os ~530 veículos motorizados sem condutor (F3-9/Co4): caracterizar.

Uso: ``python -m src.eda.hipoteses.moto_perfil``
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

from src.const import CAUSA_ALCOOL_CONDUTOR, CAUSA_PROXY_VELOCIDADE, FIGURES_PATH  # noqa: E402
from src.eda import inferencia as inf  # noqa: E402
from src.eda.dataset import apenas_vitimas, load_enriched, por_pessoa  # noqa: E402

DEST = FIGURES_PATH / "hipoteses" / "moto_perfil"
VULNERAVEIS_VEIC = ["Motocicleta", "Bicicleta", "Ciclomotor"]


def base(df: pd.DataFrame | None = None) -> pd.DataFrame:
    if df is None:
        df = load_enriched()
    return apenas_vitimas(por_pessoa(df), com_desfecho=True)


# --- H5 -----------------------------------------------------------------
def h5_sexo_papel_por_veiculo(b: pd.DataFrame) -> pd.DataFrame:
    """Letalidade por (sexo × papel), no geral e dentro de Automóvel."""
    occ = b[b["tipo_envolvido"].isin(["Condutor", "Passageiro"])]
    geral = occ.groupby(["sexo", "tipo_envolvido"], observed=True)["mortos"].agg(["mean", "size"])
    auto = occ[occ["tipo_veiculo"] == "Automóvel"].groupby(
        ["sexo", "tipo_envolvido"], observed=True
    )["mortos"].agg(["mean", "size"])
    return pd.concat({"geral": geral, "automovel": auto}, axis=1)


def h5_condutor_vs_passageiro_padronizado(b: pd.DataFrame, sexo: str) -> pd.DataFrame:
    occ = b[b["tipo_envolvido"].isin(["Condutor", "Passageiro"]) & b["sexo"].eq(sexo)]
    return inf.padronizacao_direta(
        occ, "tipo_envolvido", "mortos", eixos=["faixa_etaria", "tipo_veiculo"]
    )


# --- H6 ---------------------------------------------------------------
def h6_moto_vs_auto_condutor(b: pd.DataFrame) -> dict:
    cond = b[b["tipo_envolvido"] == "Condutor"]
    sub = cond[cond["tipo_veiculo"].isin(["Motocicleta", "Automóvel"])]
    res = inf.contraste(sub, sub["tipo_veiculo"].eq("Motocicleta"), "mortos",
                        eixos=["faixa_etaria", "sexo"], rotulo="condutor moto vs auto")
    res["padronizacao"] = inf.padronizacao_direta(
        sub, "tipo_veiculo", "mortos", eixos=["faixa_etaria", "sexo"]
    )
    return res


# --- H7 -----------------------------------------------------------------
def h7_vulneravel_sem_carroceria(b: pd.DataFrame) -> pd.DataFrame:
    """Letalidade de cada componente do grupo 'vulnerável' + do grupo agregado."""
    linhas = {
        "Pedestre (papel)": b[b["tipo_envolvido"] == "Pedestre"]["mortos"],
        "Motocicleta": b[b["tipo_veiculo"] == "Motocicleta"]["mortos"],
        "Ciclomotor": b[b["tipo_veiculo"] == "Ciclomotor"]["mortos"],
        "Bicicleta": b[b["tipo_veiculo"] == "Bicicleta"]["mortos"],
    }
    out = pd.DataFrame(
        {k: {"letalidade": v.mean(), "n": len(v)} for k, v in linhas.items()}
    ).T
    vuln = b["tipo_envolvido"].eq("Pedestre") | b["tipo_veiculo"].isin(VULNERAVEIS_VEIC)
    out.loc["— agregado —"] = [b[vuln]["mortos"].mean(), int(vuln.sum())]
    out.loc["fechado (ref.)"] = [b[~vuln]["mortos"].mean(), int((~vuln).sum())]
    out["razao_vs_moto"] = out["letalidade"] / out.loc["Motocicleta", "letalidade"]
    return out


# --- H8 -------------------------------------------------------------
def h8_causa_por_faixa_etaria(b: pd.DataFrame) -> pd.DataFrame:
    """Para as causas de interesse: % de condutores < 30 anos quando a causa é
    atribuída, vs. a base. `causa` é atribuição do BO (ressalva C1)."""
    cond = b[b["tipo_envolvido"] == "Condutor"].copy()
    cond["jovem"] = cond["idade"] < 30
    causas = [
        CAUSA_PROXY_VELOCIDADE, CAUSA_ALCOOL_CONDUTOR,
        "Reação tardia ou ineficiente do condutor", "Condutor Dormindo",
        "Ausência de reação do condutor",
    ]
    linhas = {}
    base_jovem = cond["jovem"].mean()
    for c in causas:
        m = cond["causa_acidente"].eq(c)
        linhas[c] = {
            "n": int(m.sum()),
            "share_jovem": cond[m]["jovem"].mean(),
            "idade_mediana": cond[m]["idade"].median(),
            "delta_vs_base_pp": 100 * (cond[m]["jovem"].mean() - base_jovem),
        }
    return pd.DataFrame(linhas).T


# --- H9 -----------------------------------------------------------------
def h9_motorizados_sem_condutor(df: pd.DataFrame) -> dict:
    pp = por_pessoa(df)
    com_cond = set(
        pp[pp["tipo_envolvido"] == "Condutor"].groupby(["id", "id_veiculo"]).groups.keys()
    )
    veic = pp.dropna(subset=["id_veiculo"]).drop_duplicates(["id", "id_veiculo"]).copy()
    veic["tem_condutor"] = [(i, v) in com_cond for i, v in zip(veic["id"], veic["id_veiculo"])]
    reboque = veic["tipo_veiculo"].str.contains("reboque|Reboque", na=False)
    mot = veic[(~veic["tem_condutor"]) & (~reboque)]

    acc_fatal = pp.groupby("id")["mortos"].max()
    return {
        "n": len(mot),
        "fatalidade_acidente": float(acc_fatal.reindex(mot["id"].unique()).mean()),
        "fatalidade_acidente_base": float(acc_fatal.mean()),
        "tipo_veiculo_top": mot["tipo_veiculo"].value_counts().head(5).to_dict(),
        "pct_rural": float((mot["uso_solo"] == "Não").mean()),
        "hora_mediana": float(mot["hora"].median()),
    }


# --- figuras / resumo -------------------------------------------------
def _salvar(fig: plt.Figure, nome: str, dest: Path) -> Path:
    dest.mkdir(parents=True, exist_ok=True)
    caminho = dest / nome
    fig.savefig(caminho, dpi=120, bbox_inches="tight")
    plt.close(fig)
    return caminho


def gerar_figuras(b: pd.DataFrame, dest: Path = DEST) -> list[Path]:
    figs = []

    h5 = h5_sexo_papel_por_veiculo(b)["geral"]["mean"].unstack()
    fig, ax = plt.subplots(figsize=(6, 4))
    h5.plot(kind="bar", ax=ax, color=["#4C72B0", "#C44E52"])
    ax.set_ylabel("letalidade"); ax.set_title("H5 — letalidade por sexo × papel")
    ax.tick_params(axis="x", rotation=0)
    figs.append(_salvar(fig, "h5_sexo_papel.png", dest))

    pad = h6_moto_vs_auto_condutor(b)["padronizacao"]
    fig, ax = plt.subplots(figsize=(6, 4))
    x = range(len(pad))
    ax.bar([i - 0.2 for i in x], pad["taxa_bruta"], 0.4, label="bruta", color="#4C72B0")
    ax.bar([i + 0.2 for i in x], pad["taxa_ajustada"], 0.4, label="ajustada idade+sexo", color="#C44E52")
    ax.set_xticks(list(x)); ax.set_xticklabels(pad.index)
    ax.set_ylabel("letalidade"); ax.set_title("H6 — condutor: moto × auto")
    ax.legend()
    figs.append(_salvar(fig, "h6_moto_vs_auto.png", dest))

    h7 = h7_vulneravel_sem_carroceria(b).drop(["— agregado —", "fechado (ref.)"])
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.bar(h7.index, h7["letalidade"], color="#C44E52")
    ax.set_ylabel("letalidade"); ax.set_title("H7 — 'vulnerável sem carroceria': riscos de ordens diferentes")
    ax.tick_params(axis="x", rotation=20)
    figs.append(_salvar(fig, "h7_vulneraveis.png", dest))

    return figs


def resumo(df: pd.DataFrame | None = None) -> dict:
    if df is None:
        df = load_enriched()
    b = base(df)
    h6 = h6_moto_vs_auto_condutor(b)
    h7 = h7_vulneravel_sem_carroceria(b)
    h8 = h8_causa_por_faixa_etaria(b)
    fem = h5_condutor_vs_passageiro_padronizado(b, "Feminino")
    masc = h5_condutor_vs_passageiro_padronizado(b, "Masculino")
    return {
        "n_base": len(b),
        "H5_fem_condutora_ajust": float(fem.loc["Condutor", "taxa_ajustada"]),
        "H5_fem_passageira_ajust": float(fem.loc["Passageiro", "taxa_ajustada"]),
        "H5_masc_condutor_ajust": float(masc.loc["Condutor", "taxa_ajustada"]),
        "H5_masc_passageiro_ajust": float(masc.loc["Passageiro", "taxa_ajustada"]),
        "H6": {k: h6[k] for k in ("taxa_exposto", "taxa_controle", "delta_pp",
                                  "delta_pp_ajustado", "rr", "ic_rr", "veredito")},
        "H7_razao_pedestre_vs_moto": float(h7.loc["Pedestre (papel)", "razao_vs_moto"]),
        "H7_razao_bicicleta_vs_moto": float(h7.loc["Bicicleta", "razao_vs_moto"]),
        "H8_velocidade_delta_pp": float(h8.loc[CAUSA_PROXY_VELOCIDADE, "delta_vs_base_pp"]),
        "H8_alcool_delta_pp": float(h8.loc[CAUSA_ALCOOL_CONDUTOR, "delta_vs_base_pp"]),
        "H8_alcool_idade_mediana": float(h8.loc[CAUSA_ALCOOL_CONDUTOR, "idade_mediana"]),
        "H9": h9_motorizados_sem_condutor(df),
    }


def main() -> None:
    df = load_enriched()
    b = base(df)
    import pprint

    pprint.pp(resumo(df))
    print("\nH5 sexo × papel:\n", h5_sexo_papel_por_veiculo(b).round(4))
    print("\nH5 padronizado (Feminino):\n", h5_condutor_vs_passageiro_padronizado(b, "Feminino").round(4))
    print("\nH5 padronizado (Masculino):\n", h5_condutor_vs_passageiro_padronizado(b, "Masculino").round(4))
    print("\nH7:\n", h7_vulneravel_sem_carroceria(b).round(4))
    print("\nH8:\n", h8_causa_por_faixa_etaria(b).round(3))
    for f in gerar_figuras(b):
        print("figura:", f)


if __name__ == "__main__":
    main()
