"""Tyko client for API communication."""

import os
from datetime import datetime
from typing import Any, Mapping

# from types import TracebackType
import httpx

from .environment import capture_environment
from .types import Experiment, Project, Run, RunStatus

# from .utils import generate_random_run_name


class TykoClient:
    """Client for interacting with the Tyko Labs API."""

    _client: httpx.Client

    def __init__(self, api_url: str | None = None, api_key: str | None = None):
        """Initialize the Tyko client.

        Args:
            api_url: The base URL for the Tyko API. Defaults to the production
                server at https://api.tyko-labs.com.
            api_key: API key for authentication. If not provided, will check
                the TYKO_API_KEY environment variable. If still not found,
                an anonymous session will be created automatically.
        """

        if api_url is None:
            api_url = os.environ.get("TYKO_API_URL", "https://api.tyko-labs.com")

        self.api_url = api_url.rstrip("/")

        # Get API key from argument or environment variable
        self.api_key = api_key or os.environ.get("TYKO_API_KEY")

        if self.api_key is None:
            raise RuntimeError("API key is required for TykoClient")

    def _headers(self) -> dict[str, str]:
        headers: dict[str, str] = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def _post(self, path: str, data: Mapping[str, Any]) -> httpx.Response:
        url = f"{self.api_url}{path}"
        response = httpx.post(url, json=data, headers=self._headers())
        response.raise_for_status()
        return response

    def _patch(self, path: str, data: Mapping[str, Any]) -> httpx.Response:
        url = f"{self.api_url}{path}"
        response = httpx.patch(url, json=data, headers=self._headers())
        response.raise_for_status()
        return response

    def update_status(self, run_id: str, status: RunStatus) -> None:
        """Update the status of a run.

        Args:
            run_id: The ID of the run to update.
            status: The new status for the run.
        """
        self._patch(f"/runs/{run_id}", {"status": status})

    def close_run(self, run_id: str, status: RunStatus, at: datetime) -> None:
        """Close a run with the given status and timestamp.

        Args:
            run_id: The ID of the run to close.
            status: The final status of the run ('completed' or 'failed').
            at: Timestamp of when the run ended.
        """
        self._patch(f"/runs/{run_id}", {"status": status, "at": at.isoformat()})

    def update_params(self, run_id: str, params: dict[str, object]) -> None:
        """Update the parameters for a run.

        Params values are merged with existing params (new keys are added,
        existing keys are overwritten).

        Args:
            run_id: The ID of the run to update.
            params: Dictionary of parameter values to set/update.
        """
        self._patch(f"/runs/{run_id}", {"params": params})

    def update_environment(self, run_id: str, environment: dict[str, object]) -> None:
        """Update the system information for a run.

        System info values are merged with existing system info (new keys are added,
        existing keys are overwritten).

        Args:
            run_id: The ID of the run to update.
            environment: Dictionary of system information to set/update.
        """
        self._patch(f"/runs/{run_id}", {"environment": environment})

    def log_metrics(
        self,
        run_id: str,
        values: dict[str, float | int],
        *,
        _at: int,
        _relative_time_ns: int,
    ) -> None:
        """Log metric values for a run.

        Each call creates a new entry with a sequential number auto-assigned
        by the server for ordering.

        Metric names can use prefixes for grouping in the UI:
        - "train/loss", "train/accuracy" → grouped under "train"
        - "eval/loss", "eval/accuracy" → grouped under "eval"
        - Underscore also works: "train_loss" → grouped under "train"

        Args:
            run_id: The ID of the run to log metrics for.
            values: Dictionary of metric names to values.
            _at: Monotonic nanosecond timestamp from the client for ordering.
            _relative_time_ns: Nanoseconds since run started (for aligning metrics).
        """
        entry = {
            "timestamp": _at,
            "relative_time_ns": _relative_time_ns,
            "values": values,
        }
        data = {"entries": [entry]}
        self._post(f"/runs/{run_id}/entries", data)

    def start_run(
        self,
        project: str,
        experiment: str | None = None,
        params: dict[str, object] | None = None,
    ) -> Run:
        """Start a new run.

        This is the main method for tracking experiments. It creates a run
        within the specified project and optional experiment.

        Environment information (Python version, platform, CPU, RAM, GPU) is
        automatically captured and sent to the server.

        Args:
            project: The project name. Required.
            experiment: Optional experiment name. If not provided, the server
                will use the default experiment.
            params: Optional dictionary of parameters to log with the run.
                These are static values like hyperparameters that don't change
                during the run.

        Returns:
            A Run instance that can be used as a context manager.
        """
        data: dict[str, Any] = {"project": project}
        if experiment is not None:
            data["experiment"] = experiment
        if params is not None:
            data["params"] = params

        # Auto-capture environment information
        data["environment"] = capture_environment()

        response = self._post("/runs", data)

        response_json = response.json()

        run_id = response_json["id"]
        run_name = response_json["name"]
        project_name = response_json["project"]["name"]
        experiment_name = response_json["experiment"]["name"]
        sequential = response_json["sequential"]

        return Run(
            id=run_id,
            name=run_name,
            sequential=sequential,
            experiment=Experiment(name=experiment_name),
            project=Project(name=project_name),
            _client=self,
        )


