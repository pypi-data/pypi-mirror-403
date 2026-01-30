"""Tests for the Tyko client."""

import time
from unittest.mock import patch

import pytest
from pytest_httpx import HTTPXMock

from tyko import Experiment, Project, Run
from tyko.client import TykoClient


@pytest.fixture(autouse=True)
def default_api_key():
    """Set default environment variables for tests."""
    with patch.dict("os.environ", {"TYKO_API_KEY": "test-api-key"}):
        yield "test-api-key"


def test_client_uses_default_endpoint(default_api_key: str):
    """Test that the client uses the default API endpoint."""
    client = TykoClient()
    assert client.api_url == "https://api.tyko-labs.com"
    assert client.api_key == default_api_key


def test_client_uses_env_vars():
    """Test that the client uses environment variables for configuration."""
    with patch.dict("os.environ", {"TYKO_API_URL": "http://localhost:8000"}):
        client = TykoClient()
        assert client.api_url == "http://localhost:8000"


def test_start_run_with_project(httpx_mock: HTTPXMock):
    """Test starting a run with just a project name."""

    httpx_mock.add_response(
        method="POST",
        url="https://api.tyko-labs.com/runs",
        json={
            "id": "run-id-1234",
            "project": {"name": "my-project"},
            "experiment": {"name": "default"},
            "name": "run-1234",
            "sequential": 1,
        },
    )
    # PATCH for setting status to "running" on __enter__
    httpx_mock.add_response(
        method="PATCH",
        url="https://api.tyko-labs.com/runs/run-id-1234",
        json={},
    )
    # PATCH for setting status to "completed" on __exit__
    httpx_mock.add_response(
        method="PATCH",
        url="https://api.tyko-labs.com/runs/run-id-1234",
        json={},
    )

    client = TykoClient()

    with client.start_run(project="my-project") as run:
        assert isinstance(run, Run)
        assert isinstance(run.experiment, Experiment)
        assert isinstance(run.project, Project)
        assert run.project.name == "my-project"
        assert run.experiment.name == "default"
        assert run.name == "run-1234"

    requests = httpx_mock.get_requests()

    assert len(requests) == 3
    assert requests[0].url == "https://api.tyko-labs.com/runs"
    assert requests[0].headers["Authorization"] == "Bearer test-api-key"

    # Verify environment is automatically captured and sent
    import json

    create_body = json.loads(requests[0].content)
    assert "environment" in create_body
    assert "python_version" in create_body["environment"]
    assert "platform" in create_body["environment"]
    assert "cpu_count" in create_body["environment"]

    # Verify status is set to "running" on enter
    running_body = json.loads(requests[1].content)
    assert running_body["status"] == "running"


def test_run_closes_with_completed_status(httpx_mock: HTTPXMock):
    """Test that a run sends 'completed' status when exiting without exception."""
    httpx_mock.add_response(
        method="POST",
        url="https://api.tyko-labs.com/runs",
        json={
            "id": "run-id-5678",
            "project": {"name": "test-project"},
            "experiment": {"name": "default"},
            "name": "test-run",
            "sequential": 1,
        },
    )
    # PATCH for "running" status
    httpx_mock.add_response(
        method="PATCH",
        url="https://api.tyko-labs.com/runs/run-id-5678",
        json={},
    )
    # PATCH for "completed" status
    httpx_mock.add_response(
        method="PATCH",
        url="https://api.tyko-labs.com/runs/run-id-5678",
        json={},
    )

    client = TykoClient()

    with client.start_run(project="test-project"):
        pass

    requests = httpx_mock.get_requests()

    # First PATCH sets status to "running"
    running_request = requests[1]
    assert running_request.method == "PATCH"

    import json

    running_body = json.loads(running_request.content)
    assert running_body["status"] == "running"

    # Second PATCH sets status to "completed"
    completed_request = requests[2]
    assert completed_request.method == "PATCH"
    assert completed_request.url == "https://api.tyko-labs.com/runs/run-id-5678"

    completed_body = json.loads(completed_request.content)
    assert completed_body["status"] == "completed"
    assert "at" in completed_body


