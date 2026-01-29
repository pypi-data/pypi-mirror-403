"""
Mitmproxy addon implementing mode-aware HTTP cassette recording/replay.

Behavior by mode (RECORD_MODE env var):
- once (default): Record if no recordings exist, replay if they do
- none: Replay only, fail if no match found (use in CI)
- all: Always re-record, overwriting existing recordings

On startup → load existing HTTP cassettes from most recent file
On request → check for match, replay if found
On response → record new interaction (when recording)
On shutdown → save recordings (when recording)
"""

import json
import os
from datetime import datetime
from pathlib import Path

from mitmproxy import http
from mitmproxy.addonmanager import Loader


class RecordedInteraction:
    """Represents a recorded request-response pair."""

    def __init__(self, request_data: dict, response_data: dict):
        self.request = request_data
        self.response = response_data

    @classmethod
    def from_flow(cls, flow: http.HTTPFlow) -> "RecordedInteraction":
        """Create RecordedInteraction from mitmproxy flow."""
        if flow.response is None:
            raise ValueError("Cannot record flow without response")

        request_data = {
            "method": flow.request.method,
            "url": flow.request.pretty_url,
            "host": flow.request.host,
            "port": flow.request.port,
            "path": flow.request.path,
            "scheme": flow.request.scheme,
            "headers": dict(flow.request.headers),
            "content": (
                flow.request.content.decode("utf-8", errors="ignore")
                if flow.request.content
                else ""
            ),
        }

        response_data = {
            "status_code": flow.response.status_code,
            "reason": flow.response.reason,
            "headers": dict(flow.response.headers),
            "content": (
                flow.response.content.decode("utf-8", errors="ignore")
                if flow.response.content
                else ""
            ),
        }

        return cls(request_data, response_data)

    def matches(self, flow: http.HTTPFlow) -> bool:
        """
        Check if incoming request matches this recorded interaction.

        Matching strategy (based on Hoverfly's strongest match):
        - Method must match exactly
        - URL must match exactly
        - Host must match exactly
        - Path must match exactly
        """
        return (
            flow.request.method == self.request["method"]
            and flow.request.pretty_url == self.request["url"]
            and flow.request.host == self.request["host"]
            and flow.request.path == self.request["path"]
        )

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "request": self.request,
            "response": self.response,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "RecordedInteraction":
        """Create from dictionary (JSON deserialization)."""
        return cls(data["request"], data["response"])


