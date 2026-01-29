"""Custom exceptions for dd-dm."""


class DDDMError(Exception):
    """Base exception for dd-dm errors."""

    pass


class NotInitializedError(DDDMError):
    """Raised when dd-dm is not initialized in the current directory."""

    def __init__(self, path: str | None = None) -> None:
        msg = "dd-dm is not initialized"
        if path:
            msg = f"dd-dm is not initialized in {path}"
        msg += ". Run 'dd-dm init' first."
        super().__init__(msg)


class AlreadyInitializedError(DDDMError):
    """Raised when dd-dm is already initialized."""

    def __init__(self, path: str | None = None) -> None:
        msg = "dd-dm is already initialized"
        if path:
            msg = f"dd-dm is already initialized in {path}"
        super().__init__(msg)


class GitError(DDDMError):
    """Raised when a git operation fails."""

    pass


class ConfigError(DDDMError):
    """Raised when there's a configuration error."""

    pass


class ModuleNotFoundDDDMError(DDDMError):
    """Raised when a requested module is not found."""

    def __init__(self, module_name: str) -> None:
        super().__init__(f"Module '{module_name}' not found")
        self.module_name = module_name


class ModuleAlreadyExistsError(DDDMError):
    """Raised when trying to add a module that already exists."""

    def __init__(self, module_name: str) -> None:
        super().__init__(
            f"Module '{module_name}' is already enabled. "
            "Use --force to override or run 'dd-dm delete' first."
        )
        self.module_name = module_name


class DirtyWorkingDirectoryError(DDDMError):
    """Raised when the working directory has uncommitted changes."""

    def __init__(self) -> None:
        super().__init__(
            "Working directory has uncommitted changes. "
            "Please commit or stash them before proceeding."
        )