# # Defnault experiment name used when none is specified
# DEFAULT_EXPERIMENT = "default"


# class Run:
#     """A run represents a single execution within an experiment.

#     Runs are used to log parameters, metrics, and artifacts for a specific
#     experiment execution. They are typically used as context managers to
#     automatically handle the run lifecycle.

#     Hierarchy: Project → Experiment → Run

#     Attributes:
#         name: The name of this run.
#         experiment: The experiment this run belongs to.
#         project: The project this run belongs to (via experiment).

#     Example:
#         >>> # Simplest usage - just project name
#         >>> with client.start_run(project="my-project") as run:
#         ...     run.log_params({"learning_rate": 0.001})
#         ...     run.log_metric("accuracy", 0.95)
#         >>>
#         >>> # With experiment name
#         >>> with client.start_run(project="my-project", experiment="baseline") as run:
#         ...     run.log_metric("accuracy", 0.95)
#     """
#     _experiment: "Experiment | None"
#     _project: "Project | None"

#     def __init__(
#         self,
#         experiment: "Experiment | None" = None,
#         project: "Project | None" = None,
#         name: str | None = None,
#     ):
#         """Initialize a run.

#         Args:
#             experiment: The experiment this run belongs to.
#             project: The project this run belongs to.
#             name: Optional name for the run. If not provided, a random name
#                 will be generated (e.g., "brave-golden-eagle").
#         """
#         self._experiment = experiment
#         self._project = project or (experiment.project if experiment else None)
#         self.name = name if name is not None else generate_random_run_name()

#     @property
#     def experiment(self) -> "Experiment | None":
#         """The experiment this run belongs to."""
#         return self._experiment

#     @property
#     def project(self) -> "Project | None":
#         """The project this run belongs to."""
#         return self._project

#     def __repr__(self) -> str:
#         exp_name = self._experiment.name if self._experiment else "None"
#         proj_name = self._project.name if self._project else "None"
#         return f"<Run name={self.name} project={proj_name} experiment={exp_name}>"

#     def __enter__(self) -> "Run":
#         """Enter the context manager and start the run.

#         Returns:
#             The run instance.
#         """
#         return self

#     def __exit__(
#             self,
#             exc_type: type[BaseException] | None,
#             exc_value: BaseException | None,
#             traceback: TracebackType | None
#         ) -> bool:
#         """Exit the context manager and finalize the run.

#         Args:
#             exc_type: The type of exception that occurred, if any.
#             exc_value: The exception instance that occurred, if any.
#             traceback: The traceback object for the exception, if any.

#         Returns:
#             False to propagate exceptions, True to suppress them.
#         """
#         return True


# class Experiment:
#     """An experiment groups related runs for comparison and organization.

#     Experiments belong to a project and serve as containers for multiple runs.
#     Each experiment has a unique name within its project and can track
#     multiple training runs with different parameters and configurations.

#     Hierarchy: Project → Experiment → Run