def test_run_closes_with_failed_status_on_exception(httpx_mock: HTTPXMock):
    """Test that a run sends 'failed' status when exiting with an exception."""
    httpx_mock.add_response(
        method="POST",
        url="https://api.tyko-labs.com/runs",
        json={
            "id": "run-id-9999",
            "project": {"name": "test-project"},
            "experiment": {"name": "default"},
            "name": "failed-run",
            "sequential": 2,
        },
    )
    # PATCH for "running" status
    httpx_mock.add_response(
        method="PATCH",
        url="https://api.tyko-labs.com/runs/run-id-9999",
        json={},
    )
    # PATCH for "failed" status
    httpx_mock.add_response(
        method="PATCH",
        url="https://api.tyko-labs.com/runs/run-id-9999",
        json={},
    )

    client = TykoClient()

    with pytest.raises(ValueError):
        with client.start_run(project="test-project"):
            raise ValueError("Something went wrong")

    requests = httpx_mock.get_requests()

    # Second PATCH sets status to "failed"
    failed_request = requests[2]
    assert failed_request.method == "PATCH"
    assert failed_request.url == "https://api.tyko-labs.com/runs/run-id-9999"

    import json

    body = json.loads(failed_request.content)
    assert body["status"] == "failed"
    assert "at" in body


def test_run_params_update(httpx_mock: HTTPXMock):
    """Test setting multiple config values with update()."""
    httpx_mock.add_response(
        method="POST",
        url="https://api.tyko-labs.com/runs",
        json={
            "id": "run-config-test",
            "project": {"name": "test-project"},
            "experiment": {"name": "default"},
            "name": "config-run",
            "sequential": 1,
        },
    )
    # PATCH for "running" status
    httpx_mock.add_response(
        method="PATCH",
        url="https://api.tyko-labs.com/runs/run-config-test",
        json={},
    )
    # PATCH for params update
    httpx_mock.add_response(
        method="PATCH",
        url="https://api.tyko-labs.com/runs/run-config-test",
        json={},
    )
    # PATCH for "completed" status
    httpx_mock.add_response(
        method="PATCH",
        url="https://api.tyko-labs.com/runs/run-config-test",
        json={},
    )

    client = TykoClient()

    with client.start_run(project="test-project") as run:
        run.params.update({"learning_rate": 0.001, "batch_size": 32})

    requests = httpx_mock.get_requests()

    # First request is POST to create run
    assert requests[0].method == "POST"

    # Second request is PATCH to set status to "running"
    assert requests[1].method == "PATCH"

    import json

    running_body = json.loads(requests[1].content)
    assert running_body["status"] == "running"

    # Third request is PATCH to set config
    assert requests[2].method == "PATCH"
    assert requests[2].url == "https://api.tyko-labs.com/runs/run-config-test"

    config_body = json.loads(requests[2].content)
    assert config_body["params"] == {"learning_rate": 0.001, "batch_size": 32}

    # Fourth request is PATCH to close run
    assert requests[3].method == "PATCH"
    close_body = json.loads(requests[3].content)
    assert close_body["status"] == "completed"


def test_run_params_setitem(httpx_mock: HTTPXMock):
    """Test setting config values with dict-style access."""
    httpx_mock.add_response(
        method="POST",
        url="https://api.tyko-labs.com/runs",
        json={
            "id": "run-setitem-test",
            "project": {"name": "test-project"},
            "experiment": {"name": "default"},
            "name": "setitem-run",
            "sequential": 1,
        },
    )
    # PATCH for "running" status + two for config sets + one for close
    httpx_mock.add_response(
        method="PATCH",
        url="https://api.tyko-labs.com/runs/run-setitem-test",
        json={},
    )
    httpx_mock.add_response(
        method="PATCH",
        url="https://api.tyko-labs.com/runs/run-setitem-test",
        json={},
    )
    httpx_mock.add_response(
        method="PATCH",
        url="https://api.tyko-labs.com/runs/run-setitem-test",
        json={},
    )
    httpx_mock.add_response(
        method="PATCH",
        url="https://api.tyko-labs.com/runs/run-setitem-test",
        json={},
    )

    client = TykoClient()

    with client.start_run(project="test-project") as run:
        run.params["learning_rate"] = 0.001
        run.params["batch_size"] = 32

    requests = httpx_mock.get_requests()

    import json

    # Second request sets status to "running"
    running_body = json.loads(requests[1].content)
    assert running_body["status"] == "running"

    # Third request sets learning_rate
    config_body_1 = json.loads(requests[2].content)
    assert config_body_1["params"] == {"learning_rate": 0.001}

    # Fourth request sets batch_size
    config_body_2 = json.loads(requests[3].content)
    assert config_body_2["params"] == {"batch_size": 32}


