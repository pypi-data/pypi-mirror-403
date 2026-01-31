from text_curation.core.signals import Signal


class Document:
    """
    Container for text and associated processing artifacts.

    A Document holds the mutable text being processed along with
    emitted signals and annotations. It is the shared state passed
    through all blocks in a pipeline.
    """

    def __init__(self, text: str):
        """
        Initialize a new Document.

        Args:
            text: Raw input text to be curated
        """
        self.text = text
        self.annotations = {}
        self.signals: list[Signal] = []

    def set_text(self, text: str):
        """
        Replace the document text.

        Blocks that mutate content must use this method to ensure
        changes are explicit and centralized.
        """
        self.text = text

    def add_signal(self, name: str, value):
        """
        Emit a signal describing an observed property of the text.

        Signals are append-only and are never mutated once emitted.
        """
        self.signals.append(Signal(name, value))

        

def compute_basic_stats(text: str) -> dict:
    if not text:
        return {
            "chars": 0,
            "words": 0,
            "lines": 0,
            "paragraphs": 0
        }
    
    words = text.split()
    lines = text.split("\n")
    paragraphs = [p for p in text.split("\n\n") if p.strip()]

    return {
        "chars": len(text),
        "words": len(words),
        "lines": len(lines),
        "paragraphs": len(paragraphs)
    }

def summarize_signals(self) -> dict:
    summary = {}

    for sig in self.signals:
        key = sig.name.split(".", 1)[-1]
        summary[key] = summary.get(key, 0) + 1

    return summary 