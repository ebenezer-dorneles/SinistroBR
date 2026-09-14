# ☑️ task.md: Análise exploratória

Tarefas atômicas da **Fase 1 — ETL**, da **Fase 2 — EDA por dimensão** e da
**Fase 3 — Cruzamentos e hipóteses** (`plan.md`).

> **Regra:** a cada tarefa concluída, movê-la para `Concluídas` aqui **e** atualizar a
> seção "Status do projeto" do `README.md` na mesma passagem, antes de iniciar a próxima
> (ver `CLAUDE.md`).

## Backlog

**Fase 3 — Cruzamentos e hipóteses.** Regras que valem para **toda** tarefa H* abaixo
(detalhadas em `plan.md` §Fase 3):

1. Base fixa `apenas_vitimas(com_desfecho=True)`; declarar base e `n` em toda tabela.
2. Efeito reportado como **Δ pp + RR com IC 95%**; veredito por tamanho de efeito
   (`MIN_DELTA_PP`, `MIN_RR`, `MIN_N_CELULA`), nunca por p-valor.
3. Ajuste obrigatório por **idade** e **tipo de veículo** (+ `tipo_envolvido` quando o
   papel varia entre os grupos comparados) — estratificação + padronização direta.
4. Vereditos possíveis: `confirmado` / `rejeitado` / `sem sinal` / **`confundido`** /
   `inconclusivo (n)`. Registrar em `resultados-fase3.md` **junto com o número**,
   inclusive quando não houver sinal — o "não deu" é entregável da fase.

### Fase 3.0 — Preparo comum de inferência — `src/eda/inferencia.py` — **CONCLUÍDA**
- [x] `taxa_com_ic(sucessos, n)` — proporção + IC 95% de Wilson. — `inferencia.taxa_com_ic` (retorna `Taxa`).
- [x] `rr_com_ic(a, na, b, nb)` — RR + IC 95% pelo log de Katz + Δ em pp. — `inferencia.rr_com_ic` (retorna `RiscoRelativo` com `.ic_cruza_1`).
- [x] `tabela_estratificada(df, exposicao, desfecho, por=[...])` — taxa + IC por célula, marca `n_baixo` (`n < MIN_N_CELULA`), não deleta. — `inferencia.tabela_estratificada`.
- [x] `padronizacao_direta(df, exposicao, ...)` — taxa ajustada; população-padrão = distribuição de vítimas do dataset inteiro em `POPULACAO_PADRAO_EIXOS` (`faixa_etaria` × `tipo_veiculo`). — `inferencia.padronizacao_direta` + `populacao_padrao`.
- [x] `veredito(delta_pp, rr, ic_rr, n_ok, ...)` — aplica a regra da Premissa 2; 5 vereditos, mais os flags `efeito_bruto_sumiu` (→ `confundido`) e `houve_efeito_bruto` (→ `rejeitado` vs `sem sinal`).
- [x] Limiares em `src/const.py` + `const.md`: `MIN_N_CELULA=100`, `MIN_DELTA_PP=1.0`, `MIN_RR=1.20`, `NIVEL_CONFIANCA=0.95`, `POPULACAO_PADRAO_EIXOS`. Também `CAUSA_PROXY_VELOCIDADE`, `CAUSA_ALCOOL_CONDUTOR`.
- [x] `docs/specs/analise-exploratoria/resultados-fase3.md` — cabeçalho, regra de veredito e tabela-mestre H1–H19 vazia.
- [x] `tests/test_inferencia.py` (9 testes): Wilson vs Newcombe 1998, RR de Katz vs valor publicado, célula pequena marcada e não deletada, padronização direta com caso sintético só-composição (bruto diverge, ajustado idêntico), 5 vereditos + efeito protetor.

