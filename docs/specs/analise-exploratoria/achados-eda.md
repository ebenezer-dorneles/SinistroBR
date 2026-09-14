# 🔎 achados-eda.md: Análise exploratória

Registro dos achados da Fase 2, um por linha de evidência. Cada achado traz:
**unidade de análise**, os **números**, e um **veredito** — `confirmado` (o padrão
esperado apareceu), `rejeitado` (o esperado não se sustenta) ou `sem sinal`.

Os candidatos marcados **→ Fase 3** entram na lista de cruzamentos/hipóteses.

Reproduzir: `python -m src.eda.dimensoes.<dimensao>` (gera figuras em `reports/figuras/`).

---

## 2.1 — Temporal (unidade: acidente; n = 72.529)

Fonte: `src/eda/dimensoes/temporal.py`. Figuras: `reports/figuras/temporal/`.

### T1 — Sazonalidade mensal fraca, com pico em dezembro
**Unidade:** acidente. **Veredito:** `confirmado` (efeito existe, magnitude baixa).
Dezembro concentra 6.788 acidentes; fevereiro, 5.287 — amplitude de **+28,4%**
entre o mês mais e o menos movimentado. A curva sobe suavemente ao longo do ano
(1º semestre mais fraco). Fevereiro tem menos dias, o que explica parte do vale.
Não há um mês fora da curva que justifique recorte sazonal no dashboard.

### T2 — Sábado é o dia com mais acidentes; meio de semana é o piso
**Unidade:** acidente. **Veredito:** `confirmado`.
Sábado 11.554, domingo ~10,9k, terça-feira 9.062 (menor). Fim de semana responde
por **31,7%** dos acidentes (28,6% seria o esperado se fosse uniforme) — elevação
real, porém modesta.

### T3 — Dois picos horários: manhã (7h) e fim de tarde (17–19h), com o topo às 18h
**Unidade:** acidente. **Veredito:** `confirmado`.
Hora de pico: **18h (5.398 acidentes)**; vale às 2h (1.160). O pico da manhã (7h)
é mais estreito e some no fim de semana; o pico do fim de tarde é o mais alto e
persiste todos os dias. Ver `matriz_dia_hora.png`: segunda 7h e sexta 17–19h são
as células mais quentes.

### T4 — Madrugada de sexta e sábado é anômala
**Unidade:** acidente. **Veredito:** `confirmado`. **→ Fase 3.**
Acidentes entre 0h–4h: sábado 1.479 e domingo 1.614, contra ~570–960 nos dias de
semana. É o padrão clássico de deslocamento noturno de lazer / álcool — candidato
a cruzamento com `causa_acidente` (ingestão de álcool) e severidade na Fase 3.

### T5 — "Mais acidentes de dia" é, em parte, artefato de exposição — o risco por hora pico ao anoitecer
**Unidade:** acidente. **Veredito:** `rejeitado` (para a leitura ingênua) / `confirmado` (para a versão normalizada).
Contagem absoluta: Pleno dia 40.375 >> Plena Noite 24.781 > Anoitecer 3.926 ≈
Amanhecer 3.447. Mas o dia tem ~11,5 h de "pleno dia" e só ~0,8 h de "anoitecer"
(estimativa por P(fase|hora), `exposicao_horas_por_fase_dia`). Normalizando por
hora de exposição (índice, 1 = média):

| fase_dia | acidentes | horas/dia | índice risco/hora |
| :-- | --: | --: | --: |
| Anoitecer | 3.926 | 0,80 | **1,62** |
| Pleno dia | 40.375 | 11,50 | 1,16 |
| Plena Noite | 24.781 | 10,20 | 0,80 |
| Amanhecer | 3.447 | 1,50 | 0,76 |

A transição luz→escuro (anoitecer) é o momento de maior taxa de acidentes por
hora; a plena noite, apesar do volume, tem taxa **abaixo** da média (menos tráfego).

### T6 — Acidente noturno/ao amanhecer é mais letal, mesmo sendo menos frequente
**Unidade:** acidente. **Veredito:** `confirmado`. **→ Fase 3.**
`classificacao_acidente` por fase: fatal em **11,2%** dos acidentes ao amanhecer e
**10,2%** à noite, contra **5,1%** em pleno dia. O anoitecer concentra frequência
(T5) mas letalidade menor (6,4%); a plena noite inverte — menos acidentes, mais
mortos por acidente. Frequência e gravidade têm picos temporais diferentes:
levar as duas curvas para o dashboard, não só a contagem.

