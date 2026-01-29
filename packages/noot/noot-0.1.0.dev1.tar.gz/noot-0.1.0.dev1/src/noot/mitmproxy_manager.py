"""Mitmproxy process management for spy mode recording/replay."""

import os
import shutil
import signal
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

from noot.cache import CassettePathError, RecordMode
from noot.project import ProjectRootNotFoundError, find_project_root


def get_mitmproxy_ca_cert_path() -> Path:
    """Get the path to mitmproxy's CA certificate."""
    return Path.home() / ".mitmproxy" / "mitmproxy-ca-cert.pem"


def get_http_cassettes_dir() -> Path:
    """
    Get the default HTTP cassettes directory.

    Resolution order:
        1. NOOT_HTTP_CASSETTE_DIR environment variable
        2. <project_root>/.cassettes/http/ (based on .git location)

    Raises:
        CassettePathError: If no .git directory is found and
            NOOT_HTTP_CASSETTE_DIR is not set.
    """
    # Check for explicit env var first
    env_dir = os.environ.get("NOOT_HTTP_CASSETTE_DIR")
    if env_dir:
        return Path(env_dir)

    try:
        root = find_project_root()
    except ProjectRootNotFoundError as e:
        raise CassettePathError(
            "Cannot determine HTTP cassette directory: "
            f"no .git found starting from {e.start_dir}.\n"
            "Either:\n"
            "  1. Run from within a git repository, or\n"
            "  2. Set NOOT_HTTP_CASSETTE_DIR environment variable, or\n"
            "  3. Pass an explicit http_cassettes path: "
            "Flow.spawn(..., http_cassettes='path/to/dir')"
        ) from e
    return root / ".cassettes" / "http"


@dataclass
class MitmproxyConfig:
    """Mitmproxy configuration."""

    listen_port: int = 8080
    http_cassettes_dir: Path | None = None
    addon_path: Path | None = None
    command: str | None = None  # Kept for potential future use
    record_mode: RecordMode = RecordMode.ONCE  # Controls spy mode behavior

    def __post_init__(self):
        # Use default HTTP cassettes directory if not specified
        if self.http_cassettes_dir is None:
            try:
                self.http_cassettes_dir = get_http_cassettes_dir()
            except CassettePathError:
                # Cannot determine default directory - leave as None
                # Caller should check and skip mitmproxy if not needed
                pass


class MitmproxyManager:
    """Manages mitmproxy process lifecycle with spy mode addon."""

    def __init__(self, config: MitmproxyConfig):
        self._config = config
        self._process: subprocess.Popen | None = None
        self._started = False

        # Default addon path
        if not self._config.addon_path:
            addon_file = Path(__file__).parent / "addons" / "spy_mode.py"
            self._config.addon_path = addon_file

    def start(self) -> None:
        """Start mitmproxy with spy mode addon."""
        if self._started:
            raise RuntimeError("Mitmproxy already started")

        # Set HTTP cassettes directory via environment variable
        env = os.environ.copy()
        if self._config.http_cassettes_dir:
            env["MITM_HTTP_CASSETTES_DIR"] = str(self._config.http_cassettes_dir)

        # Pass record mode to addon
        env["MITM_RECORD_MODE"] = self._config.record_mode.value

        # Find mitmdump binary
        mitmdump_path = shutil.which("mitmdump")
        if not mitmdump_path:
            raise RuntimeError(
                "mitmdump not found in PATH. Install with: pip install mitmproxy"
            )

        cmd = [
            mitmdump_path,
            "--listen-port",
            str(self._config.listen_port),
            "--ssl-insecure",  # Don't verify upstream HTTPS certs
            "-s",
            str(self._config.addon_path),
        ]

        # Start mitmproxy
        print(f"[MitmproxyManager] Starting: {' '.join(cmd)}")
        self._process = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            env=env,
        )

        # Wait for mitmproxy to be ready
        self._wait_for_ready()

        # Double-check it's still alive after wait
        if self._process.poll() is not None:
            raise RuntimeError(
                "Mitmproxy process died after startup. "
                "Check that mitmdump is installed and the port is available."
            )

        print(
            f"[MitmproxyManager] Mitmproxy started successfully "
            f"on port {self._config.listen_port}"
        )
        self._started = True

    def stop(self) -> None:
        """Stop mitmproxy process."""
        if not self._started or not self._process:
            return

        # Send SIGTERM to allow graceful shutdown (calls addon.done())
        self._process.send_signal(signal.SIGTERM)

        try:
            self._process.wait(timeout=5.0)
        except subprocess.TimeoutExpired:
            self._process.kill()

        self._started = False

    def _wait_for_ready(self, timeout: float = 5.0) -> None:
        """
        Wait for mitmproxy to be ready.

        Uses a simple time-based approach since mitmproxy starts quickly
        and port-based checks have issues with IPv6/IPv4 resolution.
        """
        print(f"[MitmproxyManager] Waiting {timeout}s for mitmproxy to start...")
        start = time.time()

        # Check periodically if process died
        while time.time() - start < timeout:
            if self._process and self._process.poll() is not None:
                raise RuntimeError(
                    "Mitmproxy process died during startup. "
                    "Check that mitmdump is installed and the port is available."
                )
            time.sleep(0.2)

        print(f"[MitmproxyManager] Wait complete ({time.time() - start:.1f}s)")

        # Final check that process is still alive
        if self._process and self._process.poll() is not None:
            raise RuntimeError(
                "Mitmproxy process died during startup. "
                "Check that mitmdump is installed and the port is available."
            )

    def get_proxy_url(self) -> str:
        """Get proxy URL for configuring applications."""
        # Use 127.0.0.1 instead of localhost to avoid resolution issues on some systems
        return f"http://127.0.0.1:{self._config.listen_port}"

    def get_ca_cert_path(self) -> Path:
        """Get the path to mitmproxy's CA certificate."""
        return get_mitmproxy_ca_cert_path()

    def get_env_vars(self, base_url_var: str | None = None) -> dict[str, str]:
        """
        Get environment variables for redirecting API calls through proxy.

        Args:
            base_url_var: Name of env var that the CLI app uses for API base URL
                         (e.g., "API_BASE_URL", "ANTHROPIC_BASE_URL", etc.)

        Returns:
            Dictionary of environment variables to set
        """
        proxy_url = self.get_proxy_url()
        ca_cert_path = self.get_ca_cert_path()

        env_vars = {
            # Generic proxy vars (for apps that respect HTTP_PROXY)
            "HTTP_PROXY": proxy_url,
            "HTTPS_PROXY": proxy_url,
            "http_proxy": proxy_url,
            "https_proxy": proxy_url,
            # CA certificate for SSL verification through the proxy
            "SSL_CERT_FILE": str(ca_cert_path),
            "REQUESTS_CA_BUNDLE": str(ca_cert_path),
            # Custom var for apps that want to explicitly use the mitmproxy CA
            "MITMPROXY_CA_CERT": str(ca_cert_path),
        }

        # Add custom base URL var if specified
        if base_url_var:
            env_vars[base_url_var] = proxy_url

        return env_vars