### Fase 3.1 — Pedestre e atropelamento (F3-2; spec §2.8 D/B) — `src/eda/hipoteses/pedestre.py` — **CONCLUÍDA**
- [x] **H1** — `confirmado`. Pedestre 27,7% vs ocupante 3,2%; padronizado por idade Δ 24,5→22,0 pp. A idade explica ~10% da diferença. — `h1_pedestre_ajustado_idade`.
- [x] **H2** — `confirmado`. Atropelamento noite/amanhecer 14,1% vs resto 7,4% (Δ 6,8 pp, RR 1,92; ajuste por idade não muda). Anoitecer é exceção (8,0%). — `h2_atropelamento_por_fase_dia`/`h2_contraste_noite_dia`. **Achado:** sem coluna de iluminação; visibilidade fica como indício.
- [x] **H3** — `confirmado` (escala absoluta) / `rejeitado` (relativa). Rural adiciona 15,3 pp ao pedestre e 2,5 pp ao ocupante; RR relativo maior no ocupante (2,50 vs 1,71). — `h3_interacao_rural_pedestre`. **Achado:** pedestre em rodovia rural é a pior combinação do dataset.
- [x] **H4** — `confirmado` (parcial). 60+ = 18,9% dos pedestres vs 10,8% das demais vítimas; 45+ = 42% vs 34%; sexo idêntico. 16,6% dos pedestres com idade "Não informado" (vs 2,9%). — `h4_perfil_pedestre`/`h4_sexo`.
- [x] Registrado em `resultados-fase3.md` §3.1 + 4 figuras em `reports/figuras/hipoteses/pedestre/`; testes em `tests/test_hip_pedestre.py` (7).

### Fase 3.2 — Motocicleta, sexo e papel (F3-3, Co2, Co3, F3-9; spec D/F) — `src/eda/hipoteses/moto_perfil.py` — **CONCLUÍDA**
- [x] **H5** — `confirmado` (**não** `confundido`). Padronizando por idade **e** tipo de veículo, ♀ condutora (1,4%) continua < ♀ passageira (2,6%) e ♂ condutor (3,6%) > ♂ passageiro (3,3%). A moto é confundidor parcial, não a explicação. — `h5_condutor_vs_passageiro_padronizado`.
- [x] **H6** — `confirmado`. Condutor moto 5,4% vs auto 2,4% (RR 2,23); Δ cresce de 3,0→3,3 pp após ajuste idade+sexo. — `h6_moto_vs_auto_condutor`.
- [x] **H7** — `rejeitado`. Agregado 7,0% mascara pedestre 27,7% / bicicleta 13,2% / ciclomotor 7,8% / moto 4,9% (fator 5,6). **Decisão:** dashboard mantém os quatro separados. — `h7_vulneravel_sem_carroceria`.
- [x] **H8** — `sem sinal`. "Velocidade Incompatível" +3,4 pp de share <30a; "álcool" −2,5 pp (mediana 40a); "dormindo" −3,5 pp. Ressalva C1. — `h8_causa_por_faixa_etaria`.
- [x] **H9** — `confirmado` (exploratório). 530 motorizados sem condutor: acidentes 15,2% fatais vs 7,2% base; 87% rural, hora mediana 10h. Mecanismo evasão vs. registro faltante não identificável. — `h9_motorizados_sem_condutor`.
- [x] Registrado em `resultados-fase3.md` §3.2 + 3 figuras; testes em `tests/test_hip_moto_perfil.py` (7).

### Fase 3.3 — Tempo: noite, madrugada e álcool (F3-4 + F3-6; spec B/E) — `src/eda/hipoteses/tempo.py` — **CONCLUÍDA**
- [x] **H10** — `confirmado`. Madrugada (0–4h) de sex–dom: "álcool" em 15,1% dos acidentes vs 4,5% no resto (3,4×); "dormindo" 3,3×. Piso, não prevalência. — `h10_composicao_causa_madrugada_fds`.
- [x] **H11** — `confirmado` (~40% da diferença bruta é composição). Noite 5,3% vs dia 2,5% (Δ 2,87 pp); padronizado por tipo de acidente + uso do solo Δ 1,69 pp. **Decisão:** "noite" vira **alerta**, não filtro. — `h11_letalidade_noturna_ajustada`.
- [x] **H12** — `confirmado`. FDS-noite: "saída de leito carroçável" 17,2% (perda de controle); segunda-dia: "colisão traseira" 22,7% (congestionamento). — `h12_tipo_por_janela`.
- [x] **H13** — `confirmado`. Frontal 0,39 mortos/acidente vs atropelamento 0,118 mortos/pessoa (C4 reconfirmado); ambos ~2× seu share nas janelas 0–5h e 18–23h. — `h13_mortes_por_tipo_e_hora`/`h13_migracao_horaria`.
- [x] Registrado em `resultados-fase3.md` §3.3 + 4 figuras; testes em `tests/test_hip_tempo.py` (6).

