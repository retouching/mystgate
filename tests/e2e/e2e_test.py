from collections.abc import Iterator

import pytest

from tests.constants import ROOT
from tests.stacks import DockerStack


@pytest.mark.e2e
class E2ETest:
    stack: DockerStack

    @pytest.fixture(scope="class")
    @classmethod
    def running_stack(cls) -> Iterator[DockerStack]:
        """Start and tear down the throwaway mystgate Docker Compose stack."""
        with DockerStack(ROOT / "docker" / "compose.test.yaml") as running:
            yield running

    @pytest.fixture(autouse=True)
    def attach_stack(self, running_stack: DockerStack) -> None:
        """Bind the class-scoped DockerStack onto the test instance."""
        self.stack = running_stack