def test_run_params_with_various_types(httpx_mock: HTTPXMock):
    """Test setting config with bool, int, float, and string values."""
    httpx_mock.add_response(
        method="POST",
        url="https://api.tyko-labs.com/runs",
        json={
            "id": "run-types-test",
            "project": {"name": "test-project"},
            "experiment": {"name": "default"},
            "name": "types-run",
            "sequential": 1,
        },
    )
    # PATCH for "running" status
    httpx_mock.add_response(
        method="PATCH",
        url="https://api.tyko-labs.com/runs/run-types-test",
        json={},
    )
    # PATCH for params update
    httpx_mock.add_response(
        method="PATCH",
        url="https://api.tyko-labs.com/runs/run-types-test",
        json={},
    )
    # PATCH for "completed" status
    httpx_mock.add_response(
        method="PATCH",
        url="https://api.tyko-labs.com/runs/run-types-test",
        json={},
    )

    client = TykoClient()

    config: dict[str, object] = {
        "enabled": True,
        "epochs": 100,
        "learning_rate": 0.001,
        "model_name": "transformer",
    }

    with client.start_run(project="test-project") as run:
        run.params.update(config)

    requests = httpx_mock.get_requests()

    import json

    # Second request is "running" status, third is params
    config_body = json.loads(requests[2].content)
    assert config_body["params"]["enabled"] is True
    assert config_body["params"]["epochs"] == 100
    assert config_body["params"]["learning_rate"] == 0.001
    assert config_body["params"]["model_name"] == "transformer"


def test_run_params_local_cache(httpx_mock: HTTPXMock):
    """Test that config values are cached locally for reading."""
    httpx_mock.add_response(
        method="POST",
        url="https://api.tyko-labs.com/runs",
        json={
            "id": "run-cache-test",
            "project": {"name": "test-project"},
            "experiment": {"name": "default"},
            "name": "cache-run",
            "sequential": 1,
        },
    )
    # PATCH for "running" status
    httpx_mock.add_response(
        method="PATCH",
        url="https://api.tyko-labs.com/runs/run-cache-test",
        json={},
    )
    # PATCH for params update
    httpx_mock.add_response(
        method="PATCH",
        url="https://api.tyko-labs.com/runs/run-cache-test",
        json={},
    )
    # PATCH for "completed" status
    httpx_mock.add_response(
        method="PATCH",
        url="https://api.tyko-labs.com/runs/run-cache-test",
        json={},
    )

    client = TykoClient()

    with client.start_run(project="test-project") as run:
        run.params["learning_rate"] = 0.001
        # Should be able to read back the value from local cache
        assert run.params["learning_rate"] == 0.001
        assert "learning_rate" in run.params
        assert len(run.params) == 1


def test_run_log_method(httpx_mock: HTTPXMock):
    """Test the run.log() method for logging metrics."""
    httpx_mock.add_response(
        method="POST",
        url="https://api.tyko-labs.com/runs",
        json={
            "id": "run-id-log-test",
            "project": {"name": "test-project"},
            "experiment": {"name": "default"},
            "name": "test-run",
            "sequential": 1,
        },
    )
    # PATCH for "running" status
    httpx_mock.add_response(
        method="PATCH",
        url="https://api.tyko-labs.com/runs/run-id-log-test",
        json={},
    )
    # Allow the entries endpoint to be called multiple times
    httpx_mock.add_response(
        method="POST",
        url="https://api.tyko-labs.com/runs/run-id-log-test/entries",
        json={"status": "success"},
    )
    httpx_mock.add_response(
        method="POST",
        url="https://api.tyko-labs.com/runs/run-id-log-test/entries",
        json={"status": "success"},
    )
    # PATCH for "completed" status
    httpx_mock.add_response(
        method="PATCH",
        url="https://api.tyko-labs.com/runs/run-id-log-test",
        json={},
    )

    client = TykoClient()

    with client.start_run(project="test-project") as run:
        # Log some metrics
        run.log({"loss": 0.5, "accuracy": 0.8})
        time.sleep(0.01)  # Small delay to ensure different timestamps
        run.log({"loss": 0.4, "accuracy": 0.85})

    requests = httpx_mock.get_requests()

    # Should have: POST /runs, PATCH (running), POST entries (x2), PATCH (completed)
    assert len(requests) == 5

    # Check the first log entries request (after running status PATCH)
    log_request1 = requests[2]
    assert log_request1.url == "https://api.tyko-labs.com/runs/run-id-log-test/entries"
    assert log_request1.method == "POST"

    import json

    log_body1 = json.loads(log_request1.content)
    assert "entries" in log_body1
    assert len(log_body1["entries"]) == 1

    # Check first entry
    entry1 = log_body1["entries"][0]
    assert "timestamp" in entry1
    assert "values" in entry1
    assert entry1["values"] == {"loss": 0.5, "accuracy": 0.8}

    # Check the second log entries request
    log_request2 = requests[3]
    log_body2 = json.loads(log_request2.content)
    entry2 = log_body2["entries"][0]
    assert entry2["values"] == {"loss": 0.4, "accuracy": 0.85}

    # Timestamps should be different
    assert entry1["timestamp"] != entry2["timestamp"]


