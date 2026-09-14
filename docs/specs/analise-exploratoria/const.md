# 🎛️ const.md: Análise exploratória

Painel de controle e superfície de reprodutibilidade. **Nenhum número mágico,
caminho ou limiar deve nascer hardcoded em script/notebook** — importar de
`src/const.py` (fonte em código; este arquivo é a versão legível e justificada).

| Frequência de atualização | Média — ao introduzir novo parâmetro/caminho |
| :-- | :-- |

## Caminhos

| Constante | Valor | Uso |
| :-- | :-- | :-- |
| `RAW_DATA_PATH` | `data/raw/por_pessoa_acidentes2025.csv` | CSV bruto da PRF (ISO-8859-1) |
| `PROCESSED_DATA_PATH` | `data/processed/acidentes2025.parquet` | dataset tratado da Fase 1 |

`data/` é git-ignored: o parquet é gerado por `python -m src.etl.pipeline`, não versionado.

## Reprodutibilidade

| Constante | Valor | Motivo |
| :-- | :-- | :-- |
| `RANDOM_SEED` | `42` | qualquer amostragem/split da EDA e das fases seguintes |

## Limiares de qualidade de dados (Fase 1)

| Constante | Valor | Motivo |
| :-- | :-- | :-- |
| `BRAZIL_LAT_RANGE` | `(-33.75, 5.27)` | limites do Brasil continental com folga; pega erro de digitação de latitude. **0 outliers** no dataset atual |
| `BRAZIL_LON_RANGE` | `(-73.99, -32.39)` | idem, longitude. **0 outliers** |
| `MAX_PLAUSIBLE_KM` | `5000` | sem limite oficial por BR neste dataset; maior BR federal tem ~4.600 km. Teto só para erro grosseiro. **0 outliers** |
| `MAX_PLAUSIBLE_AGE` | `122` | recorde humano documentado ~122; acima disso é ano no lugar da idade ("2024", "914"). **139 linhas** nulificadas |
| `MIN_PLAUSIBLE_VEHICLE_YEAR` | `1950` | `ano_fabricacao_veiculo` abaixo disso é sentinela ("1900"). **32 linhas** nulificadas |

Sentinelas tratados no ETL (não são parâmetros ajustáveis, mas ficam registrados):
`idade == 0` (33.685), `ano_fabricacao_veiculo == 0` (17.394) e `ano < 1950` (32) → `NaN`;
`id_veiculo == 0` (6.341, pessoas sem veículo), `pesid == 0` (17.150) e
`br == 0` / `km` sem BR (167 acidentes, localização na malha não identificada) → `NaN`.

## Unidades de análise (Fase 2)

Toda estatística passa por `por_acidente` / `por_veiculo` / `por_pessoa`
(`src/eda/dataset.py`), nunca por `len(df)` direto. `checar_denominadores()`
trava se algum divergir.

| Constante | Valor | Recorte |
| :-- | :-- | :-- |
| `DENOMINADOR_ACIDENTES` | `72 529` | `drop_duplicates("id")` |
| `DENOMINADOR_VEICULOS` | `139 517` | `dropna("id_veiculo").drop_duplicates(["id","id_veiculo"])` — spec §2 estimava 139.518 (parsing ingênuo); valor medido é 139.517 |
| `DENOMINADOR_PESSOAS` | `194 629` | linha bruta |

## Parâmetros da EDA (Fase 2)

| Constante | Valor | Motivo |
| :-- | :-- | :-- |
| `TOP_N` | `15` | tamanho de rankings (UF, BR, município, marca, causa) |
| `KM_TRECHO_ROUND` | `1` | arredondamento de `km` para agregar acidentes por trecho `(br, km)` (Fase 2.2) |
| `FAIXA_ETARIA_BINS` | `[0, 17, 24, 34, 44, 59, 122]` | cortes de faixa etária (limite superior fechado) |
| `FAIXA_ETARIA_LABELS` | `["0-17","18-24","25-34","35-44","45-59","60+"]` | rótulos; idade nula vira bucket `"Não informado"` (não some) |
| `DIAS_SEMANA_ORDEM` | segunda→domingo | ordem categórica; nenhum gráfico temporal ordena dia da semana alfabeticamente |

### `PAPEIS_VITIMA` (base de severidade)

