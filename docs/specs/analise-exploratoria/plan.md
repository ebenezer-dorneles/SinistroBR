# 🗺️ plan.md: Análise exploratória

Mapa metodológico e de execução para o que foi levantado em `spec.md`. Cada fase abaixo tem um critério de saída verificável — não avançar para a próxima sem fechar o anterior (ou registrar explicitamente o que ficou em aberto).

## Fase 0 — Setup do projeto
- Definir stack técnica: Python (pandas), notebook ou script para ETL, biblioteca de dashboard (ex.: Streamlit, Dash, ou Power BI/Looker se for fora do código Python — a decidir).
- Criar estrutura de diretórios do projeto (ex.: `src/etl/`, `src/dashboard/`, `data/raw/`, `data/processed/`).
- **Saída (entregue):** ambiente reprodutível — `requirements.txt` (pandas, pyarrow, matplotlib, pytest), `src/const.py` + `const.md`, layout `src/{const.py,etl,eda}` + `tests/`. Stack do dashboard (Fases 4/5) segue em aberto de propósito.

## Fase 1 — ETL (spec.md §3)
Implementar o pipeline já desenhado na spec:
1. Leitura do CSV com `encoding="latin-1"`, `sep=";"`, `decimal=","`, respeitando aspas (spec §3.1–3.3).
2. Normalização de sentinelas de ausência (`"NA"`, `"Não Informado..."`, `"Ignorado"`, vazio) para `NaN` (spec §3.4).
3. Conversão de tipos: datas, horários, numéricos (spec §3.7 passo 3).
4. Regras de negócio para `idade == 0` e `ano_fabricacao_veiculo == 0` (spec §3.5). **Decidido:** converter ambos para `NaN` (sentinela de "não informado"). A tarefa 2.8 da EDA revalida a decisão de `idade`.
5. Checagem de outliers geográficos (`latitude`/`longitude` fora do Brasil) e de `km`/`br` inconsistentes (spec §3.5).
6. Validação de unicidade por `(id, pesid)` (spec §3.6).
7. Persistência do dataset tratado, separado do bruto (spec §3.7 passo 6).
- **Saída (entregue):** `data/processed/acidentes2025.parquet` + relatório de qualidade de dados (`run_pipeline()` retorna o dict; nulos por coluna, sentinelas convertidos, duplicatas removidas, outliers).

## Fase 2 — Análise exploratória (EDA) por dimensão
Percorrer as dimensões já mapeadas na spec (§2.1–2.7), gerando estatísticas descritivas e visualizações exploratórias (fora do dashboard final, para validar hipóteses).

### Premissa metodológica: unidade de análise
O dataset tratado da Fase 1 tem **194.629 linhas (pessoas)**, **139.517 veículos** (`id_veiculo` não nulo) e **72.529 acidentes** (`id`) — média de 2,68 pessoas por acidente, cobrindo o ano completo de 2025 (01/01 a 31/12). (Números conferidos por `src.eda.checar_denominadores`; a estimativa de 139.518 do spec vinha de parsing ingênuo.)

Atributos de **acidente** (temporal, geográfico, causa, tipo, via, ambiente) estão repetidos em todas as linhas do mesmo acidente. Contar linhas nessas dimensões não mede acidentes, mede pessoas expostas — um acidente de ônibus pesa 40× mais que uma colisão de dois carros. Toda estatística da Fase 2 deve declarar explicitamente sua unidade e usar a deduplicação correspondente:

| Unidade | Como obter | Denominador | Dimensões que a usam |
|---|---|---|---|
| Acidente | `drop_duplicates("id")` | 72.529 | 2.1 temporal, 2.2 geográfico, 2.3 causa/tipo, 2.4 via/ambiente |
| Veículo | `dropna("id_veiculo").drop_duplicates(["id", "id_veiculo"])` | 139.517 | 2.5 veículo |
| Pessoa | linha bruta | 194.629 | 2.6 vítima, 2.7 condutor |

Frequência (nº de acidentes) e severidade (nº de mortos/feridos) vivem em unidades diferentes e nunca devem dividir o mesmo denominador. Quando a mesma dimensão for medida nas duas óticas (ex.: chuva por acidente × mortos por pessoa), reportar as duas lado a lado, rotuladas.

