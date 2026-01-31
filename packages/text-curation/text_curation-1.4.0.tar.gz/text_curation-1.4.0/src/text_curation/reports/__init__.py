"""
Reporting utilities for text-curation.

This module exposes high-level helpers for inspecting and summarizing
curation runs when report collection is enabled.
"""

# Human-readable, dataset-level summary printer.
# This function consumes a Hugging Face Dataset containing a
# `curation_report` column and prints an aggregated summary.
from .summary import summary

# Low-level aggregation helper.
# This function aggregates per-sample curation reports into a single
# dictionary of corpus-level statistics.
from .aggregate import aggregate_reports


# Public API of the reports package.
#
# Only the documented, stable entry points are exported.
# Internal helpers should not be imported directly by users.
__all__ = [
    "summary",
    "aggregate_reports",
]