# 🧪 resultados-fase3.md: Cruzamentos e hipóteses

Resultado da Fase 3 (`plan.md` §Fase 3). Uma linha por hipótese H1–H19, preenchida
incrementalmente à medida que cada sub-fase roda. O "não deu" é entregável: toda
hipótese fecha com veredito **e número**, inclusive `sem sinal`.

Reproduzir: `python -m src.eda.hipoteses.<modulo>` (figuras em `reports/figuras/hipoteses/`).

## Regra de veredito (fixada antes de rodar — `plan.md` Premissa 2)

- Base fixa de severidade: `apenas_vitimas(com_desfecho=True)` — 165.999 vítimas,
  letalidade global **3,64%** (Cn3).
- Efeito reportado como **Δ pontos percentuais _e_ razão de risco (RR)**, com IC 95%
  (Wilson para a taxa, log de Katz para o RR). Nunca por p-valor.
- Ajuste obrigatório por **idade** e **tipo de veículo** (+ `tipo_envolvido` quando o
  papel varia) — estratificação + padronização direta (`src/eda/inferencia.py`).
- Limiares (`src/const.py`): `MIN_N_CELULA=100`, `MIN_DELTA_PP=1.0`, `MIN_RR=1.20`,
  `NIVEL_CONFIANCA=0.95`.

| Veredito | Significado |
| :-- | :-- |
| `confirmado` | `|Δ| ≥ 1,0 pp` **e** `RR ≥ 1,20` (ou `≤ 0,83`) **e** IC do RR não cruza 1 |
| `rejeitado` | o efeito esperado pela hipótese não se sustenta |
| `sem sinal` | testado formalmente, nenhum efeito relevante (com número) |
| `confundido` | efeito bruto existe e some/inverte após o ajuste |
| `inconclusivo (n)` | célula-chave com `n < MIN_N_CELULA` |

---

## Tabela-mestre (unidade · base e n · efeito bruto · efeito ajustado · IC · veredito)