---

## 2.2 — Geográfico (unidade: acidente; n = 72.529)

Fonte: `src/eda/dimensoes/geografico.py`. Figuras: `reports/figuras/geografico/`.

> **Limitação de denominador (documentar no dashboard):** todos os rankings desta
> seção medem **volume**, não **risco**. Não há frota, extensão de malha federal
> por UF nem contagem de tráfego neste dataset para normalizar. "MG tem mais
> acidentes" pode ser só "MG tem mais quilômetros de BR".

### G1 — Georreferenciamento cobre 100% dos acidentes (spec §3.4 estava errado)
**Unidade:** acidente. **Veredito:** `rejeitado` (a estimativa do spec).
`latitude`/`longitude`: **0 nulos, 0 outliers** com o parser correto. O spec §3.4
estimava ~51k sem georreferenciamento — número de parsing ingênuo. O mapa de
densidade é viável para todos os 72.529 acidentes. **→ corrigir spec §3.4.**

### G2 — 167 acidentes sem BR identificada (`br == 0`), agora nulos
**Unidade:** acidente. **Veredito:** `confirmado` (sentinela). **→ ETL (feito).**
`br == 0` (sempre com `km == 0`) não é rodovia — é localização não identificada
na malha; mantêm `municipio` e lat/long. Sem tratar, `(br=0, km=0)` era o maior
"trecho". Normalizado para NaN em `normalize_br_km_sentinel`. **→ corrigir spec §3.5.**

### G3 — Concentração forte por rodovia: BR-101 + BR-116 = um terço de tudo
**Unidade:** acidente. **Veredito:** `confirmado`.
BR-101 (13.014) e BR-116 (11.021) sozinhas respondem por **33,1%** dos acidentes;
as 10 BRs mais movimentadas somam **61,1%**. Recorte por BR é o mais informativo
dos três (UF / BR / município) para o dashboard.

### G4 — Ranking por UF: MG, SC, PR na frente; SC desproporcional ao tamanho
**Unidade:** acidente. **Veredito:** `confirmado` (com a ressalva de denominador).
MG 9.570, SC 8.186, PR 7.630; top 5 = 50,6%. Santa Catarina em 2º, à frente de SP
e RS, é o sinal mais interessante — coincide com o corredor BR-101/BR-116. Sem
malha/tráfego para normalizar, fica como volume, não como "estado mais perigoso".

### G5 — Município é recorte ruim: dispersão alta
**Unidade:** acidente. **Veredito:** `confirmado`.
1.844 municípios; top 3 (Brasília 1.011, Duque de Caxias 847, São José 761) e o
top 10 juntos são só **9,7%** do total. Município serve para drill-down, não para
visão geral.

### G6 — Pontos negros: trechos concentram ~30% dos acidentes localizados
**Unidade:** acidente (trecho `(br, km)`, km inteiro). **Veredito:** `confirmado`. **→ Fase 3 (H17–H19).**
17.508 trechos distintos; **623 trechos com ≥ 20 acidentes** somam 21.340
ocorrências (**29,5%** dos acidentes com BR identificada). O topo é um cluster
contíguo: **BR-101 km 205–208** (81–95 acidentes cada). Lista direta de
candidatos a "ponto negro" para a Fase 3 (`concentracao_trecho`).

> **Correção pós-Fase 3 (H17):** a chave `(br, km)` **não é única entre UFs** — a
> BR-101 passa por 12 estados e o km 208 existe em todos. 508 dos 623 "trechos
> negros" misturavam acidentes de estados diferentes. Com a chave correta
> `(uf, br, km)` são **382** trechos com ≥ 20 acidentes/ano; o cluster do topo é
> BR-101 km 205–208 **em SC** (São José, região de Florianópolis), ~300 acidentes.
> `src/eda/hipoteses/pontos_negros.py` já usava a chave corrigida; `concentracao_trecho`
> em `geografico.py` foi corrigida para `(uf, br, km)` (era `(br, km)`), alinhando
> a Fase 2.2 com a Fase 3 — figura e teste atualizados.