### Fase 3.4 — Via, ambiente e infraestrutura (F3-5, F3-7 + spec A) — `src/eda/hipoteses/via.py` — **CONCLUÍDA**
- [x] **H14** — `confirmado` (dois caminhos). Simples 4,9% vs 2,3%; padronizado por tipo de acidente Δ 1,56 pp; **dentro da frontal**: simples 12,6% vs dupla 6,1%. — `h14_pista_dentro_de_tipo`/`h14_contraste`.
- [x] **H15** — declive `confirmado` (Δ ajustado 1,15 pp, RR 1,46); curva `confundido` (Δ ajustado 0,73 pp). Interação com "Velocidade Incompatível" ≈ aditiva. — `h15_geometria_ajustada`/`h15_interacao_velocidade`.
- [x] **H16** — 3-way `sem sinal` (meteorologia atua uniforme entre causas); Nevoeiro/Neblina isolado `confirmado` (Δ ajustado 1,34 pp, RR 1,57, n=1.300). Chuva −0,55 pp (V1 confirmado). — `h16_3way_causa_meteoro`/`h16_contraste_condicao`.
- [x] Registrado em `resultados-fase3.md` §3.4 + 3 figuras; testes em `tests/test_hip_via.py` (6).

### Fase 3.5 — Pontos negros (F3-1; spec C) — `src/eda/hipoteses/pontos_negros.py` — **CONCLUÍDA**
- [x] **Devolutiva → G6:** a chave `(br, km)` não é única entre UFs (508/623 negros misturavam estados). Chave correta `(uf, br, km)` → **382** trechos negros, não 623. — `CHAVE` em `pontos_negros.py`.
- [x] **H17** — `confirmado` como conjunto (382/382 nos dois semestres, 377 com ≥5 em ambos), não como ranking (spearman entre negros = 0,19). **Decisão:** janela anual, apresentar conjunto e não top-N ordenado. — `h17_estabilidade`.
- [x] **H18** — `confirmado`. 78,5% urbano (2,2×), 86% pista dupla/múltipla, colisão traseira 28% + lateral mesmo sentido 22% (congestionamento); quase 0 "saída de leito". BR-101 km 205–208 = São José/SC, 300 acid. — `h18_assinatura`/`h18_tipo_acidente`/`h18_cluster_br101`.
- [x] **H19** — `confirmado`. top-50 acidentes ∩ top-50 mortos = 1. Volume (congestionamento urbano) e mortes (evento único rural) são ortogonais. **Decisão:** dashboard precisa de dois mapas. — `h19_volume_vs_mortes`.
- [x] Entregável `reports/pontos_negros.csv` — 382 trechos `(uf, br, km)` com município, n acidentes, n mortos, feridos graves, letalidade com IC de Wilson, tipo de pista e uso do solo. — `gerar_csv`.
- [x] Registrado em `resultados-fase3.md` §3.5 + 3 figuras; testes em `tests/test_hip_pontos_negros.py` (6).