| H | Sub-fase | Pergunta | Unidade / base / n | Efeito bruto | Efeito ajustado | Veredito |
| :-- | :-- | :-- | :-- | :-- | :-- | :-- |
| H1 | 3.1 | Letalidade do pedestre (27%) sobrevive ao ajuste por idade? | pessoa · vítima c/ desfecho · 165.965 (3.245 pedestres) | 27,7% vs 3,2% · Δ 24,5 pp · RR 8,76 [8,24–9,32] | Δ 22,0 pp (padronizado por faixa etária) | **confirmado** |
| H2 | 3.1 | Atropelamento é mais letal ao anoitecer/noite? | pessoa · vítimas em atropelamento · 8.444 | noite/amanhecer 14,1% vs resto 7,4% · Δ 6,8 pp · RR 1,92 [1,66–2,21] | Δ 6,7 pp (padronizado por idade) | **confirmado** |
| H3 | 3.1 | "Rural converte ferido em morto" é mais forte no pedestre? (interação) | pessoa · pedestres 3.245 / ocupantes 162.720 | pedestre Δ 15,3 pp (RR 1,71); ocupante Δ 2,5 pp (RR 2,50) | interação: absoluto 6× maior no pedestre; relativo maior no ocupante | **confirmado** (escala absoluta) |
| H4 | 3.1 | Perfil etário/sexo da vítima-pedestre vs. demais vítimas | pessoa · 3.245 pedestres | 60+ = 18,9% vs 10,8%; 45+ = 42% vs 34%; sexo idêntico (~75% M) | — (perfil, sem ajuste) | **confirmado** (skew p/ idoso; não é cluster puro de idosos) |
| H5 | 3.2 | A inversão do sexo por papel (Co3) some ao estratificar por tipo de veículo? | pessoa · ocupantes (condutor+passageiro) c/ desfecho · 162.720 | ♀ condutora 1,6% < ♀ passageira 2,6%; ♂ condutor 3,6% > ♂ passageiro 2,6% | após padronizar por idade **e** tipo de veículo: ♀ 1,4% vs 2,6%; ♂ 3,6% vs 3,3% — inversão persiste | **confirmado** (não é confundido pela moto) |
| H6 | 3.2 | Letalidade 2× da moto sobrevive ao ajuste por idade e papel? | pessoa · condutores de moto (30.129) e auto (40.725) | moto 5,4% vs auto 2,4% · Δ 3,0 pp · RR 2,23 [2,06–2,41] | padronizado por idade+sexo: moto 5,7% vs auto 2,5% · Δ 3,3 pp (cresce) | **confirmado** |
| H7 | 3.2 | "Vulnerável sem carroceria" é um grupo coerente? | pessoa · 42.653 vulneráveis | agregado 7,0%, mas pedestre 27,7% / bicicleta 13,2% / ciclomotor 7,8% / moto 4,9% | — (riscos de ordens diferentes: pedestre = 5,6× a moto) | **rejeitado** (não colapsar num recorte único) |
| H8 | 3.2 | Perfil do condutor × causa (álcool/velocidade no jovem?) | pessoa · condutores c/ desfecho · 114.392 | "Velocidade Incompatível" +3,4 pp de share <30a; "álcool" **−2,5 pp** (mediana 40a); "dormindo" −3,5 pp | — (causa é atribuição do BO, C1) | **sem sinal** (álcool até skew p/ mais velho) |
| H9 | 3.2 | Caracterizar os ~530 veículos motorizados sem condutor | veículo · 530 · acidente | acidentes desses veículos: 15,2% fatais vs 7,2% base (2,1×) | 87% rural, hora mediana 10h, majoritariamente automóvel/moto/caminhonete | **confirmado** (exploratório — mecanismo evasão vs. registro faltante não identificável) |
| H10 | 3.3 | Madrugada de sexta/sábado tem mais álcool na composição de causas? | acidente · madrugada (0–4h) de sex–dom · 3.898 | "álcool" em 15,1% vs 4,5% no resto (razão 3,4×); "dormindo" 3,3× | — (composição, não taxa; álcool é sub-registrado — piso) | **confirmado** |
| H11 | 3.3 | Letalidade noturna (T6) sobrevive ao ajuste por tipo de acidente e uso do solo? | pessoa · vítimas c/ desfecho · 165.999 | noite 5,3% vs dia 2,5% · Δ 2,87 pp | padronizado por tipo de acidente + uso do solo: 4,5% vs 2,9% · Δ **1,69 pp** | **confirmado** (~40% da diferença é composição) |
| H12 | 3.3 | Dia da semana × fase do dia × tipo de acidente (matriz de composição) | acidente · FDS-noite vs segunda-dia | FDS-noite: "saída de leito" 17,2% (perda de controle); segunda-dia: "colisão traseira" 22,7% (congestionamento) | — (composição) | **confirmado** |
| H13 | 3.3 | Horário × tipo de acidente × mortes (mortos/acidente vs mortos/pessoa) | pessoa · 194.629 | frontal 0,39 mortos/acidente (maior); atropelamento 0,118 mortos/pessoa (maior); ambos ~2× seu share nas janelas 0–5h e 18–23h | — (descritivo; as duas unidades discordam, C4) | **confirmado** |
| H14 | 3.4 | Letalidade 2× da pista simples é explicada pela colisão frontal? | pessoa · vítimas c/ desfecho · 165.999 | simples 4,9% vs resto 2,3% · Δ 2,62 pp · RR 2,13 [2,02–2,25] | padronizado por tipo de acidente: Δ 1,56 pp; **dentro da frontal**: simples 12,6% vs dupla 6,1% | **confirmado** (dois caminhos) |
| H15 | 3.4 | Geometria (declive/curva) agrava após ajuste por tipo de pista e uso do solo? | pessoa · 165.999 | declive Δ 1,60 pp; curva Δ 1,36 pp | ajustado por pista+solo: **declive Δ 1,15 pp** (RR 1,46); **curva Δ 0,73 pp** | declive **confirmado** / curva **confundido** |
| H16 | 3.4 | Causa × condição meteorológica × gravidade (3-way) | pessoa · 165.999 | meteorologia quase plana; só Nevoeiro/Neblina (n=1.300) acima: 5,7% vs 3,7%; chuva −0,55 pp | 3-way sem interação causa-específica; Nevoeiro ajustado Δ 1,34 pp (RR 1,57) | 3-way **sem sinal**; Nevoeiro/Neblina isolado **confirmado** |
| H17 | 3.5 | Os trechos negros são estáveis entre semestres? | acidente · trechos `(uf, br, km)` com ≥20/ano · **382** (não 623 — ver devolutiva) | 382/382 presentes nos dois semestres; 377/382 com ≥5 em ambos | correlação de postos entre os negros = 0,19 (ranking fino é ruído) | **confirmado** (conjunto estável, ranking não) |
| H18 | 3.5 | Trecho negro tem assinatura de via própria? | acidente · 382 trechos negros vs base | 78,5% urbano (razão 2,2); 86% pista dupla/múltipla; "colisão traseira" 28% + "lateral mesmo sentido" 22%; quase 0 "saída de leito" | — (caracterização) | **confirmado** (perfil de congestionamento urbano/multipista) |
| H19 | 3.5 | Concentração de volume ≠ concentração de mortes (interseção das listas) | trecho `(uf, br, km)` | top-50 por acidentes ∩ top-50 por mortos = **1**; trecho de maior volume (SC BR-101 km 208, 82 acid.) tem 0 mortos; maior letalidade = evento único (PE BR-423 km 127: 1 acidente, 16 mortos) | — | **confirmado** (dois mapas, não um) |

