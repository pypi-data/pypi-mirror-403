from text_curation.blocks import (
    NormalizationBlock,
    CodeSafeFormattingBlock,
    ParagraphFormattingBlock,
    RedactionBlock,
    BasicStructureBlock,
    ExactParagraphDeduplicationBlock,
)
from text_curation.profiles.base import Profile
from text_curation.registry import register


# Stable, general-purpose profile for heterogeneous web-derived text.
# This profile prioritizes determinism, safety, and semantic preservation.
PROFILE = Profile(
    name="web_common",
    version="v1",
    blocks=[
        # Redact sensitive information early to avoid downstream leakage
        RedactionBlock(),

        # Normalize Unicode and remove low-level encoding artifacts
        NormalizationBlock(),

        # Maintains the code indenatation format
        CodeSafeFormattingBlock(),
        
        # Reconstruct readable paragraph and line structure
        ParagraphFormattingBlock(),

        # Emit structural signals without mutating text
        BasicStructureBlock(
            policy={
                "detect_headers": True,
                "detect_lists": True,
                "detect_all_caps": True,
                "short_line_threshold": 20,
                "list_block_threshold": 0.5,
                "min_repetition_for_boilerplate": 2,
            }
        ),

        # Conservatively drop empty or repeated short boilerplate paragraphs
        ExactParagraphDeduplicationBlock(
            policy={
        "scope": "paragraph",
        "normalize_case": True,
        "collapse_whitespace": True,
        "drop_empty": True,
    }
        ),
    ],
    guarantees = {
        # Reproducibility
        "deterministic": True,
        "order_independent": True,

        # Safety
        "secrets_redacted": True,
        "pii_removed": False,

        # Structure
        "structure_preserved": True,
        "layout_preserved": False,
        "code_safe": True,

        # Content policy
        "content_removed": True,
        "content_rewritten": False,

        # Repetition & dedup
        "deduplication": True,
        "repetition_preserved": False,

        # Semantics
        "semantic_filtering": False,
        "heuristic_scoring": True,
    },
)

# Register the profile at import time.
# This allows resolution via the global profile registry.
register(PROFILE)
