# Validation Report Reference

Each generation run writes `validation_summary.json` for automation and `validation_summary.md` for
human review. Both report the same named checks and an overall pass/fail result.

Checks cover required tables and files, exact declared schemas, primary and composite keys, foreign
keys, accepted statuses and payment methods, review range, state abbreviations, non-negative money,
delivered-order date order, payment reconciliation, one shipping row per order, shipping-cost
reconciliation, delivered-order review eligibility, populated scenarios, and seller-churn cutoffs.

The CLI creates a ZIP only when the overall result passes. If validation fails, inspect the retained
folder and summaries, correct the generator or configuration, and rerun with `--overwrite`. Validation
supports internal consistency; it does not certify the synthetic distributions as real market data.

