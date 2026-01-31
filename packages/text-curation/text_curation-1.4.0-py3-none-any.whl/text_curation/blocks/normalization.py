from text_curation.blocks.base import Block
import re
import unicodedata

# Invisible characters commonly introduced by copy/paste or OCR
_ZERO_WIDTH = re.compile(r"[\u200B\u200C\u200D\uFEFF]")

# Non-printable ASCII control characters
_CONTROL_CHARS = re.compile(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]")

# Canonical quote replacements
_QUOTES = {
    "“": '"', "”": '"',
    "‘": "'", "’": "'",
    "«": '"', "»": '"',
    "‚": "'",
    "`": "'",
}

# Canonical dash replacements
_DASHES = {
    "–": "-", "—": "-", "―": "-", "−": "-"
}


class NormalizationBlock(Block):
    """
    Performs low-level, non-semantic text normalization.

    This block standardizes Unicode representations and removes
    invisible or control characters commonly found in scraped or
    copied text. All transformations are deterministic and
    conservative.
    """

    def __init__(self, policy=None):
        super().__init__(policy)

    def apply(self, document):
        """
        Normalize document text in-place.

        This block mutates document.text but does not emit signals.
        """
        text = document.text

        text = self._normalize_unicode(text)
        text = self._remove_zero_width(text)
        text = self._remove_control_char(text)
        text = self._normalize_line_endings(text)
        text = self._normalize_quotes(text)
        text = self._normalize_dashes(text)
        text = self._normalize_ellipses(text)
        text = self._collapse_whitespaces(text)
        text = self._normalize_newlines(text)
        text = text.strip()

        document.set_text(text)

    def _normalize_unicode(self, text):
        return unicodedata.normalize("NFKC", text)

    def _remove_zero_width(self, text):
        return _ZERO_WIDTH.sub("", text)

    def _remove_control_char(self, text):
        return _CONTROL_CHARS.sub("", text)

    def _normalize_line_endings(self, text):
        return text.replace("\r\n", "\n").replace("\r", "\n")

    def _normalize_quotes(self, text):
        for k, v in _QUOTES.items():
            text = text.replace(k, v)
        return text

    def _normalize_dashes(self, text):
        for k, v in _DASHES.items():
            text = text.replace(k, v)
        return text

    def _normalize_ellipses(self, text):
        return text.replace("…", "...")

    def _collapse_whitespaces(self, text):
        lines = text.split("\n")
        out = []

        for line in lines:
            # Preserve leading indentation exactly
            prefix = len(line) - len(line.lstrip(" \t"))
            indent = line[:prefix]
            rest = line[prefix:]

            # Collapse internal whitespace only
            rest = re.sub(r"[ \t]+", " ", rest)

            out.append(indent + rest)

        return "\n".join(out)

    def _normalize_newlines(self, text):
        return re.sub(r"\n{3,}", "\n\n", text)
