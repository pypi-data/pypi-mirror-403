from collections import defaultdict
from text_curation.blocks.base import Block


class SignalBasedBoilerplateFilteringBlock(Block):
    """
    Removes content based on explicit structure-derived signals.

    Filtering is conservative by default and limited to clearly
    defined cases such as repeated short boilerplate paragraphs.
    """

    DEFAULT_POLICY = {
        "drop_empty": True,
        "preserve_headers": True,
        "drop_repeated_boilerplate": True,
        "min_repetition": 2,
        "max_boilerplate_length": 200,
    }

    def __init__(self, policy=None):
        # Merge caller policy with stable defaults
        merged = {**self.DEFAULT_POLICY, **(policy or {})}
        super().__init__(merged)

    def apply(self, document):
        """
        Filter paragraphs based on structure signals.

        This block mutates document.text and does not emit signals.
        """
        text = document.text

        if not text.strip():
            document.set_text("")
            return document

        paragraphs = text.split("\n\n")
        signals = document.signals

        para_signals = self._group_paragraph_signals(signals)
        kept_paragraphs = []

        for idx, para in enumerate(paragraphs):
            sigs = para_signals.get(idx, {})

            if self._should_drop_paragraph(para, sigs):
                continue

            kept_paragraphs.append(para)

        document.set_text("\n\n".join(kept_paragraphs))
        return document

    def _should_drop_paragraph(self, paragraph: str, sigs: dict) -> bool:
        """
        Decide whether a paragraph should be dropped.

        Decisions are explicit, signal-based, and conservative.
        """
        stripped = paragraph.strip()

        if not stripped:
            return True

        # Preserve header-led sections explicitly
        if sigs.get("starts_with_header"):
            return False

        # Drop only short, repeated boilerplate candidates
        if (
            sigs.get("is_boilerplate_candidate")
            and sigs.get("repetition_count", 0) >= 2
            and len(stripped) < 200
        ):
            return True

        return False

    def _group_paragraph_signals(self, signals):
        """
        Group flat signal list into a paragraph-indexed structure.
        """
        grouped = defaultdict(dict)

        for sig in signals:
            if not sig.name.startswith("paragraph["):
                continue

            prefix, key = sig.name.split("].", 1)
            idx = int(prefix[len("paragraph[") :])

            grouped[idx][key] = sig.value

        return grouped