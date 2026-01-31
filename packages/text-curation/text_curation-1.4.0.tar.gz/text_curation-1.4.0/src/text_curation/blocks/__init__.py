"""
Public block API.

This module exposes all stable block implementations and defines
the canonical import surface for block composition in profiles.
"""

from .base import Block
from .normalization import NormalizationBlock
from .formatting import (CodeSafeFormattingBlock, ParagraphFormattingBlock)
from .redaction import RedactionBlock
from .structure.basic import BasicStructureBlock
from .filtering.signal_based import SignalBasedBoilerplateFilteringBlock
from .deduplication import ExactParagraphDeduplicationBlock

# Explicit export list to keep the public API stable
__all__ = [
    "Block",
    "NormalizationBlock",
    "CodeSafeFormattingBlock", "ParagraphFormattingBlock",
    "RedactionBlock",
    "BasicStructureBlock",
    "SignalBasedBoilerplateFilteringBlock",
    "ExactParagraphDeduplicationBlock",
]