#     Attributes:
#         name: The name of the experiment.
#         project: The project this experiment belongs to.

#     Example:
#         >>> # Most users should use client.start_run() directly
#         >>> with client.start_run(project="my-project", experiment="baseline") as run:
#         ...     run.log_params({"learning_rate": 0.001})
#     """
#     _project: "Project | None"

#     def __init__(
#         self,
#         name: str,
#         project: "Project | None" = None,
#     ):
#         """Initialize an experiment.

#         Args:
#             name: The name of the experiment.
#             project: The project this experiment belongs to.
#         """
#         self.name = name
#         self._project = project

#     @property
#     def project(self) -> "Project | None":
#         """The project this experiment belongs to."""
#         return self._project

#     def __repr__(self) -> str:
#         project_name = self._project.name if self._project else "None"
#         return f"<Experiment name={self.name} project={project_name}>"

#     def start_run(self, name: str | None = None) -> Run:
#         """Start a new run within this experiment.

#         Creates and returns a new run instance that can be used to log
#         parameters, metrics, and artifacts. Best used as a context manager
#         to ensure proper cleanup.

#         Args:
#             name: Optional name for the run. If not provided, a random name
#                 will be generated (e.g., "brave-golden-eagle").

#         Returns:
#             A new Run instance associated with this experiment.

#         Example:
#             >>> with experiment.start_run() as run:
#             ...     run.log_params({"batch_size": 32})
#         """
#         return Run(experiment=self, project=self._project, name=name)


# class Project:
#     """A project is the top-level organizational unit in Tyko.

#     Projects contain experiments, which in turn contain runs.

#     Hierarchy: Project → Experiment → Run

#     Attributes:
#         name: The name of the project.
#         slug: The URL-safe identifier for the project.

#     Example:
#         >>> # Most users should use client.start_run() directly
#         >>> with client.start_run(project="my-project") as run:
#         ...     run.log_params({"learning_rate": 0.001})
#         >>>
#         >>> # For more control, create project and experiment explicitly
#         >>> project = client.create_project("mnist-classifier")
#         >>> experiment = project.create_experiment("hyperparameter-search")
#         >>> with experiment.start_run() as run:
#         ...     run.log_params({"learning_rate": 0.01})
#     """
#     _client: "TykoClient | None"

#     def __init__(
#         self,
#         name: str,
#         slug: str | None = None,
#         client: "TykoClient | None" = None,
#     ):
#         """Initialize a project.

#         Args:
#             name: The name of the project.
#             slug: Optional URL-safe identifier. If not provided, derived from name.
#             client: The Tyko client instance that created this project.
#         """
#         self.name = name
#         self.slug = slug or name.lower().replace(" ", "-")
#         self._client = client

#     def __repr__(self) -> str:
#         return f"<Project name={self.name} slug={self.slug}>"

#     def create_experiment(self, name: str) -> Experiment:
#         """Create a new experiment within this project.

#         Args:
#             name: A descriptive name for the experiment.

#         Returns:
#             An Experiment instance that can be used to start runs.

#         Example:
#             >>> project = client.create_project("my-ml-model")
#             >>> experiment = project.create_experiment("fine-tuning")
#             >>> with experiment.start_run() as run:
#             ...     run.log_params({"learning_rate": 0.001})
#         """
#         return Experiment(name=name, project=self)

#     def start_run(
#         self,
#         experiment: str | None = None,
#         name: str | None = None,
#     ) -> Run:
#         """Start a new run within this project.

#         Args:
#             experiment: Optional experiment name. If not provided, uses "default".
#             name: Optional name for the run. If not provided, a random name
#                 will be generated.

#         Returns:
#             A new Run instance.

#         Example:
#             >>> project = client.create_project("my-project")
#             >>> with project.start_run() as run:
#             ...     run.log_metric("accuracy", 0.95)
#         """
#         exp_name = experiment or DEFAULT_EXPERIMENT
#         exp = Experiment(name=exp_name, project=self)
#         return Run(experiment=exp, project=self, name=name)

