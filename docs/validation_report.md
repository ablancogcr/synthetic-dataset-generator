# Validation Report Reference

Each generation run writes `validation_summary.json` for automation and `validation_summary.md` for
human review. Both report the same named checks and an overall status of `passed`, `expected_issues`,
or `failed`.

Checks cover required tables and files, exact declared schemas, primary and composite keys, foreign
keys, accepted statuses and payment methods, review range, state abbreviations, non-negative money,
delivered-order date order, payment reconciliation, one shipping row per order, shipping-cost
reconciliation, delivered-order review eligibility, populated scenarios, and seller-churn cutoffs.

Clean runs create a ZIP only when every check passes. Dirty runs first run the same checks against the
clean source, then audit the serialized CSVs against private deterministic targets. Correctly
preserved defects have check status `expected_issue`, create a ZIP, and return success. A dirty
package also includes `dirty_data_manifest.json` with counts but no exact locations.

`checks_passed`, `checks_expected_issues`, and `checks_failed` separate the three outcomes while the
existing per-check `passed` field remains available. If validation is `failed`, inspect the retained
folder and summaries, correct the generator or configuration, and rerun with `--overwrite`.
Validation supports internal consistency; it does not certify the synthetic distributions as real
market data.
