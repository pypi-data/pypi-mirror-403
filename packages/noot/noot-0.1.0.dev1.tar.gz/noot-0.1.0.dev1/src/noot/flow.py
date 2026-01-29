"""Flow context manager for interactive CLI testing."""

from __future__ import annotations

from pathlib import Path

from noot.assertions import execute_assertion
from noot.cache import Cache
from noot.llm import LLM
from noot.mitmproxy_manager import MitmproxyConfig, MitmproxyManager
from noot.step import StepResult, execute_step
from noot.terminal import Terminal


class Flow:
    """
    Context manager for testing interactive CLI flows.

    Usage:
        with Flow.spawn("spx init") as f:
            f.step("Enter 'sample_project'")
            f.step("Select API Key auth option")
            f.step("Enter 'sample_key'")

        assert Path("project.spx.toml").exists()
    """

    def __init__(
        self,
        command: str | None = None,
        model: str = "claude-sonnet-4-20250514",
        pane_width: int = 120,
        pane_height: int = 40,
        stability_timeout: float = 5.0,
        cassette: str | Path | None = None,
        http_cassettes: str | Path | None = None,
        mitmproxy_port: int = 8080,
    ):
        """
        Initialize a Flow.

        Args:
            command: Initial command to run (e.g., "spx init")
            model: Anthropic model to use for step interpretation
            pane_width: Terminal width
            pane_height: Terminal height
            stability_timeout: Default timeout for waiting for terminal stability
            cassette: Path to cassette file for caching LLM responses.
                      Behavior controlled by RECORD_MODE env var (once/none/all).
            http_cassettes: Directory for HTTP cassettes (mitmproxy).
                           Defaults to <project_root>/.cassettes/http/
            mitmproxy_port: Port for mitmproxy to listen on (default 8080)
        """
        self._command = command
        self._terminal = Terminal(pane_width=pane_width, pane_height=pane_height)
        cassette_path = Path(cassette) if cassette else None
        self._cache = Cache.from_env(cassette_path)
        self._llm = LLM(model=model, cache=self._cache)
        self._stability_timeout = stability_timeout
        self._steps: list[StepResult] = []

        # Mitmproxy integration for API recording/replay
        http_cassettes_dir = Path(http_cassettes) if http_cassettes else None
        config = MitmproxyConfig(
            listen_port=mitmproxy_port,
            http_cassettes_dir=http_cassettes_dir,
            record_mode=self._cache.mode,
        )
        # Only create mitmproxy manager if http_cassettes_dir was determined
        if config.http_cassettes_dir:
            self._mitmproxy: MitmproxyManager | None = MitmproxyManager(config)
        else:
            self._mitmproxy = None

    @classmethod
    def spawn(
        cls,
        command: str,
        model: str = "claude-sonnet-4-20250514",
        pane_width: int = 120,
        pane_height: int = 40,
        stability_timeout: float = 5.0,
        cassette: str | Path | None = None,
        http_cassettes: str | Path | None = None,
        mitmproxy_port: int = 8080,
    ) -> Flow:
        """
        Create a Flow that spawns a command.

        Args:
            command: Command to run (e.g., "spx init")
            model: Anthropic model for step interpretation
            pane_width: Terminal width
            pane_height: Terminal height
            stability_timeout: Default timeout for stability
            cassette: Path to cassette file for caching LLM responses.
                      Behavior controlled by RECORD_MODE env var (once/none/all).
            http_cassettes: Directory for HTTP cassettes (mitmproxy).
                           Defaults to <project_root>/.cassettes/http/
            mitmproxy_port: Port for mitmproxy to listen on (default 8080)

        Returns:
            Flow instance (use as context manager)
        """
        return cls(
            command=command,
            model=model,
            pane_width=pane_width,
            pane_height=pane_height,
            stability_timeout=stability_timeout,
            cassette=cassette,
            http_cassettes=http_cassettes,
            mitmproxy_port=mitmproxy_port,
        )

    def __enter__(self) -> Flow:
        """Start mitmproxy (if enabled), then start terminal."""
        if self._mitmproxy:
            self._mitmproxy.start()
            env_vars = self._mitmproxy.get_env_vars()
        else:
            env_vars = None

        self._terminal.start(command=self._command, env_vars=env_vars)
        # Wait for initial command to stabilize
        self._terminal.wait_for_stability(timeout_sec=self._stability_timeout)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Clean up terminal and mitmproxy."""
        self._terminal.stop()
        if self._mitmproxy:
            self._mitmproxy.stop()

    def expect(self, expected_state: str) -> None:
        """
        PyTest compatible assertion for screen content.

        Uses LLM to generate assertion code (during recording) or executes
        cached assertion code (during replay) to verify screen content.

        Raises AssertionError if the screen content does not match the expected state.
        """
        __tracebackhide__ = True

        screen = self.screen()
        assertion_code = ""
        error_msg = "Assertion code generation failed"

        try:
            assertion_code = self._llm.generate_assertion(
                screen=screen, expected_state=expected_state
            )
            passed, error_msg = execute_assertion(
                assertion_code, screen, expected_state
            )
        except Exception as exc:
            passed = False
            error_msg = f"Assertion generation/execution failed: {exc}"

        if passed:
            return

        recent_steps = self._steps[-3:]
        step_lines = []
        if recent_steps:
            base_index = len(self._steps) - len(recent_steps) + 1
            step_lines = [
                f"{base_index + idx}) {step.instruction}"
                for idx, step in enumerate(recent_steps)
            ]

        message_lines = [
            "Flow.expect failed",
            f"Expected: {expected_state}",
            f"Reason: {error_msg}",
        ]
        if assertion_code:
            message_lines.append("Assertion code:")
            message_lines.extend(f"  {line}" for line in assertion_code.split("\n"))
        if step_lines:
            message_lines.append("Recent steps:")
            message_lines.extend(f"  {line}" for line in step_lines)
        message_lines.append("Screen:")
        message_lines.append(screen)
        raise AssertionError("\n".join(message_lines))

    def step(self, instruction: str, timeout: float | None = None) -> StepResult:
        """
        Execute a single step in the flow.

        Args:
            instruction: Natural language instruction
                e.g., "Enter 'sample_project'"
                e.g., "Select the API Key option"
                e.g., "Press enter to confirm"
            timeout: Override stability timeout for this step

        Returns:
            StepResult with execution details
        """
        result = execute_step(
            terminal=self._terminal,
            instruction=instruction,
            llm=self._llm,
            stability_timeout=timeout or self._stability_timeout,
        )
        self._steps.append(result)
        return result

    def screen(self) -> str:
        """Get current terminal screen."""
        return self._terminal.capture()

    @property
    def steps(self) -> list[StepResult]:
        """Get all executed steps."""
        return self._steps.copy()
