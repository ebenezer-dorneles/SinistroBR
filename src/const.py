"""Painel de controle / superfície de reprodutibilidade (docs/specs/analise-exploratoria/const.md).

Fonte única em código dos caminhos, sementes e limiares usados pelo ETL (Fase 1) e
pela EDA (Fase 2). Nada de número mágico solto em script/notebook — importar daqui.
O `const.md` é a versão legível deste arquivo e explica o porquê de cada valor.
"""

from pathlib import Path

# --- Caminhos -----------------------------------------------------------------
RAW_DATA_PATH = Path("data/raw/por_pessoa_acidentes2025.csv")
PROCESSED_DATA_PATH = Path("data/processed/acidentes2025.parquet")
REPORTS_PATH = Path("reports")
FIGURES_PATH = REPORTS_PATH / "figuras"

# --- Reprodutibilidade -------------------------------------------------------
RANDOM_SEED = 42

# Dataset cobre o ano de 2025 inteiro (01/01 a 31/12).
ANO_REFERENCIA = 2025
DIAS_NO_PERIODO = 365

# --- Limiares de qualidade de dados (Fase 1) --------------------------------
# Limites geográficos do Brasil continental, com folga, só para pegar erro de
# digitação de latitude/longitude.
BRAZIL_LAT_RANGE = (-33.75, 5.27)
BRAZIL_LON_RANGE = (-73.99, -32.39)

# Sem limite oficial de km por BR neste dataset; teto conservador (maior BR
# federal tem ~4.600 km) para erros grosseiros.
MAX_PLAUSIBLE_KM = 5000

# Idade máxima plausível de uma pessoa. Acima disso é erro de digitação
# (ano no lugar da idade: "2024", "914"). Registro do Guinness ~122.
MAX_PLAUSIBLE_AGE = 122

# Ano de fabricação abaixo disso é sentinela ("1900", 15 veículos) ou
# implausível para a frota que circula em rodovia federal hoje.
MIN_PLAUSIBLE_VEHICLE_YEAR = 1950

# --- Unidades de análise (Fase 2) ------------------------------------------
# Denominadores esperados do dataset tratado. Toda estatística da Fase 2 passa
# por por_acidente/por_veiculo/por_pessoa (src/eda/dataset.py), nunca por len(df).
DENOMINADOR_ACIDENTES = 72529
DENOMINADOR_VEICULOS = 139517
DENOMINADOR_PESSOAS = 194629

# --- Parâmetros da EDA (Fase 2) -------------------------------------------
# Nº de itens em rankings (UF, BR, município, marca, causa...).
TOP_N = 15

# Arredondamento de `km` para agregar acidentes por trecho de rodovia (Fase 2.2).
KM_TRECHO_ROUND = 1  # km inteiro

# Faixas etárias: cortes (limite superior fechado) e rótulos. Bucket separado
# para idade nula é criado pelo código, não entra aqui.
FAIXA_ETARIA_BINS = [0, 17, 24, 34, 44, 59, MAX_PLAUSIBLE_AGE]
FAIXA_ETARIA_LABELS = ["0-17", "18-24", "25-34", "35-44", "45-59", "60+"]

# Ordem canônica do dia da semana (o campo bruto vem em pt-BR minúsculo).
DIAS_SEMANA_ORDEM = [
    "segunda-feira",
    "terça-feira",
    "quarta-feira",
    "quinta-feira",
    "sexta-feira",
    "sábado",
    "domingo",
]

