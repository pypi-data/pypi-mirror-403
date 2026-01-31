class Signal:
    """
    Represents an inspectable observation emitted during text processing.

    Signals capture structural or statistical properties of text
    without directly modifying content. They are consumed explicitly
    by downstream blocks.
    """

    def __init__(self, name: str, value):
        """
        Create a new signal.

        Args:
            name: Fully-qualified signal name (e.g. "paragraph[3].is_header")
            value: Observed value associated with the signal
        """
        self.name = name
        self.value = value