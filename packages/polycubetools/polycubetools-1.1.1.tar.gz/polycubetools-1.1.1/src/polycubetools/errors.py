from __future__ import annotations

__all__ = (
    "InvalidVolumeException",
    "PolycubeException",
)


class PolycubeException(Exception):
    """Base exception for all errors raised by this library."""

    pass


class InvalidVolumeException(PolycubeException):
    """Exception raised when failing to compute a volume."""

    pass