### G7 — Recorte operacional PRF (`regional`/`delegacia`/`uop`): fora do dashboard geral
**Unidade:** acidente. **Veredito:** `sem sinal` novo (decisão de escopo).
`regional` (29, top 10 = 74%), `delegacia` (154, top 10 = 22%), `uop` (396, top
10 = 12%) — granularidade crescente. `regional` quase espelha UF (29 vs 27; UOPs
de divisa registram o estado vizinho). Útil para gestão interna da PRF, redundante
com UF/BR para o público geral. **Decisão:** manter fora do dashboard principal;
disponível como filtro avançado se houver usuário PRF.

---

## 2.3 — Causa e tipo do acidente (unidade: acidente; n = 72.529)

Fonte: `src/eda/dimensoes/causa_tipo.py`. Figuras: `reports/figuras/causa_tipo/`.

### C1 — Causa dominada por (des)atenção do condutor
**Unidade:** acidente. **Veredito:** `confirmado`.
As duas causas mais frequentes — "Ausência de reação do condutor" (11.469) e
"Reação tardia ou ineficiente do condutor" (10.799) — somam **30,7%** de todos os
acidentes. A macro-categoria **Falha do condutor concentra 81,0%**; via/ambiente
8,6%, veículo 7,3%, pedestre 2,7%, outros 0,3%.
**Ressalva:** `causa_acidente` é a atribuição do agente da PRF no boletim, não uma
medição — carrega viés de "culpar o condutor" e não deve ser lida como causa-raiz.

### C2 — Tipo de acidente: colisão traseira é o modal
**Unidade:** acidente. **Veredito:** `confirmado`.
Colisão traseira 14.360 (19,8%), saída de leito carroçável 10.209, colisão
transversal 9.306. As três somam quase metade dos acidentes. "Sinistro pessoal de
trânsito" tem só 7 registros (categoria nova/rara na taxonomia PRF).

### C3 — `classificacao_acidente`: 77% com feridos, 7,2% fatais; 1 registro nulo com óbito
**Unidade:** acidente. **Veredito:** `confirmado` + anomalia isolada.
Com Vítimas Feridas 56.181 (77,5%), Sem Vítimas 11.138 (15,4%), Com Vítimas
Fatais 5.209 (7,2%), **1 nulo**. O nulo (id 652519) **tem um `mortos == 1`** —
deveria ser "Com Vítimas Fatais"; é lacuna de preenchimento, não ambiguidade.
Impacto nulo: EDA/dashboard usam as flags de severidade por pessoa como fonte
canônica (ver 2.8). **→ não corrige o dado, documenta.**

### C4 — Frequência e letalidade apontam para tipos diferentes
**Unidade:** acidente (letalidade medida no nível pessoa). **Veredito:** `confirmado`. **→ Fase 3.**
O tipo mais frequente (colisão traseira) tem letalidade de só **1,5%** por pessoa.
Os dois tipos letais destacados, isolados no gráfico `tipo_frequencia_vs_letalidade.png`:

| tipo | acidentes | mortos/acidente | mortos/pessoa |
| :-- | --: | --: | --: |
| Atropelamento de Pedestre | 3.057 | 0,30 | **0,118** |
| Colisão frontal | 4.739 | **0,39** | 0,103 |
| Colisão traseira (ref.) | 14.360 | 0,05 | 0,015 |

As duas unidades discordam do ranking: **colisão frontal mata mais por acidente**
(envolve ~3,8 pessoas/acidente), **atropelamento mata mais por pessoa envolvida**.
Levar as duas para o dashboard, rotuladas.

### C5 — Letalidade por macro-causa: pedestre e "outros" no topo, veículo na base
**Unidade:** pessoa. **Veredito:** `confirmado`. **→ Fase 3.**
Mortos por pessoa: Outros (suicídio/transtorno mental) **0,166**, Pedestre
**0,125**, Falha do condutor 0,029, Via/ambiente 0,026, Veículo **0,012**. Defeito
de veículo gera acidente pouco letal; conflito com pedestre, muito. Candidato a
cruzamento causa × severidade × velocidade na Fase 3.

---

## 2.4 — Condições da via e ambiente (unidade: acidente; n = 72.529)

