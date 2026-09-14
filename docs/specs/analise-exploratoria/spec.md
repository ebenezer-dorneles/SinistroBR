# 📄 spec.md: Análise exploratória

## 1. Visão Geral (Overview)
Criar um dashboard com uma análise exploratória sobre o conjunto de dados data/por_pessoa_acidentes2025.csv.

## 2. Campos disponíveis e padrões a investigar

O dataset traz um registro por pessoa envolvida em acidente na malha rodoviária federal (padrão PRF). Os campos abaixo estão agrupados por dimensão de análise.

### 2.1 Temporal
- `data_inversa`, `dia_semana`, `horario` — sazonalidade (mês, dia da semana), horários de pico de acidentes.
- Cruzar com `fase_dia` (Pleno dia, Anoitecer, Plena noite, Amanhecer) para comparar acidentes diurnos vs. noturnos.

### 2.2 Geográfico
- `uf`, `br`, `km`, `municipio`, `latitude`, `longitude` — identificação de pontos críticos (trechos/km com concentração de acidentes), ranking de UFs e BRs mais perigosas, mapa de calor.
- `regional`, `delegacia`, `uop` — jurisdição da PRF responsável, útil para análise operacional.

### 2.3 Causa e tipo do acidente
- `causa_acidente` — principais causas (falha humana, condição da via, condição do veículo, etc.).
- `tipo_acidente` — colisão frontal, tombamento, saída de pista, atropelamento, etc.
- `classificacao_acidente` — com vítimas fatais, feridos ou sem vítimas; indicador de gravidade.

### 2.4 Condições da via e ambiente
- `condicao_metereologica` — chuva, sol, neblina, etc., cruzado com gravidade.
- `tipo_pista` (simples, dupla, múltipla) e `tracado_via` (reta, curva, declive, aclive) — geometria da via como fator de risco.
- `sentido_via` (crescente/decrescente).
- `uso_solo` (urbano/rural).

### 2.5 Veículo
- `tipo_veiculo`, `marca`, `ano_fabricacao_veiculo` — tipos de veículo mais envolvidos em acidentes, idade média da frota acidentada.
- `id_veiculo` — permite contar veículos únicos por acidente (múltiplas pessoas podem estar no mesmo veículo).

### 2.6 Vítima / pessoa
- `tipo_envolvido` (condutor, passageiro, pedestre) — perfil de quem se envolve.
- `estado_fisico`, `idade`, `sexo` — perfil demográfico das vítimas, faixas etárias mais vulneráveis.
- `ilesos`, `feridos_leves`, `feridos_graves`, `mortos` — métricas de severidade, taxa de letalidade.

### 2.7 Identificação do condutor
- É possível isolar o condutor via `tipo_envolvido == "Condutor"` (122.367 de ~194,6 mil linhas, ~63% dos registros; demais valores: `Passageiro`, `Pedestre`, `Testemunha`, `Cavaleiro`, `NaN`).
- Validado que a granularidade é consistente: agrupando por `(id, id_veiculo)`, não há mais de um `"Condutor"` por veículo em um mesmo acidente — ou seja, o dado permite tratar "o condutor" como único por veículo/acidente.
- Com o filtro aplicado, dá para analisar exclusivamente o perfil de quem dirigia: `idade`, `sexo`, `estado_fisico`, cruzado com `causa_acidente`, `tipo_veiculo`, `classificacao_acidente`.
- Limitações: o dado é anonimizado (sem CPF/nome, não é possível identificar a pessoa física nem cruzar histórico entre acidentes diferentes); acidentes sem nenhum registro de `"Condutor"` (parte dos ~17k com `tipo_envolvido` vazio) merecem checagem à parte — pode indicar evasão ou condutor não localizado.

> **Correção pós-EDA (Fase 2.7/2.8):** a hipótese de evasão **não se sustenta** para
> a maioria. Os 17.150 veículos sem linha "Condutor" são exatamente os 17.150
> `tipo_envolvido` nulos, e **97% (16.620) são semirreboque ou reboque** — a metade
> rebocada de um conjunto articulado não tem condutor próprio. Evasão/condutor não
> localizado vale só para ~516 veículos motorizados (0,4% da frota), esses com
> fatalidade acima da média. Ver `achados-eda.md` (Co4).

### 2.8 Cruzamentos mais reveladores
- Causa × condição meteorológica × gravidade.
- Horário × tipo de acidente × mortes.
- BR/km × classificação do acidente (identificação de pontos negros).
- Idade/sexo × tipo de veículo × estado físico.
- Dia da semana × fase do dia × tipo de acidente.
- Perfil do condutor (idade/sexo) × causa do acidente × gravidade.