### Fase 3.6 — Consolidação e handoff para a Fase 4 — **CONCLUÍDA**
- [x] `resultados-fase3.md` consolidado: tabela-mestre H1–H19 (unidade, base e `n`, efeito bruto, efeito ajustado, IC, veredito) + seção detalhada por sub-fase (§3.1–§3.5).
- [x] Tabela de corte **"vira gráfico × sem sinal"** — 13 itens que viram gráfico/KPI com a pergunta de negócio; 6 itens que **não** viram recomendação (H7, H8, H15-curva, chuva, interação meteoro×causa, ranking fino dos trechos).
- [x] Devolutiva para `spec.md` §2.8: nota "Devolutiva pós-Fase 3" com o veredito dos 6 cruzamentos.
- [x] Devolutiva para `achados-eda.md`: tabela "Resolução dos candidatos F3" (F3-1…F3-9) + correção de G6 (chave `(uf, br, km)`).
- [x] Devolutiva para a Fase 2.2 (não Fase 1): `concentracao_trecho` em `geografico.py` usava `(br, km)`, que conflita entre UFs. **Corrigido:** chave passou a `(uf, br, km)` (382 trechos, top SC/BR-101/km 208), `test_geografico.py` atualizado.
- [x] `README.md` (status + comandos) e `plan.md` (§Fase 3 fechada, placar) atualizados.

## Em Progresso
_(vazio — Fase 3 fechada. Próxima: Fase 4 — definição do dashboard, `plan.md` §Fase 4.)_

## Concluídas
- [x] Criar estrutura de diretórios `data/raw/` e `data/processed/`; mover `data/por_pessoa_acidentes2025.csv` para `data/raw/`.
- [x] Implementar leitura do CSV com `encoding="latin-1"`, `sep=";"`, `decimal=","`, respeitando aspas (spec §3.1–3.3). — `src/etl/pipeline.py:load_raw`.
- [x] Implementar normalização de sentinelas de ausência (`""`, `"NA"`, `"Não Informado"`, `"Não Informado/Não Informado"`, `"Ignorado"`) para `NaN` via `na_values` (spec §3.4). — `src/etl/pipeline.py:load_raw` (`NA_VALUES`).
- [x] Converter tipos: `data_inversa` (data), `horario` (hora), `idade`/`km`/`ano_fabricacao_veiculo`/`latitude`/`longitude` (numéricos) (spec §3.7 passo 3). — `src/etl/pipeline.py:convert_types` (numéricos já saem tipados de `load_raw` via `decimal=","`).
- [x] Checar e marcar/remover outliers de `latitude`/`longitude` fora dos limites geográficos do Brasil (spec §3.5). — `src/etl/pipeline.py:check_geo_outliers` (0 outliers encontrados no dataset atual).
- [x] Checar e marcar/remover `km`/`br` inconsistentes (ex.: km negativo ou fora do intervalo plausível da rodovia) (spec §3.5). — `src/etl/pipeline.py:check_km_outliers` (0 outliers encontrados).
- [x] Validar unicidade de linhas por `(id, pesid)` e tratar duplicatas exatas, se houver (spec §3.6). — `src/etl/pipeline.py:check_duplicates`/`drop_exact_duplicates`. **Achado:** `pesid == 0` é um sentinel de ausência (~17k linhas, bate com a estimativa do spec §3.4) não coberto pelos sentinelas textuais; sem normalizá-lo primeiro (`normalize_pesid_sentinel`), a checagem de unicidade colidia essas linhas e as marcava como ~6.283 falsas duplicatas. Corrigido antes de rodar o drop.
- [x] Gerar relatório de qualidade de dados: contagem de nulos tratados por coluna e outliers removidos/marcados (critério de saída da Fase 1 no `plan.md`). — `src/etl/pipeline.py:build_quality_report` (+ `sentinel_zeros_converted_to_nan` e `duplicate_rows_removed_id_pesid` injetados por `run_pipeline`).
- [x] Aplicar regra de negócio para `idade == 0` e `ano_fabricacao_veiculo == 0` (spec §3.7 passo 4). **Decisão:** converter ambos para `NaN` (idade real 0 / ano 0 implausíveis; são sentinela de "não informado"). — `src/etl/pipeline.py:normalize_numeric_sentinels`. Afetou 33.685 linhas de `idade` e 17.394 de `ano_fabricacao_veiculo`.
- [x] Persistir dataset tratado, separado do bruto (spec §3.7 passo 7). **Decisão:** parquet (preserva dtypes de data/`horario`/nullable) em `data/processed/acidentes2025.parquet`. — `src/etl/pipeline.py:persist`; `run_pipeline(persist_output=...)` controla a gravação (a Fase 2 usa `False` e consome em memória).
- [x] **Devolutiva da Fase 2 → Fase 1:** normalizar `id_veiculo == 0` (6.341 linhas = pedestre/testemunha/cavaleiro, sem veículo) para `NaN`, mesma natureza de `pesid == 0`. — `src/etl/pipeline.py:normalize_idveiculo_sentinel`. Sem isso, a dedup por veículo contava um "veículo 0" fantasma por acidente (144.922 em vez de 139.517).
- [x] **Devolutiva da Fase 2 → Fase 1:** nulificar `idade > 122` (139 linhas: "2024", "914", "125" — ano no lugar da idade). — `src/etl/pipeline.py:normalize_numeric_sentinels` + `const.MAX_PLAUSIBLE_AGE`.
- [x] Mover paths/seeds/limiares hardcoded para superfície de reprodutibilidade. — `src/const.py` (+ `docs/.../const.md`); `pipeline.py` passa a importar `BRAZIL_*_RANGE`, `MAX_PLAUSIBLE_*`, paths.
- [x] Criar `requirements.txt` (pandas, pyarrow, matplotlib, pytest) — ambiente reprodutível (critério de saída da Fase 0).