---

## 3.1 — Pedestre e atropelamento (`src/eda/hipoteses/pedestre.py`)

Figuras: `reports/figuras/hipoteses/pedestre/`.

- **H1 — `confirmado`.** A letalidade do pedestre (27,7%) é ~8,8× a do ocupante de
  veículo (3,2%). O pedestre vítima é de fato mais velho (mediana 45 vs 38), mas o
  ajuste por faixa etária derruba o Δ só de 24,5 pp para 22,0 pp — a idade explica
  ~10% da diferença; o resto é a exposição física do corpo. É o achado mais forte
  da fase em magnitude.
- **H2 — `confirmado`.** Atropelamento em plena noite (14,0%) e ao amanhecer (16,2%)
  mata ~2× mais que em pleno dia (7,3%). O anoitecer é a exceção (8,0%, n=465) —
  ainda há tráfego e o pedestre é visto. O ajuste por idade não muda o Δ (6,8→6,7 pp).
  Mecanismo candidato: visibilidade — mas **não há coluna de iluminação**, é indício.
- **H3 — `confirmado` na escala absoluta, `rejeitado` na relativa.** O meio rural
  adiciona **15,3 pp** de letalidade ao pedestre e só **2,5 pp** ao ocupante — a
  penalidade absoluta do campo é 6× maior para quem anda a pé. Mas o *risco
  relativo* rural é maior para o ocupante (RR 2,50 vs 1,71), porque a base urbana do
  pedestre já é altíssima. Para política pública (número de mortos evitáveis) vale a
  escala absoluta: **pedestre em rodovia rural é a pior combinação do dataset**.
- **H4 — `confirmado` (parcial).** A vítima-pedestre não é um cluster puro de idosos,
  mas o skew é claro: 60+ representa **18,9%** dos pedestres contra 10,8% das demais
  vítimas (quase o dobro), e 45+ soma 42% vs 34%. Sexo é idêntico ao das demais
  vítimas (~75% masculino). Também: 16,6% dos pedestres têm idade "Não informado"
  (vs 2,9%) — subidentificação do atropelado. Insumo de campanha: faixa de travessia
  e tempo de semáforo calibrados para o pedestre idoso, em trecho rural/periurbano.

---

## 3.2 — Motocicleta, sexo e papel (`src/eda/hipoteses/moto_perfil.py`)

Figuras: `reports/figuras/hipoteses/moto_perfil/`.

- **H5 — `confirmado`. É o achado mais forte da fase em termos de confundimento
  controlado.** A Fase 2 (Co3) suspeitou que "mulher condutora é a mais segura"
  fosse artefato da moto (frota 92,5% masculina). Não é: padronizando por idade
  **e** tipo de veículo, a mulher condutora (1,4%) continua abaixo da mulher
  passageira (2,6%), e o homem condutor (3,6%) continua acima do homem passageiro
  (3,3%). O papel de condutor **protege a mulher e não protege o homem** — sinal
  que sobrevive ao ajuste. A moto é confundidor *parcial* (infla a taxa bruta
  masculina), não a explicação. Mecanismo (exposição a risco, velocidade) não é
  observável no dataset.
- **H6 — `confirmado`.** A letalidade 2× da moto não é composição: condutor de moto
  5,4% vs condutor de auto 2,4% (RR 2,23), e o Δ **cresce** de 3,0 para 3,3 pp após
  padronizar por idade e sexo — o motociclista é mais jovem, então ajustar remove um
  desconto etário que estava mascarando parte do efeito.
