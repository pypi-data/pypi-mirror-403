class Pipeline:
    """
    Executes an ordered sequence of blocks over input text.

    The pipeline is deterministic: blocks are applied in order
    and operate on a shared Document instance.
    """

    def __init__(self, blocks):
        """
        Create a pipeline from an ordered list of blocks.

        Args:
            blocks: Iterable of Block instances
        """
        self.blocks = blocks

    def run(self, text: str) -> str:
        """
        Run the pipeline on input text and return the final output.

        This method is a thin orchestration layer and intentionally
        hides Document internals from callers.
        """
        document = self.run_document(text)
        return document.text
    
    def run_document(self, text: str, *, collect_report: bool = False, profile_id: str | None = None):
        """
        Run the pipeline and return the Document.

        Optionally collects a CurationReport.
        """

        from .document import Document, compute_basic_stats
        from .report import CurationReport

        document = Document(text)

        input_stats = compute_basic_stats(document.text) if collect_report else None
        block_stats = {} if collect_report else None

        for block in self.blocks:
            if collect_report and hasattr(block, "reset_stats"):
                block.reset_stats()

            block.apply(document)

            if collect_report and hasattr(block, "get_stats"):
                stats = block.get_stats()

                if stats:
                    block_stats[block.__class__.__name__] = stats

        if not collect_report:
            return document
        
        output_stats = compute_basic_stats(document.text)

        report = CurationReport(
            profile_id=profile_id or "<unknown>",
            blocks=[b.__class__.__name__ for b in self.blocks],
            input_stats=input_stats,
            output_stats=output_stats,
            block_stats=block_stats or {},
            signals_summary=document.summarize_signals() if hasattr(document, "summarize_signals") else {},
            )
        
        return document, report