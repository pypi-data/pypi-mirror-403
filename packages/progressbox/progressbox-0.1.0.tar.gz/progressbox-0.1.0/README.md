# ProgressBox

Stage-aware progress monitoring for parallel Python jobs.

![Python Version](https://img.shields.io/badge/python-3.9%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Status](https://img.shields.io/badge/status-alpha-orange)

## Features

- **Stage-aware tracking** - Monitor different stages of computation with timing analysis
- **True parallelism** - Built for multiprocessing, threading, and joblib
- **Rich statistics** - ETA, throughput, stage timing breakdown
- **Multiple renderers** - Terminal, Jupyter notebooks, or plain string output
- **Production ready** - Logging, snapshots, callbacks, error handling

## Installation

```bash
pip install progressbox
```

For development:
```bash
git clone https://github.com/yourorg/progressbox.git
cd progressbox
pip install -e .
```

## Quick Start

### Basic Usage

```python
from progressbox import Progress, Config

config = Config(total=100, n_workers=4)
with Progress(config) as progress:
    for i in range(100):
        progress.task_start(f"task_{i}")
        # ... do work ...
        progress.task_finish(f"task_{i}")
```

### With Stages

Track different phases of each task:

```python
from progressbox import Progress, Config

config = Config(total=100)
with Progress(config) as progress:
    for i in range(100):
        progress.task_start(f"task_{i}")

        progress.task_update(f"task_{i}", stage="loading")
        data = load_data(i)

        progress.task_update(f"task_{i}", stage="processing")
        result = process(data)

        progress.task_update(f"task_{i}", stage="saving")
        save(result)

        progress.task_finish(f"task_{i}")
```

### With Callbacks

Get notified on completion:

```python
from progressbox import Progress, Config

def on_complete(snapshot):
    print(f"Processed {snapshot['completed']} tasks")
    print(f"Total time: {snapshot['elapsed']:.1f}s")

config = Config(total=100, on_complete=on_complete)
with Progress(config) as progress:
    # ... process tasks ...
```

## Display Example

```
+======================================================================+
|                       Progress Monitoring                             |
+======================================================================+
| Progress: [################............] 42/100 (42%)                |
| Elapsed: 1m 23s | ETA: 1m 52s | Rate: 0.5 tasks/s                    |
+----------------------------------------------------------------------+
| Stage Analysis                                                        |
|   loading:     0.8s avg (32%)                                        |
|   processing:  1.2s avg (48%)                                        |
|   saving:      0.5s avg (20%)                                        |
+----------------------------------------------------------------------+
| Active Workers                                                        |
|   W0: processing  [####....] 1.2s                                    |
|   W1: loading     [##......] 0.3s                                    |
|   W2: saving      [######..] 0.4s                                    |
+======================================================================+
```

## Configuration Reference

```python
Config(
    # Required
    total=100,                    # Total number of tasks

    # Display options
    n_workers=6,                  # Number of worker rows to display
    inner_width=68,               # Display width (60, 68, 84, 100, or "auto")
    unicode=True,                 # Use Unicode box characters
    renderer="ascii",             # "ascii", "string", "jupyter", or "rich"

    # Feature toggles
    show_stage_analysis=True,     # Show stage timing breakdown
    show_workers=True,            # Show active worker list
    max_active_rows=12,           # Max worker rows to display

    # Performance
    refresh_hz=8.0,               # Display refresh rate
    display_interval=0.1,         # Minimum time between renders

    # Metrics
    ewma_alpha=0.2,               # ETA smoothing factor
    cache_speed_factor=0.8,       # Speed adjustment for cached tasks

    # Production settings
    fail_safe=True,               # Never raise exceptions
    headless_ok=True,             # Allow headless operation
    prod_safe=False,              # Conservative mode for production

    # Callbacks
    on_snapshot=None,             # Called periodically with state
    on_complete=None,             # Called when all tasks complete
    snapshot_interval_s=10.0,     # Seconds between snapshots
    log_interval_s=30.0,          # Seconds between log messages
)
```

## API Reference

### Progress Class

```python
from progressbox import Progress, Config

config = Config(total=100)
progress = Progress(config)

# Context manager (recommended)
with Progress(config) as p:
    p.task_start(task_id)
    p.task_update(task_id, stage="working")
    p.task_finish(task_id)

# Manual control
progress.start()           # Start rendering
progress.stop()            # Stop rendering (keeps state)
progress.close()           # Final cleanup
progress.tick()            # Force render update
```

### Task Methods

```python
# Start tracking a task
progress.task_start(
    task_id,              # Unique task identifier
    worker=None,          # Worker ID (auto-assigned if None)
    cached=False,         # Whether task uses cached results
    meta=None             # Optional metadata dict
)

# Update task state
progress.task_update(
    task_id,
    stage=None,           # New stage name
    progress=None,        # Progress ratio (0.0-1.0)
    sub_progress=None     # Sub-progress as (current, total)
)

# Mark task complete
progress.task_finish(task_id)

# Aliases
progress.stage_transition(task_id, stage)  # Same as task_update with stage
progress.stage_progress(task_id, ratio)    # Same as task_update with progress
progress.task_complete(task_id)            # Same as task_finish
```

### Helper Functions

```python
from progressbox import create_default_config

# Create config with sensible defaults
config = create_default_config(
    total=100,
    n_workers=8,
    renderer="string"
)
```

## Renderers

ProgressBox automatically selects the best renderer for your environment:

| Environment | Default Renderer |
|------------|------------------|
| Terminal (TTY) | `ascii` - Unicode box drawing |
| Jupyter notebook | `jupyter` - HTML with styling |
| Headless/CI | `string` - Plain text |

Force a specific renderer:

```python
config = Config(total=100, renderer="string")
```

## Joblib Integration

```python
from joblib import Parallel, delayed
from progressbox.adapters import joblib_progress

def process(item):
    # Your processing function
    return result

items = list(range(100))

with joblib_progress(total=len(items)) as progress:
    results = Parallel(n_jobs=4)(
        delayed(process)(item) for item in items
    )
```

## Thread Safety

All task methods (`task_start`, `task_update`, `task_finish`) are thread-safe and can be called from multiple workers concurrently.

## Error Handling

By default, ProgressBox operates in fail-safe mode (`fail_safe=True`), catching and logging errors without interrupting your workflow. For strict error handling:

```python
config = Config(total=100, fail_safe=False)
```

## License

MIT License - see LICENSE file for details.