- **H7 — `rejeitado`.** "Vulnerável sem carroceria" não é uma categoria: no grupo
  agregado a letalidade é 7,0%, mas os componentes variam de 4,9% (moto) a 27,7%
  (pedestre) — um fator 5,6. Bicicleta (13,2%) é 2,7× a moto. **Decisão para o
  dashboard:** manter os quatro separados; pedestre e bicicleta merecem destaque
  próprio, não diluídos numa média de "vulneráveis".
- **H8 — `sem sinal`.** A hipótese "álcool e velocidade concentram no condutor
  jovem" não se sustenta com a `causa` do BO: "Velocidade Incompatível" tem só
  +3,4 pp de participação de condutores <30 anos, e "Ingestão de álcool" tem
  **−2,5 pp** (mediana de idade 40). "Condutor Dormindo" skew para mais velho
  (−3,5 pp). Ressalva C1: `causa` é atribuição subjetiva do agente, não medição —
  o resultado pode ser tanto do comportamento real quanto do viés de registro.
- **H9 — `confirmado` (exploratório).** Os 530 veículos motorizados sem linha de
  condutor (após excluir reboques, Co4) estão em acidentes com letalidade 15,2% vs
  7,2% na base — 2,1×. São 87% rurais, hora mediana 10h, majoritariamente automóvel,
  moto e caminhonete. O padrão é compatível com **evasão de acidente grave**, mas o
  dataset não permite separar isso de "condutor morto/removido antes do registro".
  n = 530 é suficiente para a taxa; a limitação é de interpretação, não de amostra.

---

## 3.3 — Tempo: noite, madrugada e álcool (`src/eda/hipoteses/tempo.py`)

Figuras: `reports/figuras/hipoteses/tempo/`.

- **H10 — `confirmado`.** Na madrugada (0h–4h) de sexta a domingo, "Ingestão de
  álcool pelo condutor" aparece em **15,1%** dos acidentes, contra 4,5% no resto da
  semana — 3,4×. "Condutor Dormindo" sobe na mesma proporção (8,6% vs 2,6%). É
  composição de causa, não taxa de severidade. **O número é piso**: álcool só entra
  no BO quando testado ou evidente — a participação real é maior.
- **H11 — `confirmado`, mas ~40% da diferença bruta é composição.** A letalidade
  noturna (5,3%) é 2,1× a diurna (2,5%). Padronizando por `tipo_acidente` e
  `uso_solo`, o Δ cai de 2,87 pp para **1,69 pp** — parte do excesso noturno é a
  noite concentrar colisão frontal e trecho rural (H12/H13). Mas sobra 1,7 pp de
  efeito próprio. **Decisão para o dashboard:** "noite" vira **alerta** (o efeito
  residual é real), e a parte compositiva remete às recomendações de pista simples
  (H14) e rural. O amanhecer é a pior fase isolada (6,3%).
- **H12 — `confirmado`.** O acidente do fim de semana à noite é qualitativamente
  outro: "Saída de leito carroçável" (17,2%) — veículo único, perda de controle — é
  o tipo modal, com "colisão com objeto" (10,8%) e frontal (9,7%) acima do normal.
  Na segunda de manhã domina "Colisão traseira" (22,7%) — congestionamento. O filtro
  temporal do dashboard muda o *tipo* de acidente, não só o volume.
- **H13 — `confirmado`.** Reconfirma C4: colisão frontal mata mais **por acidente**
  (0,39 — envolve ~3,8 pessoas), atropelamento mata mais **por pessoa** (0,118). Os
  dois tipos letais praticamente dobram sua participação nas janelas 0h–5h e
  18h–23h em relação ao meio-dia — a mistura letal migra para a noite, o que
  alimenta o efeito residual de H11. Levar as duas curvas (mortos/acidente e
  mortos/pessoa) para o dashboard, rotuladas.

---

## 3.4 — Via, ambiente e infraestrutura (`src/eda/hipoteses/via.py`)

Figuras: `reports/figuras/hipoteses/via/`.

- **H14 — `confirmado`, pelos dois caminhos.** A pista simples é 2,1× mais letal
  (4,9% vs 2,3%). ~40% disso é composição — a colisão frontal é 16,8% dos acidentes
  em pista simples contra 1,6% em pista dividida —, mas **dentro da própria colisão
  frontal** a pista simples ainda mata o dobro (12,6% vs 6,1% em pista dupla). O
  mesmo vale para traseira, saída de leito e tombamento. A barreira central se
  justifica tanto por eliminar frontais quanto por reduzir a energia de cada
  frontal remanescente. Δ ajustado por tipo de acidente = 1,56 pp.
