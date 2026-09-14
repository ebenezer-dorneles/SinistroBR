# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

Exploratory-analysis dashboard project over `data/raw/por_pessoa_acidentes2025.csv`, a Polícia
Rodoviária Federal (PRF) traffic-accident dataset with **one row per person involved** in an
accident (not one row per accident). The project has moved through ETL (Fase 1), per-dimension EDA
(Fase 2), and cross-dimension hypothesis testing (Fase 3); the dashboard itself (Fase 4+) has not
started. See `README.md` "Status do projeto" for the current phase and `docs/specs/analise-exploratoria/spec.md`
for the field catalog, data-quality issues, and ETL design — read it before any data work here.

## Commands

```bash
pip install -r requirements.txt

python -m src.etl.pipeline               # writes data/processed/acidentes2025.parquet + quality report
python -m src.eda.dimensoes.<nome>       # one dimension module = numbers + figures in reports/figuras/<nome>/
python -m src.eda.hipoteses.<nome>       # one hypothesis module = tests + figures for that sub-phase

pytest -q                                 # full suite
pytest tests/test_etl.py -q               # single file
pytest tests/test_etl.py::test_name -q    # single test
```

Dimension modules: `temporal`, `geografico`, `causa_tipo`, `via_ambiente`, `veiculo`, `vitima`,
`condutor`, `consistencia`. Hypothesis modules: `pedestre`, `moto_perfil`, `tempo`, `via`,
`pontos_negros`. Each has a matching `tests/test_*.py`.

## Architecture

**Pipeline shape:** `src/etl/pipeline.py` (Fase 1) reads the raw CSV, applies the type/sentinel
normalizations below, and persists `data/processed/acidentes2025.parquet`. Everything downstream
goes through `src.eda.dataset.load_enriched()`, which runs the ETL in memory (or loads the
parquet with `from_parquet=True`) and applies `src.eda.enrich.enriquecer` (derived columns: `mes`,
`dia_semana_ord`, `hora`, `faixa_etaria`, canonicalized `tracado_via` indicators, `marca_normalizada`/
`modelo`, `causa_macro`).

**Never call `len(df)` or filter the raw dataframe ad hoc for a denominator.** Every statistic in
Fase 2/3 goes through one of three unit cuts in `src/eda/dataset.py` — `por_acidente` (72,529),
`por_veiculo` (139,517), `por_pessoa` (194,629) — plus `apenas_vitimas`/`apenas_condutores` filters.
`checar_denominadores()` asserts these counts and is meant to fail loudly if enrichment logic
drifts. `src/eda/severity.py` layers severity metrics (`taxa_letalidade_por_pessoa`,
`resumo_severidade`, etc.) on top of these cuts.

**Fase 3 statistical framework** lives in `src/eda/inferencia.py`: Wilson CI for rates
(`taxa_com_ic`), Katz CI for risk ratio (`rr_com_ic`), `tabela_estratificada`,
`padronizacao_direta` (age/vehicle-type adjustment), and `veredito()`, which classifies a
hypothesis as confirmed/confounded/rejected/inconclusive by **effect size, not p-value** — with
n=194,629 everything is "significant". The cutoff (`MIN_DELTA_PP`, `MIN_RR`, `MIN_N_CELULA`) is
fixed in `src/const.py`, decided *before* running the first hypothesis (see plan.md Fase 3,
Premissa 2) — do not tune it post hoc to make a hypothesis land one way or the other. Every
severity comparison across hypotheses must report both bruto and ajustado (adjusted for
`faixa_etaria` + `tipo_veiculo`) — an unadjusted comparison is not a valid finding here.

**`src/const.py`** is the single source of paths, seeds, quality thresholds, denominators, and
category-mapping dicts (`CAUSA_MACRO`, `MARCA_SINONIMOS`, ...) for both ETL and EDA. It mirrors
`docs/specs/analise-exploratoria/const.md` (which explains the *why* for each value) — never
hardcode a magic number, path, or threshold in a script; import it from here, and update both
files together when introducing a new one.

## Critical data gotchas (verified against the raw file)

These are not obvious from the file structure and have caused parsing bugs before — confirm any
ETL/loading code accounts for them:

- **Encoding is ISO-8859-1 (Latin-1), not UTF-8.** Reading without `encoding="latin-1"` corrupts
  every accented text field (`causa_acidente`, `tipo_veiculo`, etc.).
- **Delimiter is `;` with quoted fields, and some values contain a literal `;` inside the quotes**
  (e.g. `tracado_via` can be `"Reta;Declive"`). Never split lines naively on `;` — always use a
  real CSV parser that respects quoting (e.g. `pandas.read_csv(sep=";", quotechar='"')`).
- **Decimal separator is a comma**, not a period (e.g. `latitude = -23,48586772`). Use
  `decimal=","` on read or convert explicitly.
- **Missing values are represented inconsistently**: empty string, `"NA"`, `"Não Informado"` /
  `"Não Informado/Não Informado"`, `"Ignorado"`. These are normalized to a single null
  representation in `load_raw`.
