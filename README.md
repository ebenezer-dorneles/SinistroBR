# Sinistros de trânsito — análise exploratória (PRF 2025)

Dashboard com análise exploratória de `data/raw/por_pessoa_acidentes2025.csv`, dataset
da Polícia Rodoviária Federal com **uma linha por pessoa envolvida** em um acidente
(não uma linha por acidente).

Documentação de referência (ler antes de qualquer trabalho de dados):

- `docs/specs/analise-exploratoria/spec.md` — contrato do problema (o quê / por quê)
- `docs/specs/analise-exploratoria/plan.md` — mapa metodológico e fases
- `docs/specs/analise-exploratoria/task.md` — checklist tático (fonte da verdade do progresso)
- `docs/specs/analise-exploratoria/const.md` — parâmetros e limiares (espelho de `src/const.py`)
- `docs/specs/analise-exploratoria/achados-eda.md` — achados da EDA, um por linha de evidência
- `CLAUDE.md` — gotchas de parsing do CSV e workflow spec-driven

## Estrutura

```
data/raw/          CSV bruto da PRF (ISO-8859-1, sep=";", decimal=",")
data/processed/    dataset tratado em parquet (git-ignored; gerado pelo ETL)
src/const.py       painel de controle: paths, seeds, limiares, denominadores
src/etl/           Fase 1 — pipeline de ETL
src/eda/           Fase 2 — enriquecimento, recortes por unidade, métricas
src/eda/dimensoes/ Fase 2 — uma análise por dimensão (temporal, geográfico, ...)
reports/figuras/   figuras da EDA (git-ignored; geradas pelos scripts de dimensão)
tests/             pytest (ETL + EDA)
docs/specs/        specs do projeto
```

## Setup

```bash
pip install -r requirements.txt
```

## Como rodar

```bash
python -m src.etl.pipeline              # Fase 1: grava data/processed/acidentes2025.parquet + relatório
python -m src.eda.dimensoes.temporal    # Fase 2.1: números + figuras em reports/figuras/temporal/
python -m src.eda.dimensoes.geografico  # Fase 2.2: rankings, trechos, mapa de densidade
python -m src.eda.dimensoes.causa_tipo  # Fase 2.3: causa/tipo/classificação, letalidade
python -m src.eda.dimensoes.via_ambiente # Fase 2.4: meteorologia, pista, solo, traçado + gravidade
python -m src.eda.dimensoes.veiculo     # Fase 2.5: tipo, marca, idade da frota, letalidade
python -m src.eda.dimensoes.vitima      # Fase 2.6: perfil, severidade, letalidade por faixa/sexo/papel
python -m src.eda.dimensoes.condutor    # Fase 2.7: perfil do condutor vs passageiro, veículos sem condutor
python -m src.eda.dimensoes.consistencia # Fase 2.8: checagens cruzadas e devolutiva para o ETL
python -m src.eda.hipoteses.pedestre    # Fase 3.1: H1–H4 pedestre/atropelamento + figuras
python -m src.eda.hipoteses.moto_perfil # Fase 3.2: H5–H9 moto, sexo, papel + figuras
python -m src.eda.hipoteses.tempo       # Fase 3.3: H10–H13 noite, madrugada, álcool + figuras
python -m src.eda.hipoteses.via         # Fase 3.4: H14–H16 pista, geometria, meteorologia + figuras
python -m src.eda.hipoteses.pontos_negros # Fase 3.5: H17–H19 + reports/pontos_negros.csv
pytest -q                               # suíte de testes (133 testes)
```

Na EDA (Fase 2), o dataframe tratado + enriquecido vem de:

```python
from src.eda import load_enriched, por_acidente, por_veiculo, por_pessoa, resumo_severidade

df = load_enriched()                 # roda o ETL em memória (ou from_parquet=True)
acidentes = por_acidente(df)         # 72.529 — unidade das dimensões de acidente
resumo_severidade(por_pessoa(df), por="tipo_envolvido")
```

## Status do projeto

| Fase | Situação |
| :--- | :--- |
| 0 — Setup | **Concluída** — diretórios, `requirements.txt`, persistência parquet, `src/const.py` |
| 1 — ETL | **Concluída** — sete passos de `spec.md §3.7` + duas devolutivas da Fase 2 |
| 2 — EDA por dimensão | **Concluída** — 2.0–2.8; 42 achados em `achados-eda.md`, 9 candidatos para a Fase 3 |
| 3 — Cruzamentos e hipóteses | **Concluída** — 3.0–3.6; H1–H19 com veredito em `resultados-fase3.md` (~15 confirmado, 2 sem sinal, 1 confundido, 1 rejeitado), tabela de corte para a Fase 4, `reports/pontos_negros.csv` |
| 4+ — Dashboard | Não iniciada — entrada em `resultados-fase3.md` §"Tabela de corte para a Fase 4" |