### Fase 2.0 — Preparo comum da EDA
- [x] Criar `docs/specs/analise-exploratoria/const.md` + `src/const.py`: faixas etárias, `TOP_N`, `KM_TRECHO_ROUND`, bounding box do Brasil, `RANDOM_SEED`, denominadores, mapa de `causa_macro`. Nenhum limiar da Fase 2 nasce hardcoded.
- [x] Escolher biblioteca de visualização: **matplotlib** (única madura no ambiente; não pré-julga a stack do dashboard). Registrado em `plan.md` e `const.md`.
- [x] Módulo `src/eda/` consumindo `run_pipeline(persist_output=False)` em memória. — `src/eda/dataset.py:load_enriched` (ou `from_parquet=True`).
- [x] Três recortes por unidade de análise + assert de denominadores 72.529 / 139.517 / 194.629. — `src/eda/dataset.py:por_acidente`/`por_veiculo`/`por_pessoa`/`checar_denominadores`. `por_veiculo` mede 139.517 (spec estimava 139.518 por parsing ingênuo).
- [x] Colunas temporais `mes`, `dia_semana_ord` (categórica ordenada seg→dom), `hora` cheia. — `src/eda/enrich.py:add_temporal_columns`.
- [x] `faixa_etaria` a partir de `idade`, cortes de `const.py`, bucket `"Não informado"` para nulo. — `src/eda/enrich.py:add_faixa_etaria`.
- [x] Canonicalizar `tracado_via`: conjunto ordenado (`tracado_via_canon`) + 12 indicadores `tem_<caracteristica>`. — `src/eda/enrich.py:canonicalize_tracado_via`. 605 combinações → 12 características atômicas; "Reta;Declive" e "Declive;Reta" colapsam.
- [x] Separar `marca_normalizada` (antes da `/`) de `modelo`. — `src/eda/enrich.py:split_marca_modelo`. Refino dos prefixos I/SR/REB fica na Fase 2.5.
- [x] Agrupar as 69 `causa_acidente` em 5 macros (condutor / via-ambiente / veículo / pedestre / outros), mapa em `const.CAUSA_MACRO`, causa original preservada, warning em causa não mapeada. — `src/eda/enrich.py:add_causa_macro`.
- [x] Métricas de severidade reutilizáveis. — `src/eda/severity.py`: `taxa_letalidade_por_pessoa`, `taxa_ferido_grave_por_pessoa`, `mortos_por_acidente`, `resumo_severidade(df, por=...)`.
- [x] Testes da Fase 1 e da Fase 2.0. — `tests/test_etl.py`, `tests/test_eda.py` (23 testes, incl. asserts de denominador e de colapso de `tracado_via`).

