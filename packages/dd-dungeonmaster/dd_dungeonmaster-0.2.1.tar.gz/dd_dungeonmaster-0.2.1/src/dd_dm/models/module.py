"""Module data models."""

from dataclasses import dataclass, field
from enum import Enum


class ModuleSource(Enum):
    """Source of a module."""

    REMOTE = "remote"
    LOCAL = "local"


@dataclass
class Module:
    """A constitution module."""

    name: str
    content: str
    source: ModuleSource
    version: str = "1.0.0"
    description: str = ""
    tags: list[str] = field(default_factory=list)
    requires: list[str] = field(default_factory=list)
    conflicts: list[str] = field(default_factory=list)

    @property
    def display_name(self) -> str:
        """Return human-readable name for display."""
        return self.name.replace("_", " ").title()


@dataclass
class ModuleDiff:
    """Difference between two versions of a module."""

    module_name: str
    old_content: str | None
    new_content: str | None

    @property
    def is_addition(self) -> bool:
        """Check if this is a new module addition."""
        return self.old_content is None and self.new_content is not None

    @property
    def is_removal(self) -> bool:
        """Check if this is a module removal."""
        return self.old_content is not None and self.new_content is None

    @property
    def is_modification(self) -> bool:
        """Check if this is a module modification."""
        return (
            self.old_content is not None
            and self.new_content is not None
            and self.old_content != self.new_content
        )

    @property
    def has_changes(self) -> bool:
        """Check if there are any changes."""
        return self.is_addition or self.is_removal or self.is_modification
