# Stage B2 retrieval ablation

**Development retrieval ablation: complete. Configuration freeze: pending. Heldout: not run.**

The gold set is marked human reviewed, and the seeded split remains 25 dev / 10 heldout. The heldout permission flag remains false. This ablation uses only the 14 answerable DOC and MIX questions in the dev split; it makes no generation or faithfulness claim.

Command run:

```powershell
.\.venv\Scripts\python.exe -m eval.run_eval --split dev --ablation
```

All six strategy/mode combinations completed with 14 queries each. Hit rates are proportions.

| Strategy | Mode | Queries | Hit@1 | Hit@3 | Hit@5 | MRR |
|---|---|---:|---:|---:|---:|---:|
| A | bm25 | 14 | 0.214 | 0.286 | 0.429 | 0.286 |
| A | dense | 14 | 0.214 | 0.357 | 0.500 | 0.310 |
| A | hybrid | 14 | 0.357 | 0.429 | 0.571 | 0.429 |
| B | bm25 | 14 | 0.214 | 0.286 | 0.429 | 0.286 |
| B | dense | 14 | 0.071 | 0.357 | 0.429 | 0.196 |
| B | hybrid | 14 | 0.214 | 0.429 | 0.571 | 0.318 |

A + hybrid has the highest dev MRR and ties B + hybrid on Hit@3 and Hit@5. It is the current retrieval development candidate. The dev-selected strategy is now recorded as `rag.chunking: fixed` (strategy A) in `config.yaml`; answer generation uses hybrid retrieval. The configuration has not been frozen. The run loaded `sentence-transformers/all-MiniLM-L6-v2` successfully and completed despite an unauthenticated Hugging Face Hub rate-limit warning.

`rag.min_score` is now provisionally calibrated from dev retrieval scores below; it is not frozen. Provider-backed generation remains unconfirmed after repeated 503 availability errors. Do not run heldout evaluation until the final configuration is committed and the required human faithfulness labels are complete.
## Dev-only refusal-threshold calibration

Using strategy A + hybrid, the best fused score was `0.027650648360030512` for the single unanswerable-from-corpus dev question R04. The lowest score among the 14 answerable DOC/MIX dev questions was `0.028373015873015873`. The interval separates these observed cases; the midpoint, `rag.min_score: 0.028012`, is recorded in `config.yaml`. At this threshold R04 is below threshold and all 14 answerable DOC/MIX dev questions are above it.

This calibration has only one unanswerable retrieval example, so the threshold is provisional and sensitive to that example. The three advice/prediction dev cases are refused by the OOS router and do not calibrate retrieval confidence. This setting is not frozen: `rag.frozen_at` and `rag.frozen_commit` remain unset. The split still has `heldout_run_permitted: false`.
