from text_curation import TextCurator


def test_report_basic_stats():
    curator = TextCurator.from_profile("web_common_v1", collect_reports=True)

    out = curator({
        "text": ["Hello\n\nhello"]
    })

    report = out["curation_report"][0]

    # Two identical paragraphs in input
    assert report["input_stats"]["paragraphs"] == 2

    # Deduplication collapses them into one
    assert report["output_stats"]["paragraphs"] == 1