### 2.0 Preparo comum da EDA — **CONCLUÍDA** (`src/eda/`, `src/const.py`, `tests/`)
Passos que a Fase 1 não fez porque são decisões de **análise**, não de qualidade de dado. Ficam num módulo reutilizável para o dashboard da Fase 5 consumir exatamente os mesmos números:
- **Derivações temporais e de perfil** — `enrich.add_temporal_columns` (`mes`, `dia_semana_ord`, `hora`), `enrich.add_faixa_etaria` (bucket próprio para idade nula).
- **`tracado_via` canonicalizado** — `enrich.canonicalize_tracado_via`: 605 combinações → `tracado_via_canon` (conjunto ordenado) + 12 indicadores `tem_*`.
- **`marca` → `marca_normalizada` + `modelo`** — `enrich.split_marca_modelo` (split simples antes da `/`; prefixos I/SR/REB ficam para a Fase 2.5).
- **`causa_acidente` (69) → `causa_macro` (5)** — `enrich.add_causa_macro`, mapa em `const.CAUSA_MACRO`, causa original preservada. Cinco macros: condutor / via-ambiente / veículo / **pedestre** / outros (pedestre separada de "outros" por ser analiticamente distinta).
- **Métricas de severidade** — `severity.py`: taxa de letalidade e de ferido grave por pessoa, mortos por acidente, `resumo_severidade(df, por=...)`.
- **Recortes por unidade** — `dataset.por_acidente`/`por_veiculo`/`por_pessoa` + `checar_denominadores`.
- **Biblioteca de visualização: matplotlib** — decisão local da Fase 2 (única madura no ambiente; não pré-julga a stack do dashboard das Fases 4/5).

### Dimensões
- **2.1 Temporal** *(unidade: acidente)* — **CONCLUÍDA** (`src/eda/dimensoes/temporal.py`, achados T1–T6). Distribuição por mês/dia/hora, matriz dia×hora, `fase_dia` normalizada pela exposição via P(fase|hora). Achado central: o predomínio de "pleno dia" é em parte exposição; risco/hora pico ao anoitecer, letalidade pico à noite/amanhecer. T4 (madrugada de fim de semana) e T6 (letalidade noturna) → Fase 3.
- **2.2 Geográfico** *(unidade: acidente)* — **CONCLUÍDA** (`src/eda/dimensoes/geografico.py`, achados G1–G7). Rankings UF/BR/município, concentração por trecho `(br, km)`, mapa hexbin de densidade, recorte operacional PRF. Confirmado: 0 nulos/outliers de lat-long (spec §3.4 errado). Achados: BR-101+116 = 33% dos acidentes; 623 trechos concentram ~30% dos casos localizados (G6 → Fase 3); `regional`/`delegacia`/`uop` ficam fora do dashboard geral. `br == 0` (167) foi para o ETL. Rankings medem volume, não risco (sem denominador de frota/malha).
- **2.3 Causa e tipo do acidente** *(unidade: acidente)* — **CONCLUÍDA** (`src/eda/dimensoes/causa_tipo.py`, achados C1–C5). Frequência de causa (bruta/macro), tipo e classificação; letalidade por causa e tipo nas duas unidades. Achados: 81% "Falha do condutor" (mas `causa` é atribuição subjetiva do BO); colisão traseira é o tipo modal e pouco letal, atropelamento de pedestre + colisão frontal são o par letal; 1 `classificacao_acidente` nula com óbito (documentada, não corrigida). C4/C5 → Fase 3.
- **2.4 Condições da via e ambiente** *(unidade: acidente)* — **CONCLUÍDA** (`src/eda/dimensoes/via_ambiente.py`, achados V1–V5). `condicao_metereologica`, `tipo_pista`, `uso_solo`, `sentido_via`, `tracado_via` canonicalizado — sempre com taxa de gravidade ao lado da contagem. Achados: céu claro é exposição (chuva é menos letal, só neblina agrava); pista simples ~2× letal; rural converte ferido em morto; declive/curva agravam, rotatória/interseção aliviam. V2/V5 → Fase 3.
- **2.5 Veículo** *(unidade: veículo)* — **CONCLUÍDA** (`src/eda/dimensoes/veiculo.py`, achados Ve1–Ve5). `tipo_veiculo`, `marca_normalizada` (refino I/SR/REB/R + sinônimos feito aqui), idade da frota, severidade por tipo; constância dos atributos dentro do veículo validada (0 divergências). Achados: moto = 22% da frota / 36% dos óbitos (2× a letalidade do automóvel); bicicleta a mais letal por pessoa (12,7%); frota com mediana 10 anos. `ano_fabricacao < 1950` (32) foi para o ETL. Ve3/Ve4 → Fase 3.
- **2.6 Vítima/pessoa** *(unidade: pessoa)* — **CONCLUÍDA** (`src/eda/dimensoes/vitima.py`, achados Vi1–Vi6). Perfil (`idade`/`sexo`/`tipo_envolvido`), severidade, letalidade por faixa/sexo/papel. **Decisão metodológica:** `apenas_vitimas()` (exclui Testemunha e `tipo_envolvido` nulo) é a base fixa de toda taxa de severidade. Achados: letalidade cresce com idade, ferido grave pica em 18–24; homem 4,0% vs mulher 2,6%; pedestre 27,1%; `estado_fisico` nulo ⟺ sem flag de severidade (28.630, antecipa a 2.8). Vi3/Vi6 → Fase 3.
- **2.7 Condutor** *(unidade: pessoa, filtrada)* — **CONCLUÍDA** (`src/eda/dimensoes/condutor.py`, achados Co1–Co4). Perfil (88% masculino, mediana 40) e severidade comparada a passageiro/pedestre, estratificada. Achados: condutor > passageiro em toda faixa etária (efeito do papel); sexo inverte por papel (mulher condutora a mais segura — confundidor moto); os 17.150 "veículos sem condutor" são 97% reboque/semirreboque, não evasão (spec §2.7 a corrigir). Co2/Co3 → Fase 3.
- **2.8 Consistências e devolutiva para a Fase 1** — **CONCLUÍDA** (`src/eda/dimensoes/consistencia.py`, achados Cn1–Cn4). `classificacao_acidente` e `estado_fisico` são consistentes/redundantes com as flags (EDA usa as flags); decisão `idade == 0 → NaN` revalidada; base recomendada para modelagem = `apenas_vitimas(com_desfecho=True)`. `spec.md` §2.7/§3.4/§3.5 corrigido com notas "pós-EDA".
- **Saída (entregue):** 8 scripts em `src/eda/dimensoes/` (figuras em `reports/figuras/`) + `achados-eda.md` com 42 achados numerados e a tabela de candidatos F3-1…F3-9. **Fase 2 fechada.**