> **Devolutiva pós-Fase 3** (`resultados-fase3.md`, H1–H19). Veredito dos 6 cruzamentos:
> - **Causa × meteorologia × gravidade** (H16): 3-way **sem sinal** — a meteorologia
>   não modifica o efeito da causa. Único efeito real: Nevoeiro/Neblina isolado
>   (+1,3 pp ajustado). Chuva é levemente **protetora**. Confirma V1.
> - **Horário × tipo de acidente × mortes** (H12/H13): **confirmado** — colisão
>   frontal e atropelamento (os dois tipos letais) dobram sua participação nas
>   janelas 0–5h e 18–23h; o filtro temporal muda o *tipo* de acidente, não só o volume.
> - **BR/km × pontos negros** (H17–H19): **confirmado**, com duas correções: (a) a
>   chave de trecho precisa de `uf` — `(br, km)` conflita entre estados, e o número
>   real é **382** trechos com ≥20 acidentes/ano, não ~623; (b) concentração de
>   acidentes ≠ concentração de mortes (interseção ~zero). Entregável:
>   `reports/pontos_negros.csv`.
> - **Idade/sexo × tipo de veículo × estado físico** (H1/H5/H6): **confirmado** — a
>   letalidade do pedestre (H1, +22 pp após ajuste por idade) e da moto (H6, RR 2,2
>   após ajuste) são efeitos próprios; a inversão sexo×papel (H5) sobrevive ao
>   ajuste por idade e tipo de veículo (não é confundida pela moto).
> - **Dia da semana × fase do dia × tipo de acidente** (H10/H12): **confirmado** — a
>   madrugada de fim de semana concentra álcool (15% vs 4,5%) e perda de controle
>   ("saída de leito carroçável").
> - **Perfil do condutor × causa × gravidade** (H8): **sem sinal** — a `causa` do BO
>   não concentra por idade do condutor; álcool inclusive skew para mais velho
>   (mediana 40). Herda a ressalva C1 (causa é atribuição, não medição).

## 3. ETL — tratamento de dados vazios ou incorretos

Inspeção do arquivo bruto identificou os seguintes problemas que precisam ser resolvidos antes da análise:

### 3.1 Encoding
- Arquivo está em `ISO-8859-1` (Latin-1), não UTF-8 — ler com `encoding="latin-1"` (ou `cp1252`), senão textos como `causa_acidente` e `tipo_veiculo` saem corrompidos (`"Rea��o tardia"`).

### 3.2 Delimitador e aspas
- Separador é `;`, com campos entre aspas duplas.
- Alguns campos de texto (ex.: `tracado_via`) contêm **`;` dentro do próprio valor** (ex.: `"Reta;Declive"` para indicar múltiplas características do traçado). Um split ingênuo por `;` quebra o alinhamento das colunas — obrigatório usar um parser de CSV que respeite aspas (`pandas.read_csv(sep=";", quotechar='"')` ou equivalente), nunca `str.split(";")`.

### 3.3 Separador decimal
- Campos numéricos como `latitude`, `longitude` e `km` usam vírgula como separador decimal (ex.: `-23,48586772`) — precisam de conversão (`decimal=","` no `read_csv`, ou `str.replace(",", ".")` seguido de cast para `float`).

### 3.4 Valores ausentes / sentinelas
O dataset mistura diferentes formas de representar "sem informação", que precisam ser normalizadas para `NaN`:
- Vazio (string vazia)
- `"NA"`
- `"Não Informado/Não Informado"`, `"Não Informado"`
- `"Ignorado"`

Colunas com maior volume de ausentes/sentinelas (estimativa sobre ~194 mil linhas):
| Coluna | Ausentes (aprox.) | Observação |
|---|---|---|
| `mortos` | ~183k | maioria dos registros não é morte — comportamento esperado, não é falta de dado |
| `feridos_graves` | ~162k | idem |
| `feridos_leves` | ~124k | idem |
| `ilesos` | ~94k | idem |
| `latitude`/`longitude` | ~51k / ~5,5k | georreferenciamento incompleto, impacta mapas |
| `idade` | ~32k | ver 3.5 |
| `sexo` | ~29k | inclui `"Não Informado"` |
| `estado_fisico` | ~25k | inclui `"Ignorado"` |
| `ano_fabricacao_veiculo` | ~15k | valor `0` usado como sentinela |
| `tipo_envolvido` | ~15k | |
| `pesid` | ~17k | vazio em parte dos registros |
| `marca` | ~8k | inclui `"Não Informado/Não Informado"` |

