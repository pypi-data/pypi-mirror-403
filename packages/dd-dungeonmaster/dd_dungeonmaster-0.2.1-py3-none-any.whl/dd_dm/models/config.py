"""Configuration data models."""

from dataclasses import dataclass, field


@dataclass
class ModulesConfig:
    """Enabled modules configuration."""

    enabled: list[str] = field(default_factory=list)


@dataclass
class LocalConfig:
    """Local modules configuration."""

    custom_modules: list[str] = field(default_factory=list)


@dataclass
class Config:
    """Complete dd-dm configuration."""

    modules: ModulesConfig = field(default_factory=ModulesConfig)
    local: LocalConfig = field(default_factory=LocalConfig)
