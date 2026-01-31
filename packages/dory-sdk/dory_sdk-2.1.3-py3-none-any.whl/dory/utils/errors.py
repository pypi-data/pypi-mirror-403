"""
Dory SDK Exception Classes.

All SDK-specific exceptions inherit from DoryError for easy catching.
"""


class DoryError(Exception):
    """Base exception for all Dory SDK errors."""

    def __init__(self, message: str, cause: Exception | None = None):
        super().__init__(message)
        self.message = message
        self.cause = cause

    def __str__(self) -> str:
        if self.cause:
            return f"{self.message}: {self.cause}"
        return self.message


class DoryStartupError(DoryError):
    """Raised when processor startup fails."""
    pass


class DoryShutdownError(DoryError):
    """Raised when processor shutdown fails or times out."""
    pass


class DoryStateError(DoryError):
    """Raised when state operations fail (snapshot, restore, validation)."""
    pass


class DoryConfigError(DoryError):
    """Raised when configuration is invalid or missing."""
    pass


class DoryK8sError(DoryError):
    """Raised when Kubernetes API operations fail."""
    pass


class DoryHealthError(DoryError):
    """Raised when health check operations fail."""
    pass


class DoryTimeoutError(DoryError):
    """Raised when an operation times out."""
    pass


class DoryValidationError(DoryError):
    """Raised when validation fails (state schema, config, etc.)."""
    pass
