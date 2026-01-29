"""noot - Library for testing interactive CLIs with LLM-driven steps."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from noot.cache import CacheMissError, RecordMode
    from noot.flow import Flow
    from noot.step import StepResult

__all__ = ["Flow", "StepResult", "RecordMode", "CacheMissError"]


def __getattr__(name: str):
    """Lazy import to avoid requiring anthropic at import time."""
    if name == "Flow":
        from noot.flow import Flow

        return Flow
    if name == "StepResult":
        from noot.step import StepResult

        return StepResult
    if name == "RecordMode":
        from noot.cache import RecordMode

        return RecordMode
    if name == "CacheMissError":
        from noot.cache import CacheMissError

        return CacheMissError
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