**Relação com a Fase 1:** a EDA consome `run_pipeline(persist_output=False)` em memória (ou lê `data/processed/acidentes2025.parquet`). Os sentinelas `idade == 0` (33.685) e `ano_fabricacao_veiculo == 0` (17.394) já saem como `NaN` do ETL; a tarefa 2.8 cruza esses casos com `tipo_envolvido`/`estado_fisico` para revalidar a decisão e, se houver sinal forte de idades reais, reabri-la.

## Fase 3 — Cruzamentos e hipóteses (spec.md §2.8)

Testar os seis cruzamentos da spec §2.8 e os nove candidatos maduros da Fase 2
(`achados-eda.md`, F3-1…F3-9). A Fase 2 descreveu **uma dimensão de cada vez**; a
Fase 3 cruza dimensões e, principalmente, **separa efeito de confundidor** — vários
achados da Fase 2 são explicitamente suspeitos de composição (Co3/moto, T5/exposição,
V3/velocidade rural).

### Premissa 1 — toda taxa desta fase é condicional ao acidente

O dataset só contém pessoas **já envolvidas** em acidente. Não há denominador de
exposição (frota, km rodados, contagem de tráfego). Portanto:

| Pergunta | Mensurável? | Forma testável |
| :-- | :-- | :-- |
| P(morte \| envolvido no acidente) | **sim** | fator de **severidade** |
| P(acidente \| exposição) | **não** | vira "sobre-representação no volume", nunca risco |

**Regra:** nenhuma hipótese entra na fase escrita como "X causa mais acidentes".
Antes de rodar, cada uma é reescrita em uma das duas formas acima. Herda as
limitações de denominador já registradas (G3, G4, Ve5). Única exposição disponível
é a temporal (P(fase|hora), Fase 2.1) — e mesmo ela não dá acidentes por veículo-km.

### Premissa 2 — com n = 194 mil, decide-se por tamanho de efeito, não por p-valor

Qualquer diferença é "estatisticamente significante" nesse volume. Regra de veredito
fixada **antes** de rodar (limiares em `const.py`, tarefa 3.0):

- `MIN_N_CELULA = 100` pessoas por célula — abaixo disso o veredito é
  `inconclusivo (n)`, que **não** é sinônimo de `sem sinal`;
