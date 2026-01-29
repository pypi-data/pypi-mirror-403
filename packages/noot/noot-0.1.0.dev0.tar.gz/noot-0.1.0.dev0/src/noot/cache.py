"""CLI cassette caching for deterministic test replay."""

import json
import os
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from noot.project import ProjectRootNotFoundError, find_project_root


class CassettePathError(Exception):
    """Raised when cassette path cannot be determined."""

    def __init__(self, message: str):
        super().__init__(message)


def get_cli_cassettes_dir() -> Path:
    """
    Get the default CLI cassettes directory.

    Resolution order:
        1. NOOT_CASSETTE_DIR environment variable
        2. <project_root>/.cassettes/cli/ (based on .git location)

    Raises:
        CassettePathError: If no .git directory is found and
            NOOT_CASSETTE_DIR is not set.
    """
    # Check for explicit env var first
    env_dir = os.environ.get("NOOT_CASSETTE_DIR")
    if env_dir:
        return Path(env_dir)

    try:
        root = find_project_root()
    except ProjectRootNotFoundError as e:
        raise CassettePathError(
            "Cannot determine cassette directory: "
            f"no .git found starting from {e.start_dir}.\n"
            "Either:\n"
            "  1. Run from within a git repository, or\n"
            "  2. Set NOOT_CASSETTE_DIR environment variable, or\n"
            "  3. Pass an explicit cassette path: "
            "Flow.spawn(..., cassette='path/to/cassette.json')"
        ) from e
    return root / ".cassettes" / "cli"


class RecordMode(Enum):
    """Recording mode for cassettes."""

    ONCE = "once"  # Record if cassette missing, replay if exists (default)
    NONE = "none"  # Replay only, fail if request not found (use in CI)
    ALL = "all"  # Always re-record, overwriting existing cassette


@dataclass
class CacheEntry:
    """A single cached LLM response in a CLI cassette."""

    instruction: str
    screen: str
    response: str
    method: str  # "complete" or "expect"
    assertion_code: str | None = None  # For method="expect"


@dataclass
class Cache:
    """
    CLI cassette cache for deterministic replay.

    CLI cassettes are keyed by instruction only. For expect() calls, assertion code
    is stored and replayed deterministically without screen comparison.
    """

    mode: RecordMode
    path: Path | None = None
    _entries: list[CacheEntry] = field(default_factory=list)
    _should_record: bool = field(default=False, init=False)

    @classmethod
    def from_env(cls, cassette_path: Path | None = None) -> "Cache":
        """
        Create cache based on RECORD_MODE environment variable.

        Args:
            cassette_path: Path to CLI cassette file. If not specified and
                mode is record/replay, uses default directory based on
                .git location.

        Values:
            - "once" (default): Record if cassette missing, replay if exists
            - "none": Replay only, fail if request not found (use in CI)
            - "all": Always re-record, overwriting existing cassette
        """
        env_mode = os.environ.get("RECORD_MODE", "once").lower()
        if env_mode == "none":
            mode = RecordMode.NONE
        elif env_mode == "all":
            mode = RecordMode.ALL
        else:
            mode = RecordMode.ONCE

        # Determine cassette path - always set a default path
        if cassette_path is None:
            cassette_path = get_cli_cassettes_dir() / "default.json"

        cache = cls(mode=mode, path=cassette_path)

        # Determine behavior based on mode and cassette existence
        cassette_exists = cassette_path and cassette_path.exists()

        if mode == RecordMode.ALL:
            # Always record, clear any existing entries
            cache._should_record = True
            cache._entries = []
        elif mode == RecordMode.NONE:
            # Replay only
            cache._should_record = False
            if cassette_exists:
                cache._load()
        else:  # ONCE (default)
            if cassette_exists:
                # Cassette exists: replay mode
                cache._should_record = False
                cache._load()
            else:
                # Cassette missing: record mode
                cache._should_record = True

        return cache

    def _load(self) -> None:
        """Load CLI cassette entries from file."""
        if not self.path or not self.path.exists():
            return
        data = json.loads(self.path.read_text())
        self._entries = [
            CacheEntry(
                instruction=e["instruction"],
                screen=e["screen"],
                response=e["response"],
                method=e["method"],
                assertion_code=e.get("assertion_code"),
            )
            for e in data.get("entries", [])
        ]

    def save(self) -> None:
        """Save CLI cassette entries to file."""
        if not self.path:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        entries = []
        for e in self._entries:
            entry_data = {
                "instruction": e.instruction,
                "screen": e.screen,
                "response": e.response,
                "method": e.method,
            }
            if e.assertion_code is not None:
                entry_data["assertion_code"] = e.assertion_code
            entries.append(entry_data)
        data = {"entries": entries}
        self.path.write_text(json.dumps(data, indent=2))

    def get(self, instruction: str, screen: str, method: str) -> str | None:
        """
        Look up a cached response.

        Args:
            instruction: The instruction sent to the LLM
            screen: The current screen content
            method: The LLM method ("complete" or "expect")

        Returns:
            For "complete": Cached response if instruction matches.
            For "expect": Cached assertion_code if instruction matches.
            Returns None if not found.
        """
        for entry in self._entries:
            if entry.instruction != instruction or entry.method != method:
                continue
            # Both "complete" and "expect" match on instruction only
            if method == "expect":
                return entry.assertion_code
            return entry.response
        return None

    def put(
        self,
        instruction: str,
        screen: str,
        response: str,
        method: str,
        assertion_code: str | None = None,
    ) -> None:
        """
        Store a response in the cache.

        Args:
            instruction: The instruction sent to the LLM
            screen: The screen content at time of request
            response: The LLM response
            method: The LLM method ("complete" or "expect")
            assertion_code: For method="expect", the generated assertion code
        """
        if not self._should_record:
            return

        self._entries.append(
            CacheEntry(
                instruction=instruction,
                screen=screen,
                response=response,
                method=method,
                assertion_code=assertion_code,
            )
        )
        self.save()

    @property
    def fail_on_miss(self) -> bool:
        """Return True if cache miss should raise an error."""
        # In NONE mode, always fail on miss
        # In ONCE mode with existing cassette, fail on miss (replay mode)
        return not self._should_record and self.mode != RecordMode.ALL


class CacheMissError(Exception):
    """Raised when replay mode encounters a cache miss."""

    def __init__(self, instruction: str, method: str):
        self.instruction = instruction
        self.method = method
        super().__init__(
            f"Cache miss in replay mode: {method}() with instruction: {instruction!r}"
        )