> **Correção pós-EDA (Fase 2.8):** vários números acima vieram de parsing ingênuo
> do CSV e não se confirmaram com o parser correto (`encoding="latin-1"`, `sep=";"`,
> `decimal=","`). Valores reais medidos no dataset tratado:
> - **`latitude`/`longitude`: 0 nulos, 0 outliers.** Georreferenciamento cobre 100%
>   dos acidentes — a estimativa de ~51k sem georreferenciamento estava errada.
> - `estado_fisico`: 28.630 nulos (nível pessoa), **idênticos** às linhas sem
>   nenhuma flag de severidade — é redundante com `ilesos/feridos_*/mortos`.
> - `sexo`: 29.081 nulos. `tipo_envolvido`: 17.150 nulos (= veículos sem condutor,
>   ver §2.7). `pesid`: 17.150 sentinelas `0` → `NaN`.
> - Sentinelas adicionais tratados no ETL, não previstos aqui: `id_veiculo == 0`
>   (6.341, pessoas sem veículo), `br == 0` (167 acidentes, sem localização na malha).
> Detalhes e evidência: `achados-eda.md` (G1, G2, Vi2).

> Nota: para as colunas `ilesos`, `feridos_leves`, `feridos_graves`, `mortos`, o valor `0` **é legítimo** (indicador binário por pessoa) — não deve ser tratado como ausente.

### 3.5 Valores suspeitos/incorretos
- `idade = 0`: ocorre em ~23,8 mil linhas — provável uso como sentinela de "não informado", já que idade real zero é implausível na maioria dos casos. Decidir regra de negócio: converter para `NaN` ou manter distinção entre bebês/crianças (checar coerência com `tipo_envolvido`).
- `ano_fabricacao_veiculo = 0`: mesma lógica de sentinela — converter para `NaN`.
- Checar `latitude`/`longitude` fora dos limites geográficos do Brasil (outliers de digitação).
- Checar `km` e `br` inconsistentes (ex.: km negativo ou fora do intervalo plausível da rodovia).

> **Correção pós-EDA (Fase 2.8) — decisões tomadas:**
> - **`idade == 0`: 33.685 linhas** (não ~23,8 mil). **Decisão: → `NaN`.** Revalidado
>   na 2.8: 84,6% das linhas sem idade também não têm desfecho de severidade
>   (registro incompleto), e 2.056 são condutores (impossível ter idade real 0).
>   Convertida para `NaN`, não `0`. Também `idade > 122` (139 linhas, ano no lugar
>   da idade) → `NaN`.
> - **`ano_fabricacao_veiculo == 0`: 17.394 linhas → `NaN`.** Mais `ano < 1950`
>   (32 linhas, quase tudo "1900") → `NaN`.
> - `km`/`br`: 0 outliers de `km` (negativo/absurdo). `br == 0` (167 acidentes) é
>   sentinela de "não localizado na malha" → `NaN` junto com o `km`.
> Evidência: `achados-eda.md` (Vi3, Ve5, G2) e `const.md`.

### 3.6 Duplicidade
- Uma linha por pessoa envolvida: acidentes com múltiplos ocupantes geram múltiplas linhas com o mesmo `id` (acidente) e possivelmente mesmo `id_veiculo`. Validar que não há linhas duplicadas por `(id, pesid)`.

### 3.7 Pipeline proposto
1. Ler CSV com `encoding="latin-1"`, `sep=";"`, `decimal=","`, respeitando aspas.
2. Padronizar nomes de sentinelas (`"NA"`, `"Não Informado..."`, `"Ignorado"`, string vazia) para `NaN` via `na_values`.
3. Converter tipos: datas (`data_inversa`), horários (`horario`), numéricos (`idade`, `km`, `ano_fabricacao_veiculo`, `latitude`, `longitude`).
4. Tratar sentinelas numéricas (`idade == 0`, `ano_fabricacao_veiculo == 0`) conforme regra definida em 3.5.
5. Validar unicidade de `(id, pesid)` e remover duplicatas exatas, se houver.
6. Persistir dataset tratado (ex.: parquet/CSV UTF-8) para consumo do dashboard, separado do dado bruto.

## 4. Próximos passos
- Definir as perguntas de negócio prioritárias e os gráficos correspondentes para o dashboard.
- Definir granularidade das visualizações (nacional, por UF, por BR).
- Decidir e documentar as regras de negócio para os pontos levantados em 3.5 (ex.: o que fazer com `idade = 0`).