- todo efeito reportado como **Δ pontos percentuais _e_ razão de risco (RR)**, com
  IC 95% (Wilson para a taxa, log de Katz para o RR);
- `confirmado` exige `Δ ≥ MIN_DELTA_PP (1,0 pp)` **e** `RR ≥ MIN_RR (1,20)` **e** IC
  do RR sem cruzar 1;
- veredito novo da Fase 3: **`confundido`** — o efeito bruto existe e desaparece (ou
  inverte) depois do ajuste. É resultado publicável, não descarte.

### Premissa 3 — ajuste por confundidor é obrigatório, não opcional

F3-8 (gradiente etário) **não é hipótese, é controle**. Toda comparação de severidade
é ajustada por, no mínimo, **idade** e **tipo de veículo** (moto), mais
`tipo_envolvido` quando o papel varia entre os grupos comparados.

- **Método padrão (pandas puro):** tabela estratificada + **padronização direta**,
  usando a distribuição de vítimas do dataset inteiro como população-padrão.
- **Método de exceção:** regressão logística, **só** se a estratificação estourar as
  células (`< MIN_N_CELULA`) em alguma hipótese. Nesse caso `statsmodels` entra no
  `requirements.txt` como dependência condicional, justificada na tarefa que a
  exigiu. **Decisão:** não adotar por antecipação — a estratificação cobre o
  desenho da maioria das hipóteses e mantém o número reproduzível no dashboard.

**Base fixa de severidade:** `apenas_vitimas(com_desfecho=True)` (decisão Cn3). Toda
tabela declara sua base e seu n, como a Fase 2 declarava sua unidade.

### O que o dataset não tem (limite duro do que a Fase 3 pode concluir)

Levantado no planejamento, contra as 35 colunas reais do CSV:

- **Sem `velocidade` medida.** A nota "modelar com `velocidade`" em F3-5/F3-7 não é
  executável. Proxy possível: causa `"Velocidade Incompatível"` (4.088 acidentes) —
  atribuição subjetiva do agente (C1), usar como indício, nunca como medida.
- **Sem alcoolemia, cinto ou capacete.** `"Ingestão de álcool pelo condutor"` (3.685
  acidentes) + psicoativas (62) só é registrado quando testado/evidente: é **piso**
  de prevalência, não prevalência. Comparações com álcool são de composição relativa.
- **Sem frota, malha ou tráfego** → nenhum ranking geográfico ou por categoria vira
  taxa de risco.
- **Sem tempo de socorro / distância a hospital** — mediador não observado por trás
  de V3 (rural mata mais) e T6 (noite mata mais). A Fase 3 pode medir o efeito, não
  atribuir o mecanismo.
- **Anonimizado e de um único ano** — sem histórico por pessoa, sem série temporal
  para tendência; sazonalidade (T1) é de um ano só.

Essas limitações vão para o dashboard (Fase 6) como texto, não são para contornar.

### Sub-fases

- **3.0 Preparo comum de inferência** — `src/eda/inferencia.py`: taxa com IC de
  Wilson, RR com IC, `tabela_estratificada`, `padronizacao_direta`, `veredito()`
  aplicando a regra da Premissa 2. Limiares novos em `src/const.py`/`const.md`.
  Figuras em `reports/figuras/hipoteses/`.
- **3.1 Pedestre e atropelamento** (F3-2; spec §2.8 D/B) — H1–H4.
- **3.2 Motocicleta, sexo e papel** (F3-3, Co2, Co3, F3-9; spec D/F) — H5–H9.
- **3.3 Tempo: noite, madrugada e álcool** (F3-4 + F3-6; spec B/E) — H10–H13.
- **3.4 Via, ambiente e infraestrutura** (F3-5, F3-7 + spec A) — H14–H16.
- **3.5 Pontos negros** (F3-1; spec C) — H17–H19 + `reports/pontos_negros.csv`.
- **3.6 Consolidação e handoff** — `resultados-fase3.md` + tabela de corte para a
  Fase 4 + devolutiva para `spec.md` §2.8 e `achados-eda.md`.

Hipóteses detalhadas, uma tarefa cada, em `task.md`.