A Fase 3 cruza dimensões e separa **efeito de confundidor** (a Fase 2 descreveu uma
dimensão por vez e deixou suspeitas explícitas de composição). Três premissas fixadas
no planejamento, antes de rodar qualquer hipótese:

1. **Toda taxa é condicional ao acidente** — sem denominador de exposição, mede-se
   P(morte | envolvido), nunca P(acidente | exposição). Frequência é volume.
2. **Decisão por tamanho de efeito, não por p-valor** — com n = 194.629 tudo é
   "significante"; o corte é `Δ ≥ 1 pp` **e** `RR ≥ 1,20` com IC 95% (ver `const.md`).
3. **Ajuste por idade e tipo de veículo é obrigatório** em toda comparação de
   severidade (estratificação + padronização direta). Veredito novo: `confundido`.

O dataset **não tem** velocidade medida, alcoolemia, cinto/capacete, frota/malha/
tráfego nem tempo de socorro — a fase conclui sobre severidade condicional, não sobre
causa-raiz (detalhe em `plan.md` §Fase 3).

### Fase 1 — `src/etl/pipeline.py`

- `load_raw` — `encoding="latin-1"`, `sep=";"`, `decimal=","`, aspas, `na_values`
- `convert_types` — `data_inversa` (data), `horario` (timedelta)
- `normalize_pesid_sentinel` / `normalize_idveiculo_sentinel` / `normalize_br_km_sentinel` — `pesid == 0` (17.150), `id_veiculo == 0` (6.341, pessoas sem veículo), `br == 0` (167 acidentes, sem localização na malha) → `NaN`
- `normalize_numeric_sentinels` — `idade == 0` (33.685), `ano_fabricacao_veiculo == 0` (17.394), `idade > 122` (139), `ano_fabricacao_veiculo < 1950` (32) → `NaN`
- `check_geo_outliers` / `check_km_outliers` — 0 outliers
- `check_duplicates` / `drop_exact_duplicates` — unicidade `(id, pesid)` (0 duplicatas)
- `build_quality_report` + `persist` — relatório e parquet

### Fase 2.0 — `src/eda/`

- `dataset.load_enriched()` — ETL em memória + enriquecimento
- `dataset.por_acidente` / `por_veiculo` / `por_pessoa` — recortes por unidade (72.529 / 139.517 / 194.629); `checar_denominadores()` trava se divergirem
- `dataset.apenas_vitimas` / `apenas_condutores` — filtros de `por_pessoa` (base de severidade / unidade da 2.7)
- `enrich` — `mes`/`dia_semana_ord`/`hora`, `faixa_etaria`, `tracado_via` canonicalizado (12 indicadores `tem_*`), `marca_normalizada`/`modelo`, `causa_macro` (5 categorias)
- `severity` — `taxa_letalidade_por_pessoa`, `taxa_ferido_grave_por_pessoa`, `mortos_por_acidente`, `resumo_severidade`

### Fase 2.1 — `src/eda/dimensoes/temporal.py`

Distribuições por mês / dia da semana / hora, matriz dia×hora, e `fase_dia`
normalizada pela exposição (`exposicao_horas_por_fase_dia`). Achados T1–T6 em
`achados-eda.md` — destaque: o predomínio diurno é em parte exposição, o risco
por hora pico ao anoitecer e a letalidade à noite/amanhecer.

### Fase 2.2 — `src/eda/dimensoes/geografico.py`

`ranking_uf` / `ranking_br` / `ranking_municipio`, `concentracao_trecho` (pontos
negros por `(br, km)`), `cobertura_operacional`, mapa hexbin de densidade.
Achados G1–G7 — destaque: BR-101+BR-116 = 33% dos acidentes, 623 trechos
concentram ~30% dos casos localizados (insumo da Fase 3), rankings medem volume
e não risco (sem frota/malha para normalizar).

### Fase 2.3 — `src/eda/dimensoes/causa_tipo.py`

`frequencia_causa` / `frequencia_causa_macro` / `frequencia_tipo`,
`distribuicao_classificacao` + `classificacao_nula`, `letalidade_por(pessoas, coluna)`
(mortos por acidente **e** por pessoa, lado a lado). Achados C1–C5 — destaque:
81% dos acidentes são "Falha do condutor", mas os tipos letais são atropelamento
de pedestre e colisão frontal, não a colisão traseira (modal).

### Fase 2.4 — `src/eda/dimensoes/via_ambiente.py`