# Macro-categorias de causa_acidente (69 valores originais, cobertos abaixo). A
# causa original é preservada em coluna própria para drill-down. Uma causa nova
# (ex.: revisão da taxonomia da PRF) cai em CAUSA_MACRO_DEFAULT e dispara aviso
# no enriquecimento — sinal de que este dict precisa de atualização.
# Cinco macros: além das quatro do plano (condutor / via-ambiente / veículo /
# outros), "Pedestre" isola o comportamento do pedestre, que não é falha do
# condutor nem da via (desvio documentado em task.md).
CAUSA_MACRO = {
    # --- Falha / comportamento do condutor ---
    "Reação tardia ou ineficiente do condutor": "Falha do condutor",
    "Ausência de reação do condutor": "Falha do condutor",
    "Acessar a via sem observar a presença dos outros veículos": "Falha do condutor",
    "Condutor deixou de manter distância do veículo da frente": "Falha do condutor",
    "Manobra de mudança de faixa": "Falha do condutor",
    "Velocidade Incompatível": "Falha do condutor",
    "Transitar na contramão": "Falha do condutor",
    "Ingestão de álcool pelo condutor": "Falha do condutor",
    "Ultrapassagem Indevida": "Falha do condutor",
    "Condutor Dormindo": "Falha do condutor",
    "Desrespeitar a preferência no cruzamento": "Falha do condutor",
    "Trafegar com motocicleta (ou similar) entre as faixas": "Falha do condutor",
    "Conversão proibida": "Falha do condutor",
    "Mal súbito do condutor": "Falha do condutor",
    "Frear bruscamente": "Falha do condutor",
    "Retorno proibido": "Falha do condutor",
    "Condutor desrespeitou a iluminação vermelha do semáforo": "Falha do condutor",
    "Transitar no Acostamento": "Falha do condutor",
    "Estacionar ou parar em local proibido": "Falha do condutor",
    "Condutor usando celular": "Falha do condutor",
    "Acesso irregular": "Falha do condutor",
    "Ingestão de substâncias psicoativas pelo condutor": "Falha do condutor",
    "Participar de racha": "Falha do condutor",
    "Deixar de acionar o farol da motocicleta (ou similar)": "Falha do condutor",
    "Transitar na calçada": "Falha do condutor",
    # --- Via / ambiente ---
    "Animais na Pista": "Via / ambiente",
    "Chuva": "Via / ambiente",
    "Pista Escorregadia": "Via / ambiente",
    "Acumulo de água sobre o pavimento": "Via / ambiente",
    "Objeto estático sobre o leito carroçável": "Via / ambiente",
    "Demais falhas na via": "Via / ambiente",
    "Acumulo de areia ou detritos sobre o pavimento": "Via / ambiente",
    "Ausência de sinalização": "Via / ambiente",
    "Pista esburacada": "Via / ambiente",
    "Curva acentuada": "Via / ambiente",
    "Iluminação deficiente": "Via / ambiente",
    "Afundamento ou ondulação no pavimento": "Via / ambiente",
    "Falta de acostamento": "Via / ambiente",
    "Demais Fenômenos da natureza": "Via / ambiente",
    "Sinalização mal posicionada": "Via / ambiente",
    "Acostamento em desnível": "Via / ambiente",
    "Acumulo de óleo sobre o pavimento": "Via / ambiente",
    "Área urbana sem a presença de local apropriado para a travessia de pedestres": "Via / ambiente",
    "Neblina": "Via / ambiente",
    "Desvio temporário": "Via / ambiente",
    "Fumaça": "Via / ambiente",
    "Falta de elemento de contenção que evite a saída do leito carroçável": "Via / ambiente",
    "Restrição de visibilidade em curvas horizontais": "Via / ambiente",
    "Faixas de trânsito com largura insuficiente": "Via / ambiente",
    "Restrição de visibilidade em curvas verticais": "Via / ambiente",
    "Declive acentuado": "Via / ambiente",
    "Semáforo com defeito": "Via / ambiente",
    "Redutor de velocidade em desacordo": "Via / ambiente",
    "Sistema de drenagem ineficiente": "Via / ambiente",
    "Sinalização encoberta": "Via / ambiente",
    # --- Veículo ---
    "Demais falhas mecânicas ou elétricas": "Veículo",
    "Avarias e/ou desgaste excessivo no pneu": "Veículo",
    "Problema com o freio": "Veículo",
    "Carga excessiva e/ou mal acondicionada": "Veículo",
    "Problema na suspensão": "Veículo",
    "Modificação proibida": "Veículo",
    "Faróis desregulados": "Veículo",
    "Deficiência do Sistema de Iluminação/Sinalização": "Veículo",
    # --- Pedestre ---
    "Entrada inopinada do pedestre": "Pedestre",
    "Pedestre andava na pista": "Pedestre",
    "Pedestre cruzava a pista fora da faixa": "Pedestre",
    "Pedestre - Ingestão de álcool/ substâncias psicoativas": "Pedestre",
    # --- Outros ---
    "Suicídio (presumido)": "Outros",
    "Transtornos Mentais (exceto suicidio)": "Outros",
}
CAUSA_MACRO_DEFAULT = "Outros"

# Prefixos de `marca` que são classificação do veículo, não fabricante:
# "I/" = importado, "SR/"/"R/" = semirreboque/reboque, "REB/" = reboque. Nesses casos o
# fabricante real vem no 2º segmento, colado ao modelo por espaço
# ("I/M.BENZ 415 REVESC" -> marca "M.BENZ", modelo "415 REVESC");
# split_marca_modelo (Fase 2.5) trata isso. "NA/NA" é ausência total.
MARCA_PREFIXOS_CLASSIFICADORES = {"I", "SR", "REB", "R"}

# --- Parâmetros de inferência (Fase 3) ------------------------------------
# Regra de veredito fixada ANTES de rodar a primeira hipótese (plan.md §Fase 3,
# Premissa 2): com n = 194.629 qualquer diferença é "significante", então a
# decisão é por tamanho de efeito, não por p-valor.
MIN_N_CELULA = 100  # pessoas por célula estratificada; abaixo -> "inconclusivo (n)"
MIN_DELTA_PP = 1.0  # diferença mínima em pontos percentuais para "confirmado"
MIN_RR = 1.20  # razão de risco mínima, exigida JUNTO com o Δ
NIVEL_CONFIANCA = 0.95  # IC de Wilson (taxa) e de Katz (RR)

# Eixos da padronização direta (população-padrão = distribuição das vítimas do
# dataset inteiro nesses eixos). Fixado uma vez e reutilizado em toda a fase.
POPULACAO_PADRAO_EIXOS = ["faixa_etaria", "tipo_veiculo"]

# Causa usada como proxy (fraco) de velocidade — não existe coluna `velocidade`
# nas 35 do CSV. É atribuição subjetiva do agente no BO (ressalva C1), indício e
# nunca medida.
CAUSA_PROXY_VELOCIDADE = "Velocidade Incompatível"
CAUSA_ALCOOL_CONDUTOR = "Ingestão de álcool pelo condutor"

# Grafias distintas do mesmo fabricante que sobram no ranking de marca.
MARCA_SINONIMOS = {
    "CHEV": "CHEVROLET",
    "GM": "CHEVROLET",
    "VOLKSWAGEN": "VW",
    "MERCEDES": "M.BENZ",
    "MERCEDES-BENZ": "M.BENZ",
    "RANDONSP": "RANDON",
}