#
# class TykoClient:
# """Client for interacting with the Tyko Labs API.
#
# The TykoClient is the main entry point for tracking experiments with Tyko.
# It handles authentication, project creation, and communication with the
# Tyko API server.
#
# Hierarchy: Project → Experiment → Run
#
# Attributes:
# api_url: The base URL for the Tyko API.
# api_key: The API key for authentication (if provided).
# session: The requests session for API communication.
#
# Example:
# >>> client = TykoClient()
# >>>
# >>> # Simplest usage - just project name
# >>> with client.start_run(project="my-project") as run:
# ...     run.log_metric("accuracy", 0.95)
# >>>
# >>> # With experiment name
# >>> with client.start_run(project="my-project", experiment="baseline") as run:
# ...     run.log_metric("accuracy", 0.95)
# """
#
# api_url: str
#
# def __init__(self, api_url: str | None = None, api_key: Optional[str] = None):
# """Initialize the Tyko client.
#
# Args:
# api_url: The base URL for the Tyko API. Defaults to the production
# server at https://api.tyko-labs.com.
# api_key: API key for authentication. If not provided, will check
# the TYKO_API_KEY environment variable. If still not found,
# an anonymous session will be created automatically.
#
# Example:
# >>> # With explicit API key
# >>> client = TykoClient(api_key="your-api-key")
# >>>
# >>> # Using environment variable
# >>> import os
# >>> os.environ["TYKO_API_KEY"] = "your-api-key"
# >>> client = TykoClient()
# >>>
# >>> # Anonymous session (no API key)
# >>> client = TykoClient()
# """
# if api_url is None:
# api_url = os.environ.get("TYKO_API_URL", "https://api.tyko-labs.com")
# self.api_url = api_url.rstrip("/")
# self.api_key = api_key or os.environ.get("TYKO_API_KEY")
# self.session = requests.Session()
#
# if self.api_key:
# self.session.headers.update({"Authorization": f"Bearer {self.api_key}"})
#
# self.session.headers.update({"Content-Type": "application/json"})
#
# def start_run(
# self,
# project: str,
# experiment: str | None = None,
# name: str | None = None,
# ) -> Run:
# """Start a new run.
#
# This is the main method for tracking experiments. It creates a run
# within the specified project and optional experiment.
#
# Args:
# project: The project name. Required.
# experiment: Optional experiment name. If not provided, uses "default".
# name: Optional name for the run. If not provided, a random name
# will be generated (e.g., "brave-golden-eagle").
#
# Returns:
# A Run instance that can be used as a context manager.
#
# Example:
# >>> client = TykoClient()
# >>>
# >>> # Simple usage - just project name
# >>> with client.start_run(project="mnist-classifier") as run:
# ...     run.log_params({"learning_rate": 0.001})
# ...     run.log_metric("accuracy", 0.95)
# >>>
# >>> # With experiment name
# >>> with client.start_run(
# ...     project="mnist-classifier",
# ...     experiment="hyperparameter-search"
# ... ) as run:
# ...     run.log_params({"learning_rate": 0.01})
# >>>
# >>> # With custom run name
# >>> with client.start_run(
# ...     project="mnist-classifier",
# ...     name="baseline-v1"
# ... ) as run:
# ...     run.log_metric("accuracy", 0.95)
# """
# proj = Project(name=project, client=self)
# exp_name = experiment or DEFAULT_EXPERIMENT
# exp = Experiment(name=exp_name, project=proj)
# return Run(experiment=exp, project=proj, name=name)
#
# def create_project(self, name: str, slug: str | None = None) -> Project:
# """Create a new project.
#
# For most use cases, use start_run() directly instead.
#
# Args:
# name: A descriptive name for the project.
# slug: Optional URL-safe identifier. If not provided, derived from name.
#
# Returns:
# A Project instance.
#
# Example:
# >>> project = client.create_project("my-ml-model")
# >>> experiment = project.create_experiment("fine-tuning")
# >>> with experiment.start_run() as run:
# ...     run.log_params({"learning_rate": 0.001})
# """
# return Project(name=name, slug=slug, client=self)
#
