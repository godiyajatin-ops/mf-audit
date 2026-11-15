# Mutual Fund Audit

An educational research project auditing active vs passive mutual funds, with a focus on risk-adjusted performance, benchmark-relative returns, costs, and mandate-vs-behavior analysis.

**Not investment advice.**

## Project status

| Stage | Status |
|---|---|
| Stage 0 - Feasibility and Pre-registration | COMPLETE_WITH_LIMITATIONS |
| Stage A1 - Data Pipeline | PASS (inherited test-collection issue remains open) |
| Stage A2 - SQL Metrics | PASS |
| Stage A3 - Statistical Analysis and Inference | COMPLETE_WITH_LIMITATIONS |
| Stage A4 - Power BI Dashboard | PASS |
| Stage B1 - Document Ingestion and Indexing | TODO |
| Stage B2 - Mandate-vs-Behavior Analysis | TODO |
| Stage C - Final Research Synthesis | TODO |

## Current research limitations

- Eight scheme-plan records use provisional estimated hybrid BSE benchmarks because actual BSE TRI history is unavailable.
- TER comparisons use a 30-Sep-2026 snapshot, not a historical five-year TER series.
- Survivorship effects remain unclear.
- The inherited Stage A1 pytest collection issue remains unresolved.

The estimated hybrid benchmark is not actual BSE TRI. NIFTY TRI results are retained as a separate sensitivity analysis. The original preregistration remains unchanged; the fallback is a documented methodological deviation.

## Stage A4 deliverables

- Power BI dashboard: `dashboard/MF_Audit_Dashboard.pbix`
- Dashboard data pack: `dashboard/MF_Audit_DataPack.xlsx`
- Dashboard CSV exports: `dashboard/data/`
- Dashboard validation: `src/validate_dashboard_data.py`
- Human review checklist: `dashboard/CHECKLIST.md`
- Stage report: `reports/stage_A4_report.md`

## Project documentation

- `PROJECT_STATE.json` - authoritative stage status and outstanding items
- `reports/HUMAN_TODO.md` - human actions and unresolved limitations
- `docs/COMMANDS.md` - reproducible execution and validation commands
- `docs/data_lineage.md` - data provenance and lineage
- `reports/` - stage reports and analysis outputs

## Environment

The project uses Python 3.11 and PostgreSQL. Run Python commands from the project root using the project virtual environment:

```powershell
.\.venv\Scripts\python.exe
```