- **Saída (entregue):** `resultados-fase3.md` com H1…H19 (unidade, base e n, efeito
  bruto, efeito ajustado, IC, veredito) + a tabela "vira gráfico × sem sinal" para a
  Fase 4 + entregável `reports/pontos_negros.csv` (382 trechos). Os 6 cruzamentos da
  spec §2.8 e os 9 candidatos F3-x têm veredito. Módulos em `src/eda/hipoteses/`
  (`pedestre`, `moto_perfil`, `tempo`, `via`, `pontos_negros`) + `src/eda/inferencia.py`,
  com testes. **Fase 3 fechada.**
  - **Placar (H1–H19, contando H15 e H16 como divididas):** ~15 `confirmado` (H3 só
    na escala absoluta; H9 exploratório; H15-declive e H16-nevoeiro isolados),
    2 `sem sinal` (H8; H16 3-way), 1 `confundido` (H15-curva), 1 `rejeitado` (H7).
    Nenhum `inconclusivo (n)` — a estratificação não estourou as células e
    `statsmodels` **não** foi necessário (Premissa 3 confirmada).
  - **Devolutiva estrutural:** a chave de trecho `(br, km)` de G6 não é única entre
    UFs → `(uf, br, km)`, 382 trechos e não 623. `geografico.py` a corrigir.

## Fase 4 — Definição do dashboard
- A partir dos achados da Fase 2 e 3, definir as perguntas de negócio prioritárias e os gráficos correspondentes (item pendente em spec §4).
- Definir granularidade das visualizações: nacional, por UF, por BR (item pendente em spec §4).
- Desenhar o layout/wireframe do dashboard (filtros, KPIs no topo, gráficos por dimensão).
- **Saída:** wireframe aprovado + lista fechada de gráficos/KPIs a implementar.

## Fase 5 — Implementação do dashboard
- Implementar os gráficos/KPIs definidos na Fase 4 sobre o dataset processado da Fase 1.
- **Saída:** dashboard funcional rodando localmente.

## Fase 6 — Validação e entrega
- Revisar consistência dos números do dashboard contra a EDA (Fase 2/3).
- Documentar limitações conhecidas (dado anonimizado, sentinelas tratadas, etc. — já listadas em spec §2.7 e §3).
- **Saída:** dashboard entregue/publicado.

---

## Hipóteses da spec × onde são testadas

Cada cruzamento da spec §2.8 tem uma sub-fase dona e hipóteses nomeadas — nenhum
pode fechar a Fase 3 sem veredito registrado em `resultados-fase3.md`.

| Hipótese / cruzamento (spec §2.8) | Sub-fase | Hipóteses | Candidato F3 de origem |
|---|---|---|---|
| Causa × condição meteorológica × gravidade | 3.4 | H16 | *(nenhum — V1 sugere `sem sinal`; testar formalmente mesmo assim)* |
| Horário × tipo de acidente × mortes | 3.3 | H11, H13 | F3-4 |
| BR/km × classificação do acidente (pontos negros) | 3.5 | H17–H19 | F3-1 |
| Idade/sexo × tipo de veículo × estado físico | 3.2 (+3.1) | H5–H7, H1 | F3-3, F3-2, Ve4 |
| Dia da semana × fase do dia × tipo de acidente | 3.3 | H10, H12 | F3-6 |
| Perfil do condutor × causa do acidente × gravidade | 3.2 | H8, H9 | Co2, Co3, F3-9 |
| *(controle transversal, não hipótese)* | 3.0 | — | F3-8 |
| *(infra: pista simples × frontal; geometria)* | 3.4 | H14, H15 | F3-5, F3-7 |

## Bloqueadores conhecidos
- ~~Regra de negócio para `idade == 0` / `ano_fabricacao_veiculo == 0`~~ — **resolvido** (ambos → `NaN`; revalidado na 2.8/Cn4).
- ~~Formato de persistência do dataset processado~~ — **resolvido**: parquet (`data/processed/acidentes2025.parquet`).
- ~~`const.md` não existe~~ — **resolvido** na Fase 2.0.
- Escolha da stack de dashboard ainda em aberto — **não bloqueia a Fase 3** (matplotlib segue como biblioteca de EDA). Decisão precisa sair **na Fase 4**, junto do wireframe, porque a Fase 5 depende dela.
- Dependência condicional de `statsmodels` (regressão logística) — só entra se alguma hipótese da Fase 3 estourar as células na estratificação (ver Premissa 3). Enquanto não estourar, não é bloqueador nem dependência.
- **Não bloqueia, mas restringe conclusões:** ausência de `velocidade`, alcoolemia, cinto/capacete, frota/malha/tráfego e tempo de socorro (ver "O que o dataset não tem"). Nenhum desses é obtenível dentro do escopo atual; a Fase 3 conclui sobre severidade condicional, não sobre causa-raiz.