`["Condutor", "Passageiro", "Pedestre", "Cavaleiro"]` (`src/eda/dataset.py`) — os
papéis que podem ser vítima. `apenas_vitimas()` filtra por eles antes de qualquer
taxa de letalidade/gravidade; `Testemunha` e `tipo_envolvido` nulo (20.143
pessoas, nenhuma com desfecho) ficam de fora (achado 2.6/Vi5).

### Biblioteca de visualização

**matplotlib** — decisão local da Fase 2.0 (única opção madura já no ambiente;
não pré-julga a stack do dashboard das Fases 4/5). Registrada também em `plan.md`.

### Macro-categorias de `causa_acidente`

`CAUSA_MACRO` em `src/const.py` mapeia as 69 causas originais em 5 macros:
**Falha do condutor** (25), **Via / ambiente** (31), **Veículo** (8),
**Pedestre** (4), **Outros** (2 — suicídio/transtorno mental). A causa original é
preservada em `causa_acidente` para drill-down; `causa_macro` é a coluna derivada.
O plano previa 4 macros; "Pedestre" foi separada de "Outros" porque comportamento
do pedestre não é falha do condutor nem da via (desvio registrado em `task.md`).
Causa nova (revisão da taxonomia PRF) cai em `"Outros"` e dispara `warning`.

## Parâmetros de inferência (Fase 3)

> Em `src/const.py` desde a tarefa 3.0, junto com `src/eda/inferencia.py`. A regra de
> veredito é decisão de planejamento — foi fechada **antes** de rodar a primeira
> hipótese, senão o limiar acabaria escolhido depois de ver o resultado.

| Constante | Valor | Motivo |
| :-- | :-- | :-- |
| `MIN_N_CELULA` | `100` | mínimo de pessoas por célula estratificada. Abaixo disso o veredito é `inconclusivo (n)`, **não** `sem sinal` — a diferença importa para F3-9 (516 veículos) |
| `MIN_DELTA_PP` | `1.0` | diferença mínima em pontos percentuais para `confirmado`. Referência: a letalidade global de vítima é 3,64%; 1 pp é ~27% relativo |
| `MIN_RR` | `1.20` | razão de risco mínima, exigida **junto** com o Δ — sem ela, uma taxa baixa vira "efeito" por ruído; sem o Δ, um RR alto sobre base ínfima vira manchete. Efeito protetor: `RR ≤ 1/1,20 ≈ 0,83` |
| `NIVEL_CONFIANCA` | `0.95` | IC de Wilson (taxa) e de Katz (RR). Com n = 194 mil o IC serve para flagrar célula pequena, não para "significância" |
| `POPULACAO_PADRAO_EIXOS` | `["faixa_etaria", "tipo_veiculo"]` | eixos da padronização direta; a população-padrão é a distribuição das vítimas do dataset inteiro nesses eixos, calculada por `inferencia.populacao_padrao`. Fixada uma vez e reutilizada em toda a fase |
| `CAUSA_PROXY_VELOCIDADE` | `"Velocidade Incompatível"` | proxy (fraco) de velocidade — não há coluna `velocidade`. Atribuição do BO (ressalva C1), indício e nunca medida |
| `CAUSA_ALCOOL_CONDUTOR` | `"Ingestão de álcool pelo condutor"` | piso de prevalência de álcool (só registrado quando testado/evidente) |

**Por que tamanho de efeito e não p-valor:** com n = 194.629, qualquer diferença é
"significante". A regra de decisão da Fase 3 é `Δ ≥ MIN_DELTA_PP` **e**
`RR ≥ MIN_RR` **e** IC do RR sem cruzar 1 (`plan.md`, Premissa 2).

### `MARCA_PREFIXOS_CLASSIFICADORES` e `MARCA_SINONIMOS`

`MARCA_PREFIXOS_CLASSIFICADORES = {"I", "SR", "REB", "R"}` — prefixos de `marca`
que classificam o veículo (importado / semirreboque / reboque), não o fabricante.
Em "I/M.BENZ 415 REVESC" o fabricante real (M.BENZ) vem no 2º segmento, colado ao
modelo por espaço. `split_marca_modelo` (Fase 2.5) resolve o prefixo e separa
marca de modelo.

`MARCA_SINONIMOS` — grafias distintas do mesmo fabricante unificadas no ranking
(`CHEV`/`GM` → `CHEVROLET`, `VOLKSWAGEN` → `VW`, `MERCEDES` → `M.BENZ`,
`RANDONSP` → `RANDON`). Lista conservadora; a cauda longa de fabricantes de
implementos e ruído de string de modelo permanece, sem afetar o top-N.
