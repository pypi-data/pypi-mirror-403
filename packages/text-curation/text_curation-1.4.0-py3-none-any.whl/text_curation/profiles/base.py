class Profile:
    """
    Immutable description of a text curation profile.

    A Profile defines:
    - a stable name and version
    - an ordered list of configured Blocks
    - declarative guarantees about behavior

    Profiles are treated as behavioral contracts.
    Once released, their semantics must not change.
    """

    def __init__(
        self,
        name: str,
        version: str,
        blocks: list,
        guarantees: dict | None = None,
    ):
        """
        Create a new profile definition.

        Args:
            name: Logical profile name (e.g. "web_common")
            version: Explicit profile version (e.g. "v1")
            blocks: Ordered list of configured Block instances
            guarantees: Declarative, user-facing behavior guarantees
        """
        self.name = name
        self.version = version
        self.blocks = blocks
        self.guarantees = guarantees or {}

    @property
    def id(self) -> str:
        """
        Canonical profile identifier.

        Combines name and version to ensure reproducibility
        (e.g. "web_common_v1").
        """
        return f"{self.name}_{self.version}"

    def __repr__(self) -> str:
        """
        Developer-friendly representation for debugging and logs.
        """
        return f"<Profile {self.id}>"