- **H15 — declive `confirmado`, curva `confundido`.** Depois de ajustar por
  `tipo_pista` e `uso_solo`, o declive mantém +1,15 pp de letalidade (RR 1,46) — a
  perda de controle em rampa é efeito próprio. A curva cai para +0,73 pp, abaixo do
  limiar: o excesso de letalidade em curva era, em boa parte, curva coincidir com
  pista simples e trecho rural. Aclive e ponte também não sobrevivem. A interação
  com a causa "Velocidade Incompatível" (proxy, C1) é aproximadamente aditiva:
  declive sem o proxy 4,9% / com 6,9%; sem declive 3,4% / 5,3%.
- **H16 — 3-way `sem sinal`; Nevoeiro/Neblina isolado `confirmado`.** Não há
  interação causa × meteorologia: a condição do tempo desloca a letalidade de forma
  aproximadamente uniforme entre as macro-causas. O único efeito real é o
  Nevoeiro/Neblina (n=1.300): 5,7% bruto, Δ ajustado por tipo de acidente e uso do
  solo = 1,34 pp (RR 1,57 [1,26–1,96]). **Chuva é levemente protetora** (Δ −0,55 pp)
  — confirma V1: o que mata é a perda de visibilidade, não o pavimento molhado. É a
  metade "sem sinal com número" da entrega da fase.

---

## 3.5 — Pontos negros (`src/eda/hipoteses/pontos_negros.py`)

Figuras: `reports/figuras/hipoteses/pontos_negros/`. Entregável: `reports/pontos_negros.csv` (382 linhas).

- **Devolutiva (→ G6 / `geografico.py`):** a chave de trecho `(br, km)` da Fase 2.2
  **não é única entre UFs** — a BR-101 passa por 12 estados, e o km 208 existe em
  todos. 508 dos 623 "trechos negros" de G6 misturavam acidentes de estados
  diferentes no mesmo `(br, km)`. Com a chave correta `(uf, br, km)` são **382**
  trechos com ≥20 acidentes/ano, não 623. O CSV e todas as figuras da 3.5 usam a
  chave corrigida.
- **H17 — `confirmado` como conjunto, não como ranking.** Todos os 382 trechos
  negros aparecem nos dois semestres; 377 têm ≥5 acidentes em cada metade — o
  *conjunto* é altamente estável. Mas a correlação de postos entre eles é só 0,19:
  qual é o "pior" trecho é ruído de Poisson (n ~10–40 por semestre). **Decisão para
  o dashboard:** janela anual (não trimestral), e apresentar o conjunto com uma
  faixa, não um top-N ordenado com precisão falsa.
- **H18 — `confirmado`.** O trecho negro tem assinatura nítida: **78,5% urbano**
  (2,2× a base), **86% pista dupla ou múltipla**, dominado por colisão traseira
  (28%) e colisão lateral no mesmo sentido (22%) — perfil de **congestionamento**.
  Quase não há "saída de leito carroçável" (3,5% vs 16% na base). O cluster BR-101
  km 205–208 é São José/SC (região metropolitana de Florianópolis): 300 acidentes,
  85% urbano, 75% pista múltipla, letalidade quase nula.
- **H19 — `confirmado`. É a decisão de produto mais forte da sub-fase.** A
  concentração de **volume** e a de **mortes** são quase ortogonais: das 50 piores
  por acidentes e das 50 piores por mortos, só **1** trecho coincide. O trecho de
  maior volume (SC BR-101 km 208, 82 acidentes) teve 0 mortos no ano; os trechos de
  maior letalidade são eventos únicos catastróficos (PE BR-423 km 127: 1 acidente,
  16 mortos — ônibus). **O dashboard precisa de dois mapas**: um de frequência de
  acidentes (congestionamento urbano → engenharia de fluxo / fiscalização) e um de
  óbitos (rural, muitas vezes evento único → resposta diferente).

---

## Tabela de corte para a Fase 4 — "vira gráfico do dashboard" × "sem sinal"

### Vira gráfico / KPI (entrada direta da Fase 4)