Fonte: `src/eda/dimensoes/via_ambiente.py`. Figuras: `reports/figuras/via_ambiente/`.
Regra desta seção: **taxa de gravidade sempre ao lado da contagem**.

### V1 — "A maioria dos acidentes é em céu claro" é exposição, não risco
**Unidade:** acidente (letalidade no nível pessoa). **Veredito:** `rejeitado` (a leitura de risco).
Céu Claro concentra **64%** dos acidentes, mas a letalidade é praticamente plana
entre condições, e **chuva é até menos letal** (2,74%) que céu claro (3,17%) —
sob chuva as pessoas reduzem a velocidade. Só se destacam **Nevoeiro/Neblina
(4,78%)** e Vento: o que agrava é perda de **visibilidade**, não pista molhada.
1.000 acidentes (2.439 pessoas) sem `condicao_metereologica`.

### V2 — Pista simples (sem separação física) é ~2× mais letal
**Unidade:** pessoa. **Veredito:** `confirmado`. **→ Fase 3.**
Letalidade: **Simples 4,1%** vs Dupla 2,1% vs Múltipla 1,7%. Pista simples não
tem barreira central — é onde acontece a colisão frontal (o 2º tipo mais letal,
2.3/C4). Sinal de risco forte e acionável (canteiro/barreira).

### V3 — Trecho rural converte ferimento em morte
**Unidade:** pessoa. **Veredito:** `confirmado`.
`uso_solo == "Não"` (rural, 57% dos acidentes): letalidade **3,9%** vs 2,0% no
urbano. Mas a taxa de **ferido grave é igual** (10,3% vs 10,25%) — o meio rural
não produz mais feridos, produz mais **óbitos** entre os feridos (velocidade).

### V4 — `sentido_via` nulo (167) = exatamente os acidentes sem BR identificada
**Unidade:** acidente. **Veredito:** `confirmado` (sem ação nova).
Os 167 nulos de `sentido_via` são o mesmo conjunto de `br == 0` (2.2/G2). Já
tratados no ETL; nada a fazer.

### V5 — Traçado: geometria de velocidade agrava, ponto de conflito controlado alivia
**Unidade:** pessoa. **Veredito:** `confirmado`. **→ Fase 3.**
Δ letalidade (acidentes COM a característica − SEM):

| característica | Δ letalidade | leitura |
| :-- | --: | :-- |
| declive | **+1,2 pp** | perda de controle em velocidade |
| curva | **+1,0 pp** | idem |
| ponte / aclive | +0,8 / +0,5 pp | |
| reta | ~0 | é a linha de base (73% dos acidentes) |
| interseção de vias | −1,8 pp | força baixa velocidade |
| rotatória | **−2,4 pp** | idem, ainda mais |

O acidente em rotatória/interseção é frequente mas raramente fatal; o acidente
em declive/curva é o oposto.

---

## 2.5 — Veículo (unidade: veículo; n = 139.517)

Fonte: `src/eda/dimensoes/veiculo.py`. Figuras: `reports/figuras/veiculo/`.

### Ve1 — Atributos de veículo são constantes dentro de `(id, id_veiculo)`
**Unidade:** veículo. **Veredito:** `confirmado` (pré-requisito da 2.0 validado).
`tipo_veiculo`, `marca`, `marca_normalizada` e `ano_fabricacao_veiculo`: **0
divergências** entre linhas do mesmo veículo. A deduplicação `por_veiculo` não
precisa de regra de desempate.

### Ve2 — `marca` refinada: prefixos I/SR/REB/R e sinônimos resolvidos
**Unidade:** veículo. **Veredito:** `confirmado` (limitação da 2.0 fechada). **→ ETL/enrich (feito).**
`split_marca_modelo` passou a tratar "I/M.BENZ 415" → marca M.BENZ; "SR/RANDON"/
"R/RANDON" → RANDON; e a unir sinônimos (CHEV/GM → CHEVROLET, etc.,
`const.MARCA_SINONIMOS`). O top-15 ficou limpo: HONDA, VW, FIAT, CHEVROLET,
M.BENZ, YAMAHA, RANDON, FORD, SCANIA, VOLVO… A cauda longa (centenas de fabricantes
de implementos + ruído de string de modelo) permanece, mas não afeta o ranking.
7.979 veículos sem marca (`NA/NA`). Sentinela `ano_fabricacao < 1950` (32 linhas,
quase tudo "1900") → NaN no ETL.

