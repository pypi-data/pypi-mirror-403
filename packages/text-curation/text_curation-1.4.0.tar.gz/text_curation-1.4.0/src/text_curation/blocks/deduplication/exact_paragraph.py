from text_curation.blocks.base import Block
import re


class ExactParagraphDeduplicationBlock(Block):
    """
    Removes exact duplicate paragraphs within a document.

    Deduplication is local, order-preserving, and based on
    conservative normalization rules to avoid false positives.
    """

    DEFAULT_POLICY = {
        "scope": "paragraph",
        "normalize_case": True,
        "collapse_whitespace": True,
        "drop_empty": True,
    }

    def __init__(self, policy=None):
        # Merge caller policy with stable defaults
        merged = {**self.DEFAULT_POLICY, **(policy or {})}
        super().__init__(merged)

    def apply(self, document):
        """
        Deduplicate repeated paragraphs in-place.

        This block mutates document.text and does not emit signals.
        """
        text = document.text

        # Fast exit for empty documents
        if not text.strip():
            return document

        paragraphs = text.split("\n\n")

        seen = set()
        kept = []

        for para in paragraphs:
            key = self._normalize_key(para)

            # Skip empty or already-seen paragraphs
            if not key or key in seen:
                continue

            seen.add(key)
            kept.append(para)

        document.set_text("\n\n".join(kept))
        return document

    def _normalize_key(self, paragraph: str) -> str:
        """
        Generate a comparison key for deduplication.

        Normalization is intentionally minimal and non-semantic.
        """
        return re.sub(r"\s+", " ", paragraph.strip()).lower()