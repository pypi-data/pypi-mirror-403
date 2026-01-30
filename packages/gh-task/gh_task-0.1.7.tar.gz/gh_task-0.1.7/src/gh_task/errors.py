class GhTaskError(Exception):
    """Base error for gh-task."""


class ConfigError(GhTaskError):
    """Invalid configuration or missing inputs."""


class ApiError(GhTaskError):
    """GitHub API error."""

    def __init__(self, status_code, payload):
        self.status_code = status_code
        self.payload = payload
        super().__init__(f"GitHub API error {status_code}: {payload}")


class NotFoundError(GhTaskError):
    """Requested entity not found."""


class OwnershipError(GhTaskError):
    """Raised when an operation requires ownership but the caller does not own it."""


class TakeError(GhTaskError):
    """Raised when a take operation fails."""


class MoveError(GhTaskError):
    """Raised when a move operation fails."""


class ReleaseError(GhTaskError):
    """Raised when a release operation fails."""


class CreateError(GhTaskError):
    """Raised when a create operation fails."""