### Ve3 — Motocicleta: 22% da frota acidentada, 36% dos mortos
**Unidade:** veículo (letalidade no nível pessoa). **Veredito:** `confirmado`. **→ Fase 3.**
Composição: Automóvel 44.937 (32%), **Motocicleta 31.220 (22%)**, carga pesada
(semirreboque + caminhão-trator + caminhão + reboque) ≈ 28%.
Letalidade por pessoa: **Motocicleta 4,8%** vs Automóvel 2,4% (**2×**). Moto
responde por **35,9% de todos os óbitos** e automóvel por 31,8% — juntos, 68%.

### Ve4 — Bicicleta é o veículo mais letal por pessoa envolvida
**Unidade:** pessoa. **Veredito:** `confirmado`.
Bicicleta **12,7%** de letalidade (1.752 pessoas, 223 mortos), à frente de
ciclomotor (7,5%) e muito acima de moto (4,8%). Volume pequeno, risco individual
altíssimo — vítima vulnerável sem proteção nenhuma. Cruzar com `uso_solo` na
Fase 3 (bicicleta em rodovia rural?).

### Ve5 — Frota acidentada é velha: mediana 10 anos, um quarto acima de 15
**Unidade:** veículo. **Veredito:** `confirmado`.
Cobertura de `ano_fabricacao_veiculo`: **92,6%** (10.273 sem ano). Idade:
mediana 10 anos, média 10,7, p90 21. Só **33% têm até 5 anos**; **24,5% passam de
15**. Sem denominador da frota nacional não dá para dizer se a frota acidentada é
mais velha que a que circula — fica como descrição, não como fator de risco.

---

## 2.6 — Vítima / pessoa (unidade: pessoa; n = 194.629)

Fonte: `src/eda/dimensoes/vitima.py`. Figuras: `reports/figuras/vitima/`.
Base de toda taxa de severidade: `apenas_vitimas()` (ver Vi5).

### Vi1 — Perfil: homem adulto (mediana 38 anos)
**Unidade:** pessoa. **Veredito:** `confirmado`.
`sexo`: 63,6% Masculino, 21,5% Feminino, **14,9% nulo** (29.081). `idade`:
cobertura 82,6% (33.824 sem idade), mediana 38, IIQ 28–50. `tipo_envolvido`:
Condutor 122.367 (63%), Passageiro 48.771, Pedestre 3.310, Testemunha 2.993,
Cavaleiro 38, **nulo 17.150**.

### Vi2 — Severidade: 1 em 26 vítimas morre; 28.630 pessoas sem desfecho
**Unidade:** pessoa. **Veredito:** `confirmado`.
Ileso 76.406, ferido leve 63.532, ferido grave 20.018, **óbito 6.043**.
**28.630 pessoas sem nenhuma flag de severidade** — e `estado_fisico` nulo é
exatamente esse conjunto (verificação da 2.8 antecipada). São pessoas presentes
sem desfecho: `tipo_envolvido` nulo (17.150), testemunhas (2.993), condutores
sem status (7.975).

### Vi3 — Letalidade cresce com a idade; o ferimento grave é do jovem adulto
**Unidade:** pessoa (vítimas). **Veredito:** `confirmado`. **→ Fase 3.**
Letalidade por faixa: **60+ 5,1%**, 45–59 3,8%, e decrescendo até 0–17 (2,5%).
Já a **taxa de ferido grave pica em 18–24 (15,2%)** e cai nos extremos. Leitura:
o idoso que se acidenta morre; o jovem se machuca com gravidade e sobrevive.
Idade nula tem taxas artificialmente baixas (registro incompleto) — não comparar.

### Vi4 — Homem tem letalidade maior, não só exposição maior
**Unidade:** pessoa (vítimas). **Veredito:** `confirmado`.
Homens são 64% das vítimas **e** morrem mais por envolvimento: **4,0%** vs 2,6%
nas mulheres. O `sexo` nulo tem letalidade ~0 (0,1%) — clusteriza com registro
incompleto, reforçando que os 29k nulos não são aleatórios.

