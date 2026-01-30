# Tyko Client - Python SDK

Official Python SDK for Tyko Labs.

Track experiments, manage models, and version datasets with a simple, intuitive API.

## Hierarchy

Tyko uses a three-level hierarchy to organize your ML work:

```
Project → Experiment → Run
```

- **Project**: Top-level container for your ML project (e.g., "mnist-classifier")
- **Experiment**: Groups related runs for comparison (e.g., "hyperparameter-search")
- **Run**: A single training execution with parameters, metrics, and artifacts

## Installation

Install via pip:

```bash
pip install tyko
```

## Quick Start

```python
from tyko import TykoClient

client = TykoClient()

# Simplest usage - just project name (uses "default" experiment)
# Environment info (Python version, CPU, GPU, etc.) is auto-captured
with client.start_run(project="my-ml-project") as run:
    run.params["learning_rate"] = 0.001
    run.params["batch_size"] = 32
    # ... your training code ...

# With params at creation time
with client.start_run(
    project="my-ml-project",
    experiment="hyperparameter-search",
    params={"learning_rate": 0.01, "batch_size": 64}
) as run:
    # Params are already set, can add more during the run
    run.params["epochs"] = 100
    # ... your training code ...
```

## Environment Capture

Environment information is automatically captured when you start a run:
- Python version
- Operating system/platform
- CPU count
- RAM size (if `psutil` is installed)
- GPU count and names (if `torch` is available)

You can also manually add environment details:

```python
with client.start_run(project="ml-experiments") as run:
    # Add custom environment info
    run.environment["git_commit"] = "abc123"
    run.environment["cuda_version"] = "12.1"
```

To use the standalone function:

```python
from tyko import capture_environment

env = capture_environment()
print(env)  # {'python_version': '3.12.1', 'platform': 'Linux-...', ...}
```

## Metric Logging

Log metrics during training using `run.log()`:

```python
with client.start_run(project="image-classifier") as run:
    run.params["learning_rate"] = 0.001
    run.params["batch_size"] = 32

    for epoch in range(100):
        train_loss = train_epoch(model, train_data)
        val_loss, val_acc = evaluate(model, val_data)

        # Log multiple metrics at once
        run.log({
            "train/loss": train_loss,
            "eval/loss": val_loss,
            "eval/accuracy": val_acc,
            "epoch": epoch,
        })
```

### Metric Naming Conventions

Use prefixes with slashes for grouped visualization in the dashboard:

| Pattern | Example | Dashboard Grouping |
|---------|---------|-------------------|
| `prefix/metric` | `train/loss`, `train/accuracy` | Grouped under "train" |
| `prefix/metric` | `eval/loss`, `eval/accuracy` | Grouped under "eval" |
| Plain name | `epoch`, `step` | Ungrouped |

This allows the dashboard to organize metrics into logical groups automatically.

## Configuration

### API Key

Set your API key via environment variable (recommended):

```bash
export TYKO_API_KEY="your-api-key"
```

Or pass it explicitly:

```python
client = TykoClient(api_key="your-api-key")
```

### Server URL

For self-hosted deployments, set the server URL:

```bash
export TYKO_API_URL="https://your-server.com"
```

Or:

```python
client = TykoClient(api_url="https://your-server.com")
```

## Development

### Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) package manager

### Setup

```bash
cd components/tyko-client
uv sync
```

### Testing

```bash
.venv/bin/pytest --cov=src/tyko --cov-report=term-missing
```

### Linting

```bash
# Check code style
.venv/bin/ruff check src/

# Format code
.venv/bin/black src/

# Type checking
.venv/bin/mypy src/
```

### Building

```bash
make build
```
