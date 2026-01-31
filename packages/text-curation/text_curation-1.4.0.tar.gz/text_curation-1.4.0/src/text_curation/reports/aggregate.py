from collections import defaultdict


def aggregate_reports(reports):
    """
    Aggregate a list of per-sample curation reports into a single
    dataset-level summary.

    This function reduces multiple per-document `curation_report`
    dictionaries into one consolidated view describing the net
    structural changes across the entire dataset.

    Args:
        reports:
            An iterable of per-sample curation reports, typically taken
            from a Hugging Face Dataset column (`dataset["curation_report"]`).

    Returns:
        dict:
            A dictionary containing aggregated corpus-level statistics
            with the following keys:

            - "samples":
                Total number of samples processed.

            - "input_stats":
                Sum of input text statistics (chars, lines, paragraphs)
                across all samples.

            - "output_stats":
                Sum of output text statistics after curation.

            - "block_stats":
                Optional per-block counters aggregated across samples.

            - "signals_summary":
                Aggregated count of emitted signals.
    """

    # Initialize aggregation containers.
    #
    # defaultdicts are used to simplify accumulation logic and avoid
    # repeated existence checks.
    agg = {
        "samples": len(reports),
        "input_stats": defaultdict(int),
        "output_stats": defaultdict(int),
        "block_stats": defaultdict(lambda: defaultdict(int)),
        "signals_summary": defaultdict(int),
    }

    # Iterate over each per-sample report and accumulate statistics.
    for r in reports:
        # Aggregate input text statistics.
        for key, value in r["input_stats"].items():
            agg["input_stats"][key] += value

        # Aggregate output text statistics.
        for key, value in r["output_stats"].items():
            agg["output_stats"][key] += value

        # Aggregate per-block statistics, if present.
        #
        # Not all blocks emit stats, so this section is optional.
        for block, stats in r.get("block_stats", {}).items():
            for key, value in stats.items():
                agg["block_stats"][block][key] += value

        # Aggregate emitted signals, if present.
        for key, value in r.get("signals_summary", {}).items():
            agg["signals_summary"][key] += value

    # Convert defaultdicts to plain dicts before returning.
    #
    # This ensures a stable, serialization-friendly return value and
    # avoids leaking implementation details to callers.
    return {
        "samples": agg["samples"],
        "input_stats": dict(agg["input_stats"]),
        "output_stats": dict(agg["output_stats"]),
        "block_stats": {
            block: dict(stats)
            for block, stats in agg["block_stats"].items()
        },
        "signals_summary": dict(agg["signals_summary"]),
    }