# Command Registry

Run commands from the project root using the project virtual environment.

## Environment

```powershell
.\.venv\Scripts\python.exe --version
```

## Stage A3 - Statistical Analysis and Inference

Run after confirming the PostgreSQL database and required source data are available. `a3_extract_ter.py` stops without changing `scheme_facts.csv` unless all 16 Direct/Regular pairs validate.

```powershell
.\.venv\Scripts\python.exe scripts\a3_extract_ter.py
.\.venv\Scripts\python.exe -m src.verify_data
.\.venv\Scripts\python.exe -m src.regression
.\.venv\Scripts\python.exe -m src.fdr
.\.venv\Scripts\python.exe -m src.persistence
.\.venv\Scripts\python.exe -m src.fee_gap
.\.venv\Scripts\python.exe -m src.control_check
.\.venv\Scripts\python.exe -m src.robustness
.\.venv\Scripts\python.exe -m src.mandate_audit
.\.venv\Scripts\python.exe -m src.figures_a3
```

Report: `reports/stage_A3_report.md`.

Interpret results in light of the 30-Sep-2026 TER snapshot and provisional estimated hybrid BSE benchmarks. Do not describe estimated hybrid series as actual BSE TRI.

## Stage A4 - Dashboard validation

Validate the exported dashboard data:

```powershell
.\.venv\Scripts\python.exe src/validate_dashboard_data.py
```

Run the dashboard contract tests:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_dashboard_contract.py -q
```

Run the complete project test suite:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Expected completed-project results at A4 closure:

- Dashboard data validator: PASS, 11 files, 0 warnings.
- Dashboard contract tests: 6 passed.
- Full project test suite: 11 passed.

The five-value dashboard cross-check is documented in the A4 report.

## Stage A4 - Human review

Review:

- `dashboard/MF_Audit_Dashboard.pbix`
- `dashboard/CHECKLIST.md`
- `dashboard/dashboard_imgs/`
- `reports/stage_A4_report.md`
- `reports/stage_A4_dashboard_report.md`

The screenshots are retained at their native resolution rather than upscaled to 1920 x 1080. This is a documented and accepted deviation.

## Stage B2 - SQL and evaluation

Run the offline B2 checks:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_b2_units.py -q
```

Run the PostgreSQL checks using the configured read-only role:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_entities.py tests\test_b2_sql_integration.py -q
```

`eval/gold_questions.csv` is a machine-drafted candidate set. A human must review every row before the evaluation runner will proceed. After review, mark each row's `notes` with the `HUMAN_APPROVED:` prefix and set `eval/split.json` status to `human_reviewed`. Then run the development ablation:

```powershell
.\.venv\Scripts\python.exe -m eval.run_eval --split dev --ablation
```

Do not run held-out evaluation until development tuning is complete and `config.yaml` contains the frozen `rag.min_score`, `rag.frozen_at`, and `rag.frozen_commit` values. Also set `heldout_run_permitted` in `eval/split.json` only after human review. The runner blocks held-out execution until all gates are satisfied.

For B2 generation, check provider availability using only a synthetic prompt first. The dev runner requires a successful synthetic preflight for the configured model within 24 hours. The preflight itself is bounded to one 30-second HTTP attempt; the SDK default of five hidden attempts is disabled. It uses the read-only database role, the dev split, and adds the six approved O01-O06 smoke questions only to the faithfulness sample; they do not modify the gold CSV or split. Held-out additionally requires the frozen config, explicit permission, and 20 completed faithfulness labels.

```powershell
.\.venv\Scripts\python.exe -m eval.run_generation_eval --preflight
.\.venv\Scripts\python.exe -m eval.run_generation_eval --split dev
```

## Project status and outstanding work

See `PROJECT_STATE.json` and `reports/HUMAN_TODO.md` for authoritative status.

Outstanding items include the inherited A1 test-collection issue, actual BSE TRI acquisition and replacement if available, and future B1, B2, and C stages.