### Fase 2.1 — Temporal (unidade: acidente) — `src/eda/dimensoes/temporal.py`
- [x] Distribuição de acidentes por mês (dez pico 6.788 / fev vale 5.287; +28,4%). — `acidentes_por_mes`.
- [x] Distribuição por dia da semana (sábado pico, terça vale) e por hora cheia (pico 18h, vale 2h; picos duplos 7h e 17–19h). — `acidentes_por_dia_semana`, `acidentes_por_hora`.
- [x] Matriz dia da semana × hora (heatmap). — `matriz_dia_hora` + `reports/figuras/temporal/matriz_dia_hora.png`.
- [x] `fase_dia` normalizada pela exposição. — `exposicao_horas_por_fase_dia` (P(fase|hora) → horas/dia), `fase_dia_normalizada`. **Achado:** o domínio de "pleno dia" é parte exposição; o risco por hora pico ao **anoitecer** (índice 1,62) e a **letalidade** pico à noite/amanhecer (10–11% fatais vs 5% de dia).
- [x] Registrar achados em `achados-eda.md` (T1–T6; T4 e T6 → Fase 3). — testes em `tests/test_temporal.py` (8).

### Fase 2.2 — Geográfico (unidade: acidente) — `src/eda/dimensoes/geografico.py`
- [x] **Devolutiva → Fase 1:** normalizar `br == 0` / `km` sem BR (167 acidentes, localização na malha não identificada) para NaN. — `src/etl/pipeline.py:normalize_br_km_sentinel`. Sem isso `(br=0, km=0)` era o maior "trecho".
- [x] Rankings por `uf` (27), `br` (114, era 115 com o `0`) e `municipio` (1.844). — `ranking_uf`/`ranking_br`/`ranking_municipio`. BR-101+BR-116 = 33% dos acidentes; top-10 municípios = só 9,7%.
- [x] Concentração por trecho `(uf, br, km)` arredondado (`const.KM_TRECHO_ROUND`). — `com_trecho`/`concentracao_trecho`. **Atualizado pós-Fase 3 (G6/H17):** chave corrigida de `(br, km)` para `(uf, br, km)` — 382 trechos com ≥20 acidentes; topo SC/BR-101 km 205–208.
- [x] Mapa de densidade lat/long (hexbin log). — `gerar_figuras` → `densidade_espacial.png`. **Confirmado:** 0 nulos / 0 outliers, cobre 100% (spec §3.4 errado).
- [x] Documentar limitação de denominador (volume ≠ risco) em `achados-eda.md` (G3–G4).
- [x] `regional`/`delegacia`/`uop` como recorte operacional. — `cobertura_operacional`. **Decisão:** fora do dashboard principal (redundante com UF/BR; útil só para usuário PRF).
- [x] Achados G1–G7 em `achados-eda.md` (G6 → Fase 3). — testes em `tests/test_geografico.py` (9).

### Fase 2.3 — Causa e tipo do acidente (unidade: acidente) — `src/eda/dimensoes/causa_tipo.py`
- [x] Frequência de `causa_acidente` bruta (69) e de `causa_macro` (5). — `frequencia_causa`/`frequencia_causa_macro`. Top-2 "reação" = 30,7%; macro "Falha do condutor" = 81%.
- [x] Frequência de `tipo_acidente` (17). — `frequencia_tipo`. Colisão traseira 19,8% (modal).
- [x] Distribuição de `classificacao_acidente` (77,5% feridos / 15,4% sem vítima / 7,2% fatal / **1 nulo**). — `distribuicao_classificacao`. **Achado:** o nulo (id 652519) tem `mortos == 1`; lacuna de preenchimento, impacto nulo (flags por pessoa são canônicas — ver 2.8). `classificacao_nula` documenta.
- [x] Letalidade por causa e por tipo, **duas unidades lado a lado** (mortos/acidente e mortos/pessoa). — `letalidade_por`. Atropelamento de pedestre (0,118/pessoa) e colisão frontal (0,39/acidente) são o par letal; colisão traseira lidera frequência com letalidade 0,015.
- [x] Achados C1–C5 em `achados-eda.md` (C4 e C5 → Fase 3). — testes em `tests/test_causa_tipo.py` (9).

