"""Software-only channel and impairment models."""

from .awgn_channel import AWGNChannel
from .fading_channel import FadingChannel

__all__ = ["AWGNChannel", "FadingChannel"]
