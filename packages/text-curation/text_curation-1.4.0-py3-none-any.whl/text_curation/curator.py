from text_curation.core.pipeline import Pipeline
from text_curation.registry import get_profile


class TextCurator:
    """
    High-level wrapper for applying text curation pipelines to datasets.
    """

    def __init__(self, profile, collect_reports: bool = False):
        self.profile = profile
        self.collect_reports = collect_reports
        self.pipeline = Pipeline(profile.blocks)

    @classmethod
    def from_profile(cls, profile_id, *, collect_reports: bool = False):
        profile = get_profile(profile_id)
        return cls(profile, collect_reports=collect_reports)

    def __call__(self, batch):
        texts = batch["text"]

        if not self.collect_reports:
            cleaned = [self.pipeline.run(t) for t in texts]
            return {"text": cleaned}

        cleaned = []
        reports = []

        for t in texts:
            doc, report = self.pipeline.run_document(
                t,
                collect_report=True,
                profile_id=self.profile.id,
            )
            cleaned.append(doc.text)
            reports.append(report.to_dict())

        # ✅ RETURN AFTER LOOP
        return {
            "text": cleaned,
            "curation_report": reports,
        }