def test_run_log_with_grouped_metrics(httpx_mock: HTTPXMock):
    """Test logging metrics with grouped names (train/, eval/)."""
    httpx_mock.add_response(
        method="POST",
        url="https://api.tyko-labs.com/runs",
        json={
            "id": "run-id-grouped",
            "project": {"name": "test-project"},
            "experiment": {"name": "default"},
            "name": "test-run",
            "sequential": 1,
        },
    )
    # PATCH for "running" status
    httpx_mock.add_response(
        method="PATCH",
        url="https://api.tyko-labs.com/runs/run-id-grouped",
        json={},
    )
    httpx_mock.add_response(
        method="POST",
        url="https://api.tyko-labs.com/runs/run-id-grouped/entries",
        json={"status": "success"},
    )
    # PATCH for "completed" status
    httpx_mock.add_response(
        method="PATCH",
        url="https://api.tyko-labs.com/runs/run-id-grouped",
        json={},
    )

    client = TykoClient()

    with client.start_run(project="test-project") as run:
        # Log grouped metrics
        run.log(
            {
                "train/loss": 0.5,
                "train/accuracy": 0.8,
                "eval/loss": 0.6,
                "eval/accuracy": 0.75,
            }
        )

    requests = httpx_mock.get_requests()
    # Log request is now at index 2 (after POST /runs and PATCH running)
    log_request = requests[2]

    import json

    log_body = json.loads(log_request.content)
    entry = log_body["entries"][0]

    assert "train/loss" in entry["values"]
    assert "train/accuracy" in entry["values"]
    assert "eval/loss" in entry["values"]
    assert "eval/accuracy" in entry["values"]


def test_run_log_multiple_calls(httpx_mock: HTTPXMock):
    """Test that multiple log calls work correctly."""
    httpx_mock.add_response(
        method="POST",
        url="https://api.tyko-labs.com/runs",
        json={
            "id": "run-id-batch",
            "project": {"name": "test-project"},
            "experiment": {"name": "default"},
            "name": "test-run",
            "sequential": 1,
        },
    )
    # PATCH for "running" status
    httpx_mock.add_response(
        method="PATCH",
        url="https://api.tyko-labs.com/runs/run-id-batch",
        json={},
    )
    # Add responses for 5 log calls
    for _ in range(5):
        httpx_mock.add_response(
            method="POST",
            url="https://api.tyko-labs.com/runs/run-id-batch/entries",
            json={"status": "success"},
        )
    # PATCH for "completed" status
    httpx_mock.add_response(
        method="PATCH",
        url="https://api.tyko-labs.com/runs/run-id-batch",
        json={},
    )

    client = TykoClient()

    with client.start_run(project="test-project") as run:
        # Multiple log calls
        for i in range(5):
            run.log({"step": i, "loss": 1.0 / (i + 1)})

    requests = httpx_mock.get_requests()

    # Should have: 1 POST /runs + 1 PATCH (running) + 5 POST /entries + 1 PATCH (completed) = 8 requests
    assert len(requests) == 8

    # Verify the entries were logged with correct values
    for i in range(5):
        log_request = requests[i + 2]  # Skip POST /runs and PATCH (running)

        import json

        log_body = json.loads(log_request.content)
        assert len(log_body["entries"]) == 1

        entry = log_body["entries"][0]
        assert entry["values"]["step"] == i
        assert entry["values"]["loss"] == pytest.approx(1.0 / (i + 1))


# def test_start_run_with_experiment():
#     """Test starting a run with project and experiment names."""
#     client = TykoClient()
#     with client.start_run(project="my-project", experiment="baseline") as run:
#         assert run.project.name == "my-project"
#         assert run.experiment.name == "baseline"


# def test_start_run_with_custom_name():
#     """Test starting a run with a custom run name."""
#     client = TykoClient()
#     with client.start_run(project="my-project", name="run-v1") as run:
#         assert run.name == "run-v1"


# def test_run_generates_random_name():
#     """Test that runs generate random names when not provided."""
#     client = TykoClient()
#     with client.start_run(project="my-project") as run:
#         assert run.name is not None
#         assert len(run.name) > 0
