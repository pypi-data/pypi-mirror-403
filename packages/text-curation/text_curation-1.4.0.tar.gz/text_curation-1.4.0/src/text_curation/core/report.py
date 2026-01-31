from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List

@dataclass
class CurationReport:
    """
    Immutable summary of a single curation run.
    """

    profile_id: str
    blocks: List[str]

    input_stats: Dict[str, int]
    output_stats: Dict[str, int]

    block_stats: Dict[str, Dict[str, int]] = field(default_factory=dict)
    signals_summary: Dict[str, int] = field(default_factory=dict)

    def diff(self) -> Dict[str, int]:
        """
        Convenience elper: output minus input.
        """
        return {
            k: self.output_stats.get(k, 0) - self.input_stats.get(k, 0)
            for k in self.input_stats
        }
    
    def to_dict(self) -> dict:
        """
        JSON-serializable representation (HF-compatible)
        """
        return asdict(self)