- **`0` is a legitimate value, not a missing-data sentinel, for `ilesos`, `feridos_leves`,
  `feridos_graves`, `mortos`** (they're per-person binary indicators). By contrast, `idade == 0`,
  `ano_fabricacao_veiculo == 0`, `pesid == 0`, `id_veiculo == 0`, and `br == 0` are confirmed
  missing-data sentinels (see `normalize_*_sentinel` in `src/etl/pipeline.py` and Fase 2.8's
  `revalidar_idade_zero`) and are converted to `NaN`.
- **Driver identification**: filter `tipo_envolvido == "Condutor"` to isolate drivers. Grouping by
  `(id, id_veiculo)` yields at most one `"Condutor"` row — the field is safe to treat as a unique
  driver-per-vehicle-per-accident indicator. The data is anonymized (no name/CPF), so individual
  people cannot be tracked across accidents.
- Row uniqueness key is `(id, pesid)` — `id` identifies the accident, `pesid` the person;
  `id_veiculo` groups rows belonging to the same vehicle within an accident.
- The dataset has **no measured speed, blood-alcohol level, seatbelt/helmet use, fleet/road-network
  exposure, or rescue-time data**. `Velocidade Incompatível` / `Ingestão de álcool pelo condutor`
  in `causa_acidente` are the officer's subjective attribution on the police report, not a
  measurement — treat any speed/alcohol finding as indicative, never causal.

## Spec-driven development workflow

This project follows a spec-driven workflow built around four documents, one per concern, all
under `docs/specs/<feature>/` (currently only `analise-exploratoria/`). Do not blend these
concerns into one file, and do not skip straight to code/exploration before `spec.md` is
reasonably settled (even for an MVP).

### `spec.md` — the problem contract
Answers **what / why / under what constraints**. Written first, changed rarely (only on an
official change in project direction or business rules).
- Business pain and success metrics (business KPIs + target technical metrics).
- Initial hypotheses to investigate scientifically.
- Data sources and governance concerns (e.g. LGPD/PII).
- System boundary constraints (batch vs. real-time, latency, environment) — without pre-choosing
  specific libraries or models.
- An explicit "Out of scope" section to protect focus.

### `plan.md` — the methodological/execution map
Answers **how to approach it scientifically / when**. Written right after `spec.md` closes (or
after exploratory-phase insights); consulted at the start of each sprint/experimentation cycle.
- Problem formulation and chosen tech stack.
- How each `spec.md` hypothesis will be tested and in which phase.
- Project phases (e.g. 1. Acquisition & EDA, 2. Feature Engineering, 3. Modeling, 4.
  Productization/Delivery).
- Milestones with verifiable exit criteria.

### `task.md` — the day-to-day log
Answers **what to do right now**, tactically. A living document updated continuously while coding,
running experiments, refactoring pipelines, or hitting blockers.
- Plan phases broken into atomic, trackable tasks (hours, at most 1–2 days).
- Organized as `[ ] Backlog`, `[ ] Em Progresso`, `[x] Concluídas`, `[ ] Bloqueadas` (blocked items
  always documented with reason/ticket/dependency).

### `const.md` — the control panel / reproducibility surface
Answers **with which values and limits**. Reach for this instead of hardcoding magic numbers,
directories, or thresholds in scripts/notebooks/pipelines — it is the readable mirror of
`src/const.py`.
- Directory paths (`RAW_DATA_PATH`, `PROCESSED_DATA_PATH`, ...).
- Reproducibility seeds (`RANDOM_SEED`).
- Data-quality rules/thresholds and Fase 3 effect-size cutoffs (`MIN_DELTA_PP`, `MIN_RR`, ...).

| File | Key question | Update frequency |
| :--- | :--- | :--- |
| `spec.md` | O quê? Por quê? | Low — only on scope/business changes |
| `plan.md` | Como abordar? Quando? | Medium — each phase/sprint change |
| `task.md` | O que fazer hoje? | High — daily / multiple times a day |
| `const.md` | Com quais parâmetros? | Medium — when introducing new params/paths |

### Progress-tracking rule (mandatory)

Every time a step/task is finished, and before moving on to the next one, you MUST update **both**:

1. `docs/specs/analise-exploratoria/task.md` — move the item to `Concluídas` (or the right
   section), keeping the pointer to the file/function that implements it and any `**Achado:**`
   note.
2. `README.md` — keep its "Status do projeto" section in sync with what is actually done (current
   phase, what's implemented, what's blocked).

Do not batch these updates to the end of a work session — update as each step completes. Findings
from a completed dimension/hypothesis module also belong in
`docs/specs/analise-exploratoria/achados-eda.md` or `resultados-fase3.md` respectively, one entry
per evidence line — follow the existing entries' format in those files rather than inventing a new
one.

## Working with the dataset directly

Prefer `pandas.read_csv` (or `src.eda.load_enriched()`) over shell text tools for anything beyond a
quick spot-check — naive `awk -F';'` splitting silently misaligns columns on rows with quoted
embedded semicolons (see gotchas above). `iconv` + `awk`/`python3` one-liners are fine for a quick
look at the raw file only.
