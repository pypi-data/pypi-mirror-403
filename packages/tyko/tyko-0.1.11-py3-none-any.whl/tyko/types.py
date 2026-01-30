import time
from collections import UserDict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .client import TykoClient


class RunStatus(StrEnum):
    CREATED = "created"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class Experiment:
    name: str


@dataclass(frozen=True, slots=True)
class Project:
    name: str


class RunParams(UserDict[str, object]):
    """A dict-like object for run parameters that syncs to the server.

    Supports dict-style access for setting values. Each modification
    is immediately synced to the server.

    Example:
        >>> with client.start_run(project="my-project") as run:
        ...     run.params["learning_rate"] = 0.001
        ...     run.params["batch_size"] = 32
        ...     run.params.update({"model": "resnet50", "epochs": 100})
    """

    def __init__(self, run_id: str, client: "TykoClient") -> None:
        super().__init__()
        self._run_id = run_id
        self._client = client

    def __setitem__(self, key: str, value: object) -> None:
        self.data[key] = value
        self._client.update_params(self._run_id, {key: value})

    def __repr__(self) -> str:
        return f"RunParams({self.data!r})"

    def update(self, values: dict[str, object], **kwargs: object) -> None:  # type: ignore[override]
        self.data.update(values, **kwargs)
        self._client.update_params(self._run_id, {**values, **kwargs})


class Environment(UserDict[str, object]):
    """A dict-like object for system information that syncs to the server.

    Supports dict-style access for setting values. Each modification
    is immediately synced to the server.

    Example:
        >>> with client.start_run(project="my-project") as run:
        ...     run.environment["python_version"] = "3.12"
        ...     run.environment["gpu_model"] = "A100"
        ...     run.environment.update({"git_commit": "abc123", "cuda_version": "12.1"})
    """

    def __init__(self, run_id: str, client: "TykoClient") -> None:
        super().__init__()
        self._run_id = run_id
        self._client = client

    def __setitem__(self, key: str, value: object) -> None:
        self.data[key] = value
        self._client.update_environment(self._run_id, {key: value})

    def __repr__(self) -> str:
        return f"Environment({self.data!r})"

    def update(self, values: dict[str, object], **kwargs: object) -> None:  # type: ignore[override]
        self.data.update(values, **kwargs)
        self._client.update_environment(self._run_id, {**values, **kwargs})


@dataclass(frozen=True, slots=True)
class Run:
    id: str
    name: str
    sequential: int
    experiment: Experiment
    project: Project
    _client: "TykoClient" = field(repr=False)
    _start_time_ns: int = field(default_factory=time.monotonic_ns, repr=False)
    params: RunParams = field(init=False, repr=False)
    environment: Environment = field(init=False, repr=False)
    # Mutable container to track if run has started (for frozen dataclass)
    _is_running: list[bool] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "params", RunParams(self.id, self._client))
        object.__setattr__(self, "environment", Environment(self.id, self._client))
        object.__setattr__(self, "_is_running", [False])

    @property
    def url(self) -> str:
        return f"https://tyko-labs.com/dashboard/projects/{self.project.name}/experiments/{self.experiment.name}/runs/{self.name}-{self.sequential}"

    def capture_environment(self) -> dict[str, object]:
        """Automatically capture and record environment information.

        Captures:
        - Python version
        - Platform/OS
        - CPU count
        - RAM size (if psutil available)
        - GPU count and names (if torch available)

        The captured information is automatically sent to the server.

        Returns:
            Dictionary of captured environment information
        """
        from .environment import capture_environment

        env_info = capture_environment()
        self.environment.update(env_info)
        return env_info

    def log(self, values: dict[str, float | int]) -> None:
        """Log metric values for this run.

        Each call creates a new entry. The server auto-assigns a sequential
        number for ordering, and the client provides both:
        - monotonic nanosecond timestamp for precise ordering
        - relative_time_ns: nanoseconds since run started (for scatter plots)

        Metric names can use prefixes for grouping in the UI:
        - "train/loss", "train/accuracy" → grouped under "train" panel
        - "eval/loss", "eval/accuracy" → grouped under "eval" panel
        - Underscore prefix also works: "train_loss" → grouped under "train"

        This matches the convention used by HuggingFace Transformers and
        other ML frameworks.

        Note: If the run is not yet in "running" status, calling log() will
        automatically transition it to "running". This ensures the UI shows
        the correct status even if the context manager isn't used.

        Args:
            values: Dictionary of metric names to numeric values.

        Example:
            >>> with client.start_run(project="mnist") as run:
            ...     for epoch in range(10):
            ...         for step, batch in enumerate(dataloader):
            ...             loss = train_step(batch)
            ...             run.log({"train/loss": loss, "epoch": epoch, "step": step})
            ...         val_loss, val_acc = evaluate(model)
            ...         run.log({"eval/loss": val_loss, "eval/accuracy": val_acc})
        """
        # Auto-transition to "running" on first log if not already running
        if not self._is_running[0]:
            self._client.update_status(self.id, RunStatus.RUNNING)
            self._is_running[0] = True

        # Use monotonic time in nanoseconds for precise ordering
        now_ns = time.monotonic_ns()
        # Compute relative time in nanoseconds since run started
        relative_time_ns = now_ns - self._start_time_ns
        self._client.log_metrics(self.id, values, _at=now_ns, _relative_time_ns=relative_time_ns)

    def __enter__(self) -> "Run":
        # Set the run status to running when entering the context manager
        if not self._is_running[0]:
            self._client.update_status(self.id, RunStatus.RUNNING)
            self._is_running[0] = True
        return self

    def __exit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None:
        status = RunStatus.FAILED if exc_type is not None else RunStatus.COMPLETED
        at = datetime.now(timezone.utc)
        self._client.close_run(self.id, status, at)
