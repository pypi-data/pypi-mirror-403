"""Simplified tmux-based terminal session for local execution."""

import shlex
import subprocess
import time
import uuid


class Terminal:
    """Sync terminal session using tmux for local execution."""

    def __init__(
        self,
        pane_width: int = 120,
        pane_height: int = 40,
    ):
        self._session_name = f"noot-{uuid.uuid4().hex[:8]}"
        self._pane_width = pane_width
        self._pane_height = pane_height
        self._started = False

    def start(
        self, command: str | None = None, env_vars: dict[str, str] | None = None
    ) -> None:
        """Start tmux session, optionally running an initial command.

        Args:
            command: Initial command to run in the session
            env_vars: Environment variables to set in the session
        """
        if self._started:
            raise RuntimeError("Terminal already started")

        # Create tmux session
        start_cmd = (
            f"tmux new-session "
            f"-x {self._pane_width} -y {self._pane_height} "
            f"-d -s {self._session_name}"
        )
        result = subprocess.run(start_cmd, shell=True, capture_output=True)
        if result.returncode != 0:
            raise RuntimeError(f"Failed to start tmux: {result.stderr.decode()}")

        self._started = True

        # Set environment variables if provided
        if env_vars:
            for key, value in env_vars.items():
                # Export environment variables in the tmux session
                self.send_keys(f"export {key}={value}\n", wait_sec=0.1)

        # Run initial command if provided
        if command:
            self.send_keys(f"{command}\n", wait_sec=0.5)

    def stop(self) -> None:
        """Kill the tmux session."""
        if not self._started:
            return

        subprocess.run(
            f"tmux kill-session -t {self._session_name}",
            shell=True,
            capture_output=True,
        )
        self._started = False

    def send_keys(self, keys: str, wait_sec: float = 0.1) -> None:
        """Send keystrokes to the terminal."""
        if not self._started:
            raise RuntimeError("Terminal not started")

        # Split keys into individual parts for tmux send-keys
        # Handle special sequences like \n -> Enter
        escaped_keys = shlex.quote(keys)
        cmd = f"tmux send-keys -t {self._session_name} -l {escaped_keys}"
        subprocess.run(cmd, shell=True, capture_output=True)

        if wait_sec > 0:
            time.sleep(wait_sec)

    def send_special(self, key: str, wait_sec: float = 0.1) -> None:
        """Send special keys (Enter, C-c, Up, Down, etc.)."""
        if not self._started:
            raise RuntimeError("Terminal not started")

        cmd = f"tmux send-keys -t {self._session_name} {key}"
        subprocess.run(cmd, shell=True, capture_output=True)

        if wait_sec > 0:
            time.sleep(wait_sec)

    def capture(self) -> str:
        """Capture current terminal screen."""
        if not self._started:
            raise RuntimeError("Terminal not started")

        result = subprocess.run(
            f"tmux capture-pane -t {self._session_name} -p",
            shell=True,
            capture_output=True,
        )
        return result.stdout.decode()

    def is_alive(self) -> bool:
        """Check if tmux session is still running."""
        result = subprocess.run(
            f"tmux has-session -t {self._session_name}",
            shell=True,
            capture_output=True,
        )
        return result.returncode == 0

    def wait_for_stability(
        self, timeout_sec: float = 5.0, poll_interval: float = 0.2
    ) -> str:
        """Wait until terminal output stabilizes (no changes for poll_interval)."""
        start_time = time.time()
        last_screen = self.capture()

        while time.time() - start_time < timeout_sec:
            time.sleep(poll_interval)
            current_screen = self.capture()

            if current_screen == last_screen:
                return current_screen

            last_screen = current_screen

        return last_screen