class SpyModeAddon:
    """
    Mitmproxy addon with mode-aware behavior.

    Modes (RECORD_MODE):
    - once: Record if no recordings exist, replay if they do
    - none: Replay only (fail on miss)
    - all: Always re-record
    """

    def __init__(self, http_cassettes_dir: Path | None = None):
        # Check environment variable if http_cassettes_dir not provided
        if not http_cassettes_dir:
            env_path = os.environ.get("MITM_HTTP_CASSETTES_DIR")
            if env_path:
                http_cassettes_dir = Path(env_path)

        self.http_cassettes_dir = http_cassettes_dir

        # Read record mode from environment (default to "once")
        self.record_mode = os.environ.get("MITM_RECORD_MODE", "once").lower()

        # Existing HTTP cassettes (loaded from most recent file)
        self.existing_cassettes: list[RecordedInteraction] = []

        # New HTTP cassettes recorded during this session
        self.new_cassettes: list[RecordedInteraction] = []

        # Determine if we should record based on mode and existing recordings
        self._should_record = False
        self._load_most_recent()

        # Set recording flag based on mode and existing cassettes
        if self.record_mode == "all":
            # Always record, clear existing
            self._should_record = True
            self.existing_cassettes = []
        elif self.record_mode == "none":
            # Replay only
            self._should_record = False
        else:  # "once" (default)
            # Record if no existing cassettes, otherwise replay
            self._should_record = len(self.existing_cassettes) == 0

    def _find_most_recent_cassette(self) -> Path | None:
        """Find the most recent HTTP cassette file in the cassettes directory."""
        if not self.http_cassettes_dir or not self.http_cassettes_dir.exists():
            return None

        # Find all JSON files in the directory
        json_files = list(self.http_cassettes_dir.glob("*.json"))
        if not json_files:
            return None

        # Sort by modification time (most recent first)
        json_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
        return json_files[0]

    def _load_most_recent(self) -> None:
        """Load existing HTTP cassettes from the most recent file."""
        recent_file = self._find_most_recent_cassette()
        if not recent_file:
            print(
                f"[SpyMode] No existing HTTP cassettes found in "
                f"{self.http_cassettes_dir}"
            )
            return

        try:
            data = json.loads(recent_file.read_text())
            self.existing_cassettes = [
                RecordedInteraction.from_dict(item)
                for item in data.get("interactions", [])
            ]
            print(
                f"[SpyMode] Loaded {len(self.existing_cassettes)} "
                f"HTTP cassettes from {recent_file.name}"
            )
        except Exception as e:
            print(f"[SpyMode] Error loading HTTP cassettes: {e}")
            self.existing_cassettes = []

    def _save_new_cassettes(self) -> None:
        """Save new HTTP cassettes to a timestamped file."""
        if not self.new_cassettes or not self.http_cassettes_dir:
            return

        self.http_cassettes_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        output_file = self.http_cassettes_dir / f"{timestamp}.json"

        # Combine existing and new cassettes
        all_cassettes = self.existing_cassettes + self.new_cassettes

        data = {
            "version": "1.0",
            "interactions": [r.to_dict() for r in all_cassettes],
        }

        output_file.write_text(json.dumps(data, indent=2))
        print(
            f"[SpyMode] Saved {len(self.new_cassettes)} "
            f"new HTTP cassettes to {output_file.name}"
        )
        print(f"[SpyMode] Total HTTP cassettes: {len(all_cassettes)}")

    def load(self, loader: Loader) -> None:
        """Called when addon is loaded."""
        loader.add_option(
            name="spy_http_cassettes_dir",
            typespec=str,
            default="",
            help="Directory for HTTP cassettes",
        )

    def request(self, flow: http.HTTPFlow) -> None:
        """
        Intercept incoming request.

        Check if we have a cassette response for this request.
        If yes, replay it. If no, let it pass through to real API.
        """
        # Check existing cassettes first, then new ones
        all_cassettes = self.existing_cassettes + self.new_cassettes

        for cassette in all_cassettes:
            if cassette.matches(flow):
                url = flow.request.pretty_url
                print(f"[SpyMode] REPLAY: {flow.request.method} {url}")

                # Create response from cassette
                flow.response = http.Response.make(
                    status_code=cassette.response["status_code"],
                    content=cassette.response["content"].encode("utf-8"),
                    headers=cassette.response["headers"],
                )

                # Mark that this was replayed (prevent recording in response())
                flow.metadata["spy_replayed"] = True
                return

        # No match found - let request pass through to real API
        print(f"[SpyMode] FORWARD: {flow.request.method} {flow.request.pretty_url}")

    def response(self, flow: http.HTTPFlow) -> None:
        """
        Intercept response from real API.

        Only records when in recording mode (all, or once with no existing recordings).
        """
        # Skip if this was a replayed response
        if flow.metadata.get("spy_replayed"):
            return

        # Skip if no response (error occurred)
        if not flow.response:
            return

        # Only record when in recording mode
        if self._should_record:
            cassette = RecordedInteraction.from_flow(flow)
            print(f"[SpyMode] RECORD: {flow.request.method} {flow.request.pretty_url}")
            self.new_cassettes.append(cassette)

    def done(self) -> None:
        """Called when mitmproxy is shutting down."""
        if self._should_record and self.new_cassettes:
            self._save_new_cassettes()


# Entry point for mitmproxy
addons = [SpyModeAddon()]