| Item | Origem | Pergunta de negócio que responde |
| :-- | :-- | :-- |
| Letalidade por papel, **ajustada por idade** (pedestre em destaque) | H1, F3-8 | Onde a fatalidade se concentra por tipo de vítima, sem viés de composição etária? |
| Pedestre × `uso_solo` (rural vs urbano) | H3 | Onde priorizar travessias elevadas / passarelas — o pedestre em rodovia rural é a pior combinação (letalidade ~37%)? |
| Atropelamento × `fase_dia` | H2 | Em quais trechos/horários a iluminação pública tem maior retorno esperado? |
| Letalidade condutor moto × auto, ajustada | H6 | Qual o tamanho real do problema da moto (36% dos óbitos) para dimensionar campanha/fiscalização? |
| Letalidade sexo × papel | H5 | A mensagem de campanha deve separar homem condutor (risco acima da média)? |
| Composição de causa por janela horária × dia (álcool em destaque) | H10 | Quando concentrar a fiscalização de alcoolemia (madrugada de sex–dom: 15% dos acidentes)? |
| Letalidade por `fase_dia` — bruta **e** ajustada, como **alerta** | H11, H13 | "Noite" é filtro ou alerta? (alerta: ~60% do excesso é efeito próprio) |
| Tipo de acidente por janela (FDS-noite vs. dia útil) | H12 | O tipo de intervenção muda com o horário (perda de controle vs. congestionamento)? |
| Letalidade `tipo_pista`, e **dentro da colisão frontal** | H14 | Onde priorizar barreira central / duplicação (pista simples dobra a letalidade da frontal)? |
| Δ letalidade por característica de traçado — só declive | H15 | Onde instalar redutores / sinalização de rampa? |
| Nevoeiro/Neblina como condição de risco isolada | H16 | Quais trechos com neblina recorrente merecem sinalização dinâmica? |
| **Dois mapas de trecho**: frequência de acidentes × óbitos | H17, H18, H19 | Congestionamento urbano (engenharia de fluxo) e fatalidade (resposta a evento) são problemas diferentes — onde cada um? |
| Tabela operacional `reports/pontos_negros.csv` (382 trechos) | H17–H19 | Lista acionável para a PRF: trecho, UF, município, acidentes, mortos, letalidade com IC, via |

### Sem sinal / confundido / rejeitado (o que **não** vira recomendação)

| Item | Veredito | Motivo + número |
| :-- | :-- | :-- |
| Recorte agregado "vulnerável sem carroceria" | H7 `rejeitado` | riscos de ordens diferentes: pedestre 27,7% vs moto 4,9% (fator 5,6). Manter os quatro separados. |
| Segmentar campanha de álcool/velocidade por idade do condutor | H8 `sem sinal` | a `causa` do BO não concentra por idade; álcool skew p/ 40 anos (−2,5 pp de share jovem) |
| Curva como fator de risco autônomo | H15 `confundido` | Δ cai de 1,36 → 0,73 pp após ajustar por pista + solo — era pista simples + rural |
| Alerta de risco por chuva | H16 `sem sinal` | chuva é levemente **protetora** (Δ −0,55 pp) — as pessoas reduzem a velocidade |
| Interação meteorologia × causa | H16 `sem sinal` (3-way) | a condição do tempo desloca a letalidade de forma uniforme entre causas |
| Ranking fino dos trechos negros | H17 (ranking) | correlação de postos entre semestres = 0,19 — a ordem é ruído; usar o conjunto e janela anual |

---

## Devolutivas

- **`spec.md` §2.8** — nota "Devolutiva pós-Fase 3" adicionada, com o veredito dos 6
  cruzamentos. Sustentaram-se: horário×tipo×mortes, pontos negros (com correção de
  chave), idade/sexo×veículo×físico, dia×fase×tipo. **Sem sinal:** causa×meteorologia,
  perfil do condutor×causa.
- **`achados-eda.md` F3-1…F3-9** — tabela "Resolução dos candidatos F3 (pós-Fase 3)"
  adicionada; G6 corrigido (chave `(uf, br, km)` → 382 trechos, não 623).
- **Fase 2.2 / `geografico.py`** — `concentracao_trecho` usa `(br, km)`, que conflita
  entre UFs. Corrigir para `(uf, br, km)` numa tarefa dedicada (muda os números de G6
  e quebra asserts de `tests/test_geografico.py` — não é um patch de uma linha).
- **Fase 1 (ETL)** — nenhuma sentinela nova apareceu só no cruzamento. O único achado
  estrutural (chave de trecho) é da Fase 2.2, não do ETL.
