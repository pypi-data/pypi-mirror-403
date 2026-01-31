import re
from text_curation.blocks.base import Block

_CODE_INDENT = re.compile(r"^[ \t]+")
_SENTENCE_END = re.compile(r"[.!?]['\"]?$")
_CONTINUATION_START = re.compile(r"[a-z]")

_URL = re.compile(r"https?://\S+")
_EMAIL = re.compile(r"\b\S+@\S+\b")
_IP = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
_NUMBER = re.compile(r"\b\d{1,3}(?:,\d{3})+\b")
_NUMERIC_COLON = re.compile(r"\b\d+:\d+\b")


class ParagraphFormattingBlock(Block):
    """
    Faithful paragraph reconstruction that mirrors the original
    single-file FormattingBlock behavior.
    """

    DEFAULT_POLICY = {
        "normalize_punctuation": True,
    }

    def __init__(self, policy=None):
        super().__init__({**self.DEFAULT_POLICY, **(policy or {})})

    def apply(self, document):
        text = document.text
        text = self._normalize_paragraph_boundaries(text)

        if self.policy["normalize_punctuation"]:
            text = self._normalize_punctuation_spacing(text)

        document.set_text(text)
        return document
    
    def _normalize_paragraph_boundaries(self, text):
        lines = text.split("\n")
        out = []
        buffer = []
        prose_paragraph = False  # 🔑 track paragraph intent

        def flush():
            nonlocal buffer, prose_paragraph
            if not buffer:
                return
            if prose_paragraph and len(buffer) > 1:
                out.append(" ".join(buffer))
            else:
                out.extend(buffer)
            buffer = []
            prose_paragraph = False

        for line in lines:
            # Preserve code blocks
            if _CODE_INDENT.match(line):
                flush()
                out.append(line)
                continue

            # Blank line = paragraph boundary
            if not line.strip():
                flush()
                out.append("")
                continue

            stripped = line.strip()

            if not buffer:
                # Decide paragraph type on first line
                prose_paragraph = stripped and stripped[0].isupper()
                buffer.append(stripped)
                continue

            prev = buffer[-1]

            # Continue wrapped prose
            if (
                prose_paragraph
                and not _SENTENCE_END.search(prev)
                and stripped[0].islower()
            ):
                buffer.append(stripped)
                continue

            flush()
            prose_paragraph = stripped[0].isupper()
            buffer.append(stripped)

        flush()
        return "\n".join(out)

    def _normalize_punctuation_spacing(self, text):
        text = re.sub(r"([!?]){2,}", r"\1", text)
        text = re.sub(r"\.{4,}", "...", text)

        placeholders = {}

        def stash(match):
            key = f"__TOK{len(placeholders)}__"
            placeholders[key] = match.group(0)
            return key

        text = _URL.sub(stash, text)
        text = _EMAIL.sub(stash, text)
        text = _IP.sub(stash, text)
        text = _NUMBER.sub(stash, text)
        text = _NUMERIC_COLON.sub(stash, text)

        text = re.sub(r"\s+([,!?;:])", r"\1", text)
        text = re.sub(r"([,!?;:])([^\s])", r"\1 \2", text)

        for k, v in placeholders.items():
            text = text.replace(k, v)

        return text
