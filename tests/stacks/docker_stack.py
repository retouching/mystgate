import os
import secrets
import signal
import subprocess
from pathlib import Path
from types import FrameType, TracebackType

from tests.constants import ROOT


class DockerStack:
    def __init__(self, compose_file: Path, *, prefix: str = "mystgate-e2e") -> None:
        """Configure a throwaway Docker Compose stack with strict cleanup."""
        self.compose_file = compose_file
        self.project = f"{prefix}-{secrets.token_hex(4)}"
        self.env = dict(os.environ)
        self.docker_config = self.env.get("DOCKER_CONFIG") or str(Path.home() / ".docker")
        self.env["DOCKER_CONFIG"] = self.docker_config
        self.started = False

    def compose(self, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
        """Run a docker compose command scoped to this stack project."""
        return subprocess.run(
            ["docker", "compose", "-f", str(self.compose_file), "-p", self.project, *args],
            cwd=ROOT,
            env=self.env,
            text=True,
            capture_output=True,
            check=check,
        )

    def handle_signal(self, signum: int, frame: FrameType | None) -> None:
        """Tear down the stack cleanly when receiving termination signals."""
        del frame
        self.down()
        raise SystemExit(128 + signum)

    def up(self) -> None:
        """Build and start the throwaway Docker Compose stack."""
        signal.signal(signal.SIGTERM, self.handle_signal)
        signal.signal(signal.SIGHUP, self.handle_signal)
        self.compose("up", "-d", "--build")
        self.started = True

    def exec_cli(self, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
        """Execute a mystgate CLI command inside the running container."""
        return self.compose("exec", "-T", "mystgate", "mystgate", *args, check=check)

    def exec_raw(self, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
        """Execute an arbitrary command inside the running container."""
        return self.compose("exec", "-T", "mystgate", *args, check=check)

    def assert_no_leftovers(self) -> None:
        """Verify no containers, networks, or volumes remain for this stack project."""
        label = f"com.docker.compose.project={self.project}"
        for kind in ("ps -a", "network ls", "volume ls"):
            result = subprocess.run(
                ["docker", *kind.split(), "--filter", f"label={label}", "-q"],
                env=self.env,
                text=True,
                capture_output=True,
                check=True,
            )
            assert not result.stdout.strip(), f"leftover Docker {kind}: {result.stdout.strip()}"

    def down(self) -> None:
        """Stop and remove all containers, volumes, and locally built images."""
        if not self.started:
            return
        self.started = False
        self.compose("down", "--volumes", "--rmi", "local", check=False)
        self.assert_no_leftovers()

    def __enter__(self) -> DockerStack:
        """Start the stack when entering a context manager."""
        self.up()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Tear down the stack when leaving a context manager."""
        del exc_type, exc_val, exc_tb
        self.down()