### Fase 2.4 — Condições da via e ambiente (unidade: acidente) — `src/eda/dimensoes/via_ambiente.py`
- [x] Distribuição de `condicao_metereologica` (1.000 nulos no nível acidente / 2.439 no nível pessoa), `tipo_pista` (3), `uso_solo` (2), `sentido_via` (167 nulos = os `br == 0`). — `distribuicao`.
- [x] `tracado_via` sobre os indicadores `tem_*` da Fase 2.0 (frequência por característica, não por combinação). — `tracado_frequencia`. Reta 73%, curva 18%.
- [x] Taxa de gravidade ao lado da contagem para toda condição. — `gravidade_por_condicao` (letalidade + ferido grave + n_acidentes), `tracado_gravidade` (Δ com vs sem). Figuras contagem × letalidade (eixo duplo).
- [x] Achados V1–V5 em `achados-eda.md` (V2 e V5 → Fase 3). — testes em `tests/test_via_ambiente.py` (9). **Destaques:** céu claro é exposição (chuva é menos letal); pista simples ~2× letal; rural converte ferido em morto; declive/curva agravam, rotatória/interseção aliviam.

### Fase 2.5 — Veículo (unidade: veículo) — `src/eda/dimensoes/veiculo.py`
- [x] **Constância dos atributos dentro de `(id, id_veiculo)`** — `constancia_por_veiculo`: **0 divergências** em tipo/marca/ano. Dedup `por_veiculo` não precisa de desempate.
- [x] Distribuição de `tipo_veiculo` (25, 0 nulos no nível veículo). — `distribuicao_tipo`. Automóvel 32%, Motocicleta 22%, carga pesada 28%.
- [x] Ranking de `marca_normalizada` — **refino I/SR/REB/R + sinônimos feito** em `enrich.split_marca_modelo` (+ `const.MARCA_SINONIMOS`). Top-15 limpo (HONDA, VW, FIAT, CHEVROLET…).
- [x] Idade da frota (`ANO_REFERENCIA − ano`). — `idade_frota`: cobertura 92,6% (10.273 sem ano), mediana 10 anos, p90 21, 24,5% > 15 anos. **Devolutiva → Fase 1:** `ano_fabricacao_veiculo < 1950` (32, quase tudo "1900") → NaN (`normalize_numeric_sentinels`).
- [x] Severidade por tipo de veículo (nível pessoa). — `severidade_por_tipo`. **Moto = 36% dos óbitos** com 22% da frota, letalidade 4,8% (2× auto); **bicicleta 12,7%** (mais letal por pessoa).
- [x] Achados Ve1–Ve5 em `achados-eda.md` (Ve3 e Ve4 → Fase 3). — testes em `tests/test_veiculo.py` (8), `test_etl.py` +1.

