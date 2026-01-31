from .aggregate import aggregate_reports

PREFFERED_METRICS_ORDER = [
    "chars",
    "words",
    "lines",
    "paragraphs"
]

def summary(dataset):
    """
    Print a human-readable, dataset-level summary of a curation run.

    This function consumes a Hugging Face Dataset containing a
    `curation_report` column (produced when `collect_reports=True`)
    and prints an aggregated overview of how the dataset changed
    during curation.

    The summary is descriptive only and does not modify the dataset.
    """

    # Validate that curation reports are present.
    # Reports are only available when the curator is run with
    # `collect_reports=True`.
    if "curation_report" not in dataset.column_names:
        raise ValueError(
            "Dataset does not contain 'curation_report'. "
            "Run the curator with 'collect_reports=True'"
        )

    # Extract per-sample reports and aggregate them into
    # corpus-level statistics.
    reports = dataset["curation_report"]
    agg = aggregate_reports(reports)

    # ──────────────────────────────
    # Header
    # ──────────────────────────────
    print("Curation Summary")
    print("=" * 27)
    print(f"Samples Processed: {agg['samples']}")
    print()

    # ──────────────────────────────
    # Text Size Table
    # ──────────────────────────────
    #
    # Build rows for a closed, box-drawn table summarizing
    # structural text changes across the dataset.
    #
    # Metrics are aggregated totals (not per-sample averages).
    rows = []
    metrics = list(agg["input_stats"].keys())
    ordered = [m for m in PREFFERED_METRICS_ORDER if m in metrics]
    remaining = sorted(m for m in metrics if m not in ordered)
    for metric in ordered+remaining:
        inp = agg["input_stats"][metric]
        out = agg["output_stats"].get(metric, 0)

        # Absolute change (output − input).
        diff = out - inp

        # Percentage change relative to input.
        # Guard against division by zero.
        percent = (diff / inp) * 100 if inp else 0

        rows.append(
            (
                metric.capitalize(),
                f"{inp:,}",
                f"{out:,}",
                f"{diff:+,}",
                f"{percent:+.4f}%",
            )
        )

    # Table headers and column widths.
    headers = ("Metric", "Input", "Output", "Δ (Change)", "% Change")
    widths = [
        max(len(row[i]) for row in rows + [headers])
        for i in range(5)
    ]

    # Helper to draw horizontal table borders using box-drawing characters.
    def hline(left, mid, right):
        return left + mid.join("─" * (w + 2) for w in widths) + right

    # Render table header.
    print(hline("┌", "┬", "┐"))
    print(
        "│ "
        + " │ ".join(h.ljust(w) for h, w in zip(headers, widths))
        + " │"
    )
    print(hline("├", "┼", "┤"))

    # Render table rows.
    for row in rows:
        print(
            "│ "
            + " │ ".join(
                row[i].ljust(widths[i]) if i == 0 else row[i].rjust(widths[i])
                for i in range(5)
            )
            + " │"
        )

    # Render table footer.
    print(hline("└", "┴", "┘"))
    print()

    # ──────────────────────────────
    # Block Activity
    # ──────────────────────────────
    #
    # Optional section showing aggregated per-block counters,
    # if any blocks emit statistics.
    if agg["block_stats"]:
        print("Block Activity")
        print("-" * 72)
        for block, stats in agg["block_stats"].items():
            print(block)
            for key, value in stats.items():
                print(f"   {key}: {value}")
        print()

    # ──────────────────────────────
    # Signals
    # ──────────────────────────────
    #
    # Optional section showing aggregated signals emitted
    # during curation (e.g., structural or heuristic markers).
    if agg["signals_summary"]:
        print("Signals")
        print("-" * 72)
        for key, value in sorted(agg["signals_summary"].items()):
            print(f"{key}: {value}")
        print()
