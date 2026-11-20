PYTHON ?= .venv/Scripts/python.exe
PYTEST = $(PYTHON) -m pytest
SPLIT ?= dev
RUN_EVAL ?= 0

.PHONY: help setup data metrics inference figures index eval readme verify test test-db clean

help:
	echo "MF-Audit project commands"
	echo "  setup      Install pinned dependencies"
	echo "  data       Load processed datasets into PostgreSQL"
	echo "  metrics    Calculate and export metrics"
	echo "  inference  Run statistical inference pipeline"
	echo "  figures    Generate A3 figures"
	echo "  index      Ingest PDFs and build dense indexes"
	echo "  eval       Explicitly opt in to retrieval evaluation"
	echo "  readme     Refresh README results"
	echo "  verify     Run packaging and dashboard checks"
	echo "  test       Run offline tests"
	echo "  test-db    Run complete test suite (requires PostgreSQL)"
	echo "  clean      Remove disposable caches"

setup:
	$(PYTHON) -m pip install -r requirements.lock.txt

# Writes to PostgreSQL. Requires processed input datasets and DATABASE_URL.
data:
	$(PYTHON) -m src.load_all

# Reads PostgreSQL and overwrites metrics CSV outputs.
metrics:
	$(PYTHON) -m src.metrics_pandas
	$(PYTHON) src/export_metrics.py

# Re-runs the A3 statistical analysis pipeline.
inference:
	$(PYTHON) -m src.verify_data
	$(PYTHON) -m src.regression
	$(PYTHON) -m src.fdr
	$(PYTHON) -m src.persistence
	$(PYTHON) -m src.fee_gap
	$(PYTHON) -m src.control_check
	$(PYTHON) -m src.robustness
	$(PYTHON) -m src.mandate_audit

figures:
	$(PYTHON) -m src.figures_a3

# Rewrites the document manifest, extracted pages and dense index files.
index:
	$(PYTHON) -m src.rag.ingest
	$(PYTHON) -m src.rag.embed

# Evaluation is deliberately blocked unless explicitly enabled.
eval:
	@if [ "$(RUN_EVAL)" != "1" ]; then echo "Blocked: set RUN_EVAL=1 to explicitly run retrieval evaluation."; exit 2; fi
	$(PYTHON) -m eval.run_eval --split $(SPLIT) --ablation

readme:
	$(PYTHON) scripts/inject_results.py

verify:
	$(PYTHON) scripts/verify_readme_numbers.py
	$(PYTHON) src/validate_dashboard_data.py
	$(PYTHON) scripts/secrets_scan.py
	$(PYTHON) scripts/repo_size_check.py

# Offline suite: excludes tests requiring PostgreSQL.
test:
	$(PYTEST) -q --ignore=tests/test_b2_sql_integration.py --ignore=tests/test_entities.py

# Full suite. Requires READONLY_DATABASE_URL and a reachable PostgreSQL instance.
test-db:
	$(PYTEST) -q

clean:
	rm -rf .pytest_cache .ruff_cache
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