`distribuicao`, `gravidade_por_condicao` (contagem + letalidade + ferido grave),
`tracado_frequencia` / `tracado_gravidade` (Δ com vs sem cada característica).
Achados V1–V5 — destaque: "céu claro" é exposição (chuva é menos letal); pista
simples ~2× mais letal; trecho rural converte ferido em morto; declive/curva
agravam, rotatória/interseção aliviam.

### Fase 2.5 — `src/eda/dimensoes/veiculo.py`

`constancia_por_veiculo` (valida a dedup — 0 divergências), `distribuicao_tipo`,
`ranking_marca` (após refino I/SR/REB/R + sinônimos no `enrich`), `idade_frota`,
`severidade_por_tipo`. Achados Ve1–Ve5 — destaque: **motocicleta = 22% da frota
mas 36% dos óbitos** (letalidade 2× a do automóvel); bicicleta é o veículo mais
letal por pessoa (12,7%); frota acidentada tem mediana de 10 anos.

### Fase 2.6 — `src/eda/dimensoes/vitima.py`

`perfil_idade`, `distribuicao_sexo` / `distribuicao_tipo_envolvido`,
`distribuicao_severidade`, `letalidade_por` (base `apenas_vitimas`),
`impacto_testemunha`. Achados Vi1–Vi6 — destaque: letalidade cresce com idade
(60+ 5,1%) mas o ferido grave é do jovem adulto; homem 4,0% vs mulher 2,6%;
**pedestre 27,1%**; testemunha/nulo saem do denominador de severidade.

### Fase 2.7 — `src/eda/dimensoes/condutor.py`

`perfil`, `letalidade_papel` (condutor/passageiro/pedestre), `letalidade_condutor_vs_passageiro`
(estratificada), `veiculos_sem_condutor`. Achados Co1–Co4 — destaque: o condutor
morre mais que o passageiro **dentro de cada faixa etária** (efeito do papel);
mulher condutora é a mais segura (confundidor moto); os 17.150 "veículos sem
condutor" são 97% reboques, não evasão.

### Fase 2.8 — `src/eda/dimensoes/consistencia.py`

`classificacao_vs_flags`, `estado_fisico_vs_flags`, `revalidar_idade_zero`,
`vitimas_sem_desfecho`. Achados Cn1–Cn4 — `classificacao_acidente` e
`estado_fisico` são consistentes/redundantes com as flags de severidade (a EDA
usa as flags); a decisão `idade == 0 → NaN` da Fase 1 é revalidada;
`apenas_vitimas(com_desfecho=True)` é a base recomendada para a Fase 3.
`achados-eda.md` fecha com a tabela de candidatos F3-1…F3-9.

### Fase 3 — `src/eda/inferencia.py` + `src/eda/hipoteses/`

`inferencia.py` — IC de Wilson (`taxa_com_ic`), RR de Katz (`rr_com_ic`),
`tabela_estratificada`, `padronizacao_direta`, `contraste` (bruto/ajustado) e
`veredito()` (regra por tamanho de efeito, não por p-valor). Limiares em
`src/const.py` (`MIN_N_CELULA`, `MIN_DELTA_PP`, `MIN_RR`).

`hipoteses/` — uma sub-fase por módulo: `pedestre` (H1–H4), `moto_perfil`
(H5–H9), `tempo` (H10–H13), `via` (H14–H16), `pontos_negros` (H17–H19 +
`reports/pontos_negros.csv`). Resultado em `resultados-fase3.md`: tabela-mestre
H1–H19 + tabela de corte para a Fase 4. Destaques: pedestre em rodovia rural é a
pior combinação (letalidade ~37%); a inversão sexo×papel **não** é confundida
pela moto; "noite" é alerta e não filtro (~60% do excesso é efeito próprio);
pista simples dobra a letalidade da colisão frontal; concentração de acidentes ≠
concentração de mortes (dois mapas). A chave de trecho de G6 precisava de `uf` —
são 382 trechos negros, não 623.

### Decisões

- `idade == 0` / `ano_fabricacao_veiculo == 0` → `NaN`; revalidação retroativa na tarefa 2.8.
- `id_veiculo == 0` e `idade > 122` → `NaN` (devolutivas da Fase 2 para o ETL).
- Persistência em **parquet**; biblioteca de visualização da EDA: **matplotlib**.
- Denominador de veículos medido: **139.517** (spec estimava 139.518 por parsing ingênuo).

Detalhamento e próximos passos: `docs/specs/analise-exploratoria/task.md`.

## Regra de acompanhamento

A cada etapa concluída, atualizar **`docs/specs/analise-exploratoria/task.md` e este
README** antes de seguir para a próxima (ver `CLAUDE.md`).
