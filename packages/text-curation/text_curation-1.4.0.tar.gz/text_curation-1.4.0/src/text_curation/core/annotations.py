class Region:
    """
    Represents a span or region of text with associated metadata.

    Regions are intended to support future annotation and span-based
    processing (e.g. highlights, detected entities, or structural spans).
    They are purely descriptive and do not mutate document text.
    """

    def __init__(self, kind: str, start: str, end: str, data=None):
        """
        Create a new annotated region.

        Args:
            kind: Logical category of the region (e.g. "entity", "header")
            start: Start character offset (inclusive)
            end: End character offset (exclusive)
            data: Optional structured metadata associated with the region
        """
        self.kind = kind
        self.start = start
        self.end = end
        self.data = data or {}