# Command Registry

Run commands from the repository root. Use the project virtual environment.

## Environment

```powershell
.\.venv\Scripts\python.exe --version
.\.venv\Scripts\python.exe -m pip --version
```

## Make availability

On Windows, use the MSYS2 GNU Make executable:

```powershell
C:\msys64\ucrt64\bin\mingw32-make.exe help
```

The commands below assume `mingw32-make` is available on PATH.

## Setup and validation

```powershell
mingw32-make setup
mingw32-make test
mingw32-make test-db
mingw32-make verify
```

- `setup`: installs project dependencies.
- `test`: runs the offline test suite.
- `test-db`: runs the full test suite, including database integration tests.
- `verify`: runs README-number, dashboard-data, secrets, and repository-size checks.

## Data and analysis pipeline

```powershell
mingw32-make data
mingw32-make metrics
mingw32-make inference
mingw32-make figures
```

These targets run the corresponding project data, metrics, inference, and figure-generation steps.

## Retrieval index

```powershell
mingw32-make index
```

Rebuilds the retrieval index using the project's configured sources.

## Retrieval evaluation

Development evaluation requires explicit opt-in:

```powershell
mingw32-make eval RUN_EVAL=1 SPLIT=dev
```

Do not rerun the heldout evaluation for routine packaging or documentation checks. The heldout results are frozen and recorded in the project evidence.

## README and release checks

```powershell
mingw32-make readme
mingw32-make verify
```

Run the README update only when the underlying result exports have intentionally changed. Review the resulting diff before committing.

## Cleanup

```powershell
mingw32-make clean
```

Removes local test and Python cache artifacts. It does not remove project data or research outputs.

## Dashboard and packaging

The Power BI dashboard is maintained in `dashboard/MF_Audit_Dashboard.pbix`. Dashboard validation is included in `mingw32-make verify`.

The final project report is available at `reports/final_report.md`.

## Important limitations

- The estimated hybrid BSE TRI remains provisional and must not be described as actual BSE TRI.
- Historical TER disclosures are incomplete.
- The A1 test-collection issue remains documented.
- B1 retrieval limitations and B2 evaluation limitations are recorded in the corresponding reports.
- The live demo has been documented but not independently rehearsed.
- Do not claim a clean-clone validation until the clean-clone script has completed successfully.
