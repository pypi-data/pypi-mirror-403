import re
from text_curation.blocks.base import Block


class CodeSafeFormattingBlock(Block):
    """
    Structural safety layer: whitespace + blank lines only.
    """

    DEFAULT_POLICY = {}

    def __init__(self, policy=None):
        super().__init__({**self.DEFAULT_POLICY, **(policy or {})})

    def apply(self, document):
        text = document.text
        text = self._normalize_line_endings(text)
        text = self._trim_trailing_white_spaces(text)
        text = self._collapse_blank_lines(text)
        document.set_text(text)
        return document

    def _normalize_line_endings(self, text):
        return text.replace("\r\n", "\n").replace("\r", "\n")

    def _trim_trailing_white_spaces(self, text):
        return "\n".join(line.rstrip() for line in text.split("\n"))

    def _collapse_blank_lines(self, text):
        return re.sub(r"\n{3,}", "\n\n", text)