### Vi5 — Testemunha e `tipo_envolvido` nulo diluem toda taxa de severidade
**Unidade:** pessoa. **Veredito:** `confirmado` (decisão metodológica). **→ base fixa da EDA.**
Testemunha (2.993) e `tipo_envolvido` nulo (17.150) — 20.143 pessoas, todas sem
desfecho — entram no acidente mas nunca são vítimas. Incluí-las no denominador
baixa a letalidade global de **3,46% → 3,10%**. **Decisão:** `apenas_vitimas()`
(`PAPEIS_VITIMA = Condutor/Passageiro/Pedestre/Cavaleiro`) é a base de toda taxa
de severidade na EDA e no dashboard. Resíduo: ~8,5k vítimas ainda estão sem
desfecho registrado — quantificar e decidir na 2.8.

### Vi6 — Pedestre: 27% das vítimas-pedestres morrem
**Unidade:** pessoa (vítimas). **Veredito:** `confirmado`. **→ Fase 3.**
`tipo_envolvido == Pedestre`: **letalidade 27,1%**, ferido grave 35,7% — só
1 em 50 sai ileso. Nenhum outro papel chega perto (Condutor 3,2%, Passageiro
2,6%). O atropelamento (2.3/C4) e o papel de pedestre (aqui) apontam para o
mesmo grupo de altíssimo risco.

---

## 2.7 — Condutor (unidade: pessoa, `tipo_envolvido == "Condutor"`; n = 122.367)

Fonte: `src/eda/dimensoes/condutor.py`. Figuras: `reports/figuras/condutor/`.

### Co1 — O condutor acidentado é homem (88%) e de meia-idade (mediana 40)
**Unidade:** pessoa (condutores). **Veredito:** `confirmado`.
88,2% masculino (contra ~75% no total de vítimas), mediana 40 anos, cobertura de
idade 91,8%. **402 condutores menores de 18** (direção ilegal).

### Co2 — Ser condutor agrava a letalidade dentro de cada faixa etária
**Unidade:** pessoa (vítimas). **Veredito:** `confirmado`. **→ Fase 3.**
Comparado ao passageiro **no mesmo estrato de idade**, o condutor morre mais em
todas as faixas: 18–24 3,3% vs 2,5%; 25–34 3,2% vs 2,4%; 60+ 4,5% vs 3,6%. Não é
só a população que dirige ser mais velha — o **papel** carrega risco (posição
dianteira, sem antecipação, e a moto tem só condutor). O caso extremo: **0–17
dirigindo tem letalidade 6,5%**, 3× o passageiro da mesma idade.

### Co3 — O sexo inverte de sinal conforme o papel
**Unidade:** pessoa (vítimas). **Veredito:** `confirmado` (com confundidor claro). **→ Fase 3.**
Mulher **condutora** tem a menor letalidade de qualquer grupo (**1,6%**), abaixo
da mulher passageira (2,6%). Homem condutor (3,6%) é o oposto — acima do homem
passageiro (2,6%). Quase certamente o **confundidor motocicleta**: condutor de
moto tem letalidade 5,2% vs 2,2% de automóvel, e a frota de moto é
esmagadoramente masculina. Estratificar por tipo de veículo na Fase 3 antes de
qualquer conclusão sobre "quem dirige melhor".

### Co4 — Veículo sem condutor ≠ condutor evadido: são reboques
**Unidade:** veículo. **Veredito:** `rejeitado` (a hipótese da spec §2.7). **→ corrigir spec.**
17.150 veículos (12,3% da frota) não têm linha "Condutor" — e são exatamente os
17.150 `tipo_envolvido` nulos. Mas **16.620 (97%) são semirreboque ou reboque**:
a metade rebocada de um conjunto articulado não tem condutor próprio. A hipótese
de evasão/condutor não localizado vale só para **516 veículos motorizados**
(0,4% da frota), esses sim com taxa de fatalidade acima da média (11% vs 8,4%) —
padrão compatível com fuga de acidente grave.

---

## 2.8 — Consistências e devolutiva para a Fase 1 (unidade: variável)

Fonte: `src/eda/dimensoes/consistencia.py`.

