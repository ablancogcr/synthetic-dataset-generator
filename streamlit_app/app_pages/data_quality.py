"""Generator validation report viewer."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from streamlit_app.utils.shared import page_intro, require_dataset
from streamlit_app.utils.streamlit_cache import load_validation_cached, optional_mtime
from streamlit_app.utils.validation_loader import ValidationLoadError

page_intro(
    "Data quality",
    "The validation artifacts produced by the generator for the selected dataset.",
)
dataset_path = require_dataset()
json_path = dataset_path / "validation_summary.json"
markdown_path = dataset_path / "validation_summary.md"

try:
    report = load_validation_cached(
        str(dataset_path), optional_mtime(json_path), optional_mtime(markdown_path)
    )
except ValidationLoadError as exc:
    st.error(str(exc))
    st.stop()

if report is None:
    st.info(
        "No validation report is available. This can happen when files were copied without "
        "`validation_summary.json` and `validation_summary.md`."
    )
    st.stop()

status = report.overall_status.lower()
if status == "passed":
    st.success("Overall validation status: PASSED", icon=":material/check_circle:")
elif status == "failed":
    st.error("Overall validation status: FAILED", icon=":material/error:")
else:
    st.warning("Overall validation status is not available from JSON.")

with st.container(horizontal=True):
    st.metric("Passed checks", f"{report.checks_passed:,}", border=True)
    st.metric("Failed checks", f"{len(report.failed_checks):,}", border=True)
    st.metric("Warnings", f"{len(report.warnings):,}", border=True)
    st.metric("Total checks", f"{report.checks_total:,}", border=True)

if report.checks:
    checks = pd.DataFrame(report.checks)
    if "passed" in checks:
        checks.insert(
            1,
            "status",
            checks["passed"].map({True: "Passed", False: "Failed"}).fillna("Unknown"),
        )
    preferred = [column for column in ("name", "status", "details") if column in checks]
    remaining = [column for column in checks if column not in preferred and column != "passed"]
    st.subheader("Validation checks")
    st.dataframe(checks[preferred + remaining], hide_index=True)

    if report.failed_checks:
        st.subheader("Failed checks")
        st.dataframe(pd.DataFrame(report.failed_checks), hide_index=True)

if report.markdown:
    with st.expander("Human-readable validation summary"):
        st.markdown(report.markdown)
else:
    st.caption("`validation_summary.md` is not available for this dataset.")

st.caption(
    "These are the generator's own validation results. The viewer does not run a second "
    "independent validation engine."
)