### Fase 2.6 — Vítima/pessoa (unidade: pessoa) — `src/eda/dimensoes/vitima.py`
- [x] Distribuição de `idade` (cobertura 82,6%, mediana 38, IIQ 28–50). — `perfil_idade` + `distribuicao_idade.png`.
- [x] Distribuição de `sexo` (63,6% M / 21,5% F / 14,9% nulo) e `tipo_envolvido`. — `distribuicao_sexo`/`distribuicao_tipo_envolvido`.
- [x] Distribuição de severidade (óbito 6.043, ferido grave 20.018, **28.630 sem desfecho** = `estado_fisico` nulo). — `distribuicao_severidade`.
- [x] Letalidade por faixa etária, sexo e `tipo_envolvido` (base: vítimas). — `letalidade_por`. **Achados:** letalidade cresce com idade (60+ 5,1%), ferido grave pica em 18–24 (15,2%); homem 4,0% vs mulher 2,6%; **pedestre 27,1%**.
- [x] **Tratar `Testemunha` explicitamente.** — **Decisão:** `apenas_vitimas()` (`PAPEIS_VITIMA` = Condutor/Passageiro/Pedestre/Cavaleiro) em `src/eda/dataset.py` é a base fixa de toda taxa de severidade. Remove 20.143 não-vítimas; letalidade global 3,10% → 3,46%. `impacto_testemunha` quantifica.
- [x] Achados Vi1–Vi6 em `achados-eda.md` (Vi3 e Vi6 → Fase 3; resíduo de ~8,5k vítimas sem desfecho → 2.8). — testes em `tests/test_vitima.py` (10).

### Fase 2.7 — Condutor (unidade: pessoa, `tipo_envolvido == "Condutor"`) — `src/eda/dimensoes/condutor.py`
- [x] Filtro `apenas_condutores` (`src/eda/dataset.py`) + perfil demográfico dos 122.367. — `perfil`: 88,2% masculino, mediana 40 anos, 402 menores.
- [x] Severidade do condutor **comparada a passageiro e pedestre**, estratificada por faixa etária e sexo. — `letalidade_papel`, `letalidade_condutor_vs_passageiro`. **Achados:** condutor > passageiro **em toda faixa etária** (efeito do papel, não só da população); sexo inverte de sinal por papel (mulher condutora 1,6% — a mais segura), com confundidor motocicleta.
- [x] Investigar veículos sem linha "Condutor" (spec §2.7). — `veiculos_sem_condutor`. **Hipótese de evasão rejeitada:** os 17.150 são exatamente os `tipo_envolvido` nulos e **97% são semirreboque/reboque** (sem condutor próprio). Só **516 motorizados** sobram como candidatos a fuga (fatalidade 11% vs 8,4%).
- [x] Achados Co1–Co4 em `achados-eda.md` (Co2/Co3 → Fase 3; Co4 → corrigir spec §2.7). — testes em `tests/test_condutor.py` (8).

### Fase 2.8 — Consistências e devolutiva para a Fase 1 — `src/eda/dimensoes/consistencia.py`
- [x] `classificacao_acidente` × flags de severidade das pessoas do mesmo `id`. — `classificacao_vs_flags`: **0 divergências** nas 3 classes (só o 1 nulo conhecido). As duas representações concordam.
- [x] `estado_fisico` × flags. — `estado_fisico_vs_flags`: nulo ⟺ sem flag (idêntico), mapeamento 1:1. **Decisão:** flags são a representação canônica; `estado_fisico` é descartável.
- [x] Resíduo de vítimas sem desfecho: 8.487 (4,9%, 94% condutores). — `vitimas_sem_desfecho`. **Decisão:** `apenas_vitimas(com_desfecho=True)` é a base recomendada para a Fase 3 (letalidade 3,46% → 3,64%); a Fase 2 manteve `False` (sem mudança de sinal nas conclusões).
- [x] Revalidar `idade == 0 → NaN`. — `revalidar_idade_zero`: 84,6% sem desfecho + 2.056 condutores impossíveis. **Decisão da Fase 1 mantida.**
- [x] Corrigir `spec.md` §2.7, §3.4, §3.5 — notas "Correção pós-EDA" adicionadas com os valores medidos e as decisões, apontando para `achados-eda.md`.
- [x] Consolidar `achados-eda.md`: 42 achados numerados (T/G/C/V/Ve/Vi/Co/Cn) com unidade e veredito + tabela "Candidatos para a Fase 3" (F3-1 a F3-9) + limitações herdadas. — testes em `tests/test_consistencia.py` (5).

## Bloqueadas
_(vazio — os dois bloqueadores da Fase 1 foram resolvidos por decisão: `idade==0`/`ano==0` → NaN; persistência → parquet.)_
