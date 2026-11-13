# Human Tasks

Stage 0 manual actions will be appended here.

## Stage A2

- [x] Generate `results/dq_report.csv` and verify zero `FAIL` rows. Eight benchmark-coverage WARNs remain documented.
- [x] Restore/provide the Stage A2 runbook/specification.
- [x] Complete Stage A2, including factsheet cross-checks and explicit handling of the eight schemes without historical BSE benchmark TRI.

## Stage A1

- [ ] Resolve the incomplete pytest test collection. The previous A1 pytest invocation collected no tests. Investigate and add or restore the intended A1 tests; do not treat the passing A2 tests as a substitute.

## BSE Benchmark Fallback

- [x] Download BSE 500 daily price-index history.
- [x] Download BSE 100 daily price-index history.
- [x] Download NIFTY 500 daily price-index history.
- [x] Download NIFTY 100 daily price-index history.
- [x] Verify date coverage, index identity, and source provenance for all four files.
- [ ] Obtain actual BSE 100 TRI and BSE 500 TRI from BSE Index Services if available.
- [ ] Replace estimated hybrid series with actual BSE TRI when received.
- [ ] Compare estimated and actual BSE TRI results after replacement.

- [x] Benchmark confirmation waiver approved: estimated hybrid BSE TRI is the primary provisional series; NIFTY TRI remains a separate sensitivity. Original benchmark mappings are unchanged.

### Methodological limitations

- Estimated hybrid series are provisional and are not actual BSE TRI.
- NIFTY TRI results are separate sensitivity results.
- The original preregistration remains unchanged; the fallback is a documented methodological deviation.