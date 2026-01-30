"""Tests for Jupyter HTML renderer."""
import pytest
from progressbox.render.jupyter import JupyterRenderer
from progressbox.state import ProgressState
from progressbox.config import Config


def test_jupyter_renderer_returns_html():
    """Test that Jupyter renderer returns HTML string."""
    config = Config(total=10, renderer="jupyter")
    state = ProgressState(total=10)
    renderer = JupyterRenderer(config)

    output = renderer.render(state, config)

    assert isinstance(output, str)
    assert "<" in output  # Contains HTML tags


def test_jupyter_renderer_contains_progress_bar():
    """Test that output contains progress bar HTML."""
    config = Config(total=100)
    state = ProgressState(total=100)
    state.completed = 50

    renderer = JupyterRenderer(config)
    output = renderer.render(state, config)

    assert "50%" in output or "50" in output
    assert "progress" in output.lower() or "width" in output.lower()


def test_jupyter_renderer_monospace_font():
    """Test that output uses monospace font for alignment."""
    config = Config(total=10)
    state = ProgressState(total=10)
    renderer = JupyterRenderer(config)

    output = renderer.render(state, config)

    assert "monospace" in output or "Consolas" in output or "Courier" in output


def test_jupyter_renderer_protocol_compliance():
    """Test that JupyterRenderer implements Renderer protocol."""
    config = Config(total=10)
    renderer = JupyterRenderer(config)

    assert hasattr(renderer, 'render')
    assert hasattr(renderer, 'start')
    assert hasattr(renderer, 'close')

    renderer.start()
    renderer.close()


def test_jupyter_renderer_stage_analysis():
    """Test that stage analysis is rendered when enabled."""
    config = Config(total=10, show_stage_analysis=True)
    state = ProgressState(total=10)

    # Add some stage data
    state.start_task("task1", stage="loading", worker_id=0)
    state.update_task("task1", stage="processing")
    state.finish_task("task1")

    renderer = JupyterRenderer(config)
    output = renderer.render(state, config)

    # Should contain stage information
    assert "loading" in output.lower() or "processing" in output.lower() or "stage" in output.lower()