### Cn1 — `classificacao_acidente` é 100% consistente com as flags de severidade
**Unidade:** acidente. **Veredito:** `confirmado`.
Cruzando o rótulo de nível acidente com as flags das pessoas do mesmo `id`:
**0 divergências** — todo "Com Vítimas Fatais" tem ≥ 1 `mortos`, todo "Sem
Vítimas" não tem ferido nem morto, todo "Com Vítimas Feridas" tem ferido e nenhum
morto. Única exceção: o **1 registro nulo** (id 652519, 2.3/C3), que tem óbito e
deveria ser "Com Vítimas Fatais". As duas representações concordam — pode-se usar
qualquer uma; a EDA usa as flags por pessoa (mais granulares).

### Cn2 — `estado_fisico` é redundante com as flags de severidade
**Unidade:** pessoa. **Veredito:** `confirmado`. **→ decisão: usar as flags.**
`estado_fisico` nulo (28.630) é **exatamente** o conjunto de linhas sem nenhuma
flag marcada, e cada valor mapeia 1:1 (`Ileso`→`ilesos`, `Óbito`→`mortos`, etc.).
**Decisão:** a EDA e o dashboard usam `ilesos/feridos_leves/feridos_graves/mortos`
como representação canônica de severidade; `estado_fisico` não acrescenta nada.

### Cn3 — 4,9% das vítimas não têm desfecho registrado
**Unidade:** pessoa (vítimas). **Veredito:** `confirmado`. **→ decisão parcial.**
Mesmo depois do filtro `apenas_vitimas`, **8.487 vítimas (4,9%)** — 94% delas
condutores — não têm nenhuma flag de severidade. Incluí-las no denominador
deprime a letalidade de vítima de **3,64% → 3,46%** (~5% relativo).
**Decisão:** `apenas_vitimas(com_desfecho=True)` exclui esse resíduo e é a base
recomendada para a **modelagem da Fase 3**; a Fase 2 manteve `com_desfecho=False`
(as conclusões — rankings, gradientes, contrastes — não mudam de sinal).

### Cn4 — A decisão `idade == 0 → NaN` (Fase 1) se sustenta
**Unidade:** pessoa. **Veredito:** `confirmado` (revalidação retroativa).
Das 33.824 linhas sem idade: **84,6% não têm desfecho** de severidade (registro
incompleto) e **2.056 são condutores** — impossível terem idade real 0. Das 5.194
com desfecho, 2.594 são passageiros (onde bebê real seria plausível), mas o
dataset já registra idades 1–5 de passageiros quando conhecidas (1.589 casos), e
converter o desconhecido para `NaN` em vez de `0` é a escolha conservadora
(exclui da média, não a puxa para baixo). **Decisão da Fase 1 mantida.**

---

## Consolidação — candidatos para a Fase 3

Cruzamentos e hipóteses que a Fase 2 deixou maduros (cada um traz a referência do
achado de origem). Unidade e grupo de controle indicados onde importam.

| # | Hipótese / cruzamento a testar | Origem | Notas |
| :-- | :-- | :-- | :-- |
| F3-1 | **Pontos negros**: modelar concentração por trecho `(br, km)` — 623 trechos com ≥ 20 acidentes, começando por BR-101 km 205–208 | G6 | insumo operacional direto; unir com `tracado_via` e `tipo_pista` do trecho |
| F3-2 | **Pedestre / atropelamento** como cluster de altíssima letalidade (27%) — perfil, local (`uso_solo`), hora (`fase_dia`), idade | C4, C5, Vi6, Co-ref | pedestre idoso? travessia noturna? |
| F3-3 | **Motocicleta**: 22% da frota, 36% dos óbitos. Isolar o efeito "moto" da letalidade masculina e da idade jovem | Ve3, Co3 | estratificar sexo/idade **dentro** de tipo de veículo |
| F3-4 | **Anoitecer + noite**: risco/hora pico ao anoitecer, letalidade pico à noite/amanhecer — cruzar com álcool (`causa`) e madrugada de fim de semana | T4, T5, T6 | F3-4 e F3-6 se sobrepõem |
| F3-5 | **Pista simples × colisão frontal**: pista sem separação física é 2× letal e concentra a colisão frontal | V2, C4 | candidato a recomendação de infraestrutura (barreira central) |
| F3-6 | **Madrugada de sexta/sábado**: volume 2× o dia útil — cruzar com `causa` (álcool), `faixa_etaria` (jovem), letalidade | T4 | |
| F3-7 | **Geometria de velocidade** (declive/curva) agrava, ponto de conflito (rotatória/interseção) alivia — modelar com `velocidade`/`tipo_pista` | V5 | |
| F3-8 | **Gradiente etário da severidade**: idoso morre, jovem adulto se fere grave — ajustar taxa por idade em toda comparação | Vi3 | não é hipótese, é controle obrigatório |
| F3-9 | **Condutor evadido**: ~516 veículos motorizados sem condutor, fatalidade 11% vs 8,4% — caracterizar | Co4 | amostra pequena, valor exploratório |

**Limitações herdadas (registrar no dashboard):** todos os rankings geográficos e
por categoria medem **volume, não risco** — não há frota, malha rodoviária nem
tráfego para normalizar (G3, G4, Ve5). `causa_acidente` é a atribuição subjetiva
do agente no BO, não causa-raiz (C1).

> **Onde cada candidato foi parar (planejamento da Fase 3):** F3-1 → 3.5 (H17–H19);
> F3-2 → 3.1 (H1–H4); F3-3 → 3.2 (H5–H7); F3-4 e F3-6 → 3.3 (H10–H13, fundidos como
> previsto); F3-5 e F3-7 → 3.4 (H14, H15); F3-8 → **3.0**, virou controle obrigatório
> de toda comparação, não hipótese; F3-9 → 3.2 (H9). O cruzamento *causa ×
> meteorologia × gravidade* (spec §2.8) não gerou candidato — V1 sugere ausência de
> efeito — e por isso ganhou hipótese própria (H16): "sem sinal" com número é
> entregável da fase. Ver `plan.md` §Fase 3 e `task.md`.
>
> **Correção de planejamento:** as notas de F3-5/F3-7 ("modelar com `velocidade`") não
> são executáveis — **não existe coluna `velocidade`** nas 35 do dataset. O substituto
> é a causa `"Velocidade Incompatível"` (4.088 acidentes), que é atribuição do BO
> (ressalva C1), usada como indício e nunca como medida.

---

## Resolução dos candidatos F3 (pós-Fase 3)

Detalhe e números em `resultados-fase3.md`.

| Candidato | Hipótese(s) | Veredito | Nota |
| :-- | :-- | :-- | :-- |
| F3-1 Pontos negros | H17–H19 | **confirmado** | conjunto estável, ranking não; chave corrigida p/ `(uf, br, km)` → 382 trechos; volume ≠ mortes (dois mapas). `reports/pontos_negros.csv` |
| F3-2 Pedestre/atropelamento | H1–H4 | **confirmado** | letalidade 27,7% → 22 pp após ajuste por idade; pior em rodovia rural (+15 pp) e à noite (RR 1,9); skew p/ idoso |
| F3-3 Motocicleta | H5–H7 | **confirmado** (H5,H6) / **rejeitado** (H7) | moto RR 2,2 após ajuste; inversão sexo×papel NÃO é confundida pela moto; "vulnerável sem carroceria" não é grupo coerente |
| F3-4 + F3-6 Anoitecer/noite/madrugada | H10–H13 | **confirmado** | álcool na madrugada de FDS (3,4×); letalidade noturna 40% composição / 60% efeito próprio → alerta, não filtro |
| F3-5 Pista simples × frontal | H14 | **confirmado** | agrava por dois caminhos: concentra a frontal E dobra a letalidade dentro da frontal (12,6% vs 6,1%) |
| F3-7 Geometria de velocidade | H15 | **declive confirmado / curva confundido** | declive +1,15 pp ajustado; curva cai p/ +0,73 pp (era pista simples + rural) |
| F3-8 Gradiente etário | — (3.0) | **controle aplicado** | virou ajuste obrigatório de toda comparação (padronização direta por `faixa_etaria`) |
| F3-9 Condutor evadido | H9 | **confirmado (exploratório)** | 530 veículos, acidentes 2,1× mais fatais; mecanismo (evasão vs. registro faltante) não identificável |
| *(causa × meteorologia)* | H16 | **sem sinal** (3-way) | só Nevoeiro/Neblina isolado agrava; chuva é protetora |
