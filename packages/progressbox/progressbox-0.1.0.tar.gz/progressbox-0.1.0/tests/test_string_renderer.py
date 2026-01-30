"""Tests for string renderer."""
import pytest
from progressbox.render.string_ import StringRenderer
from progressbox.state import ProgressState
from progressbox.config import Config


def test_string_renderer_returns_string():
    """Test that string renderer returns plain string output."""
    config = Config(total=10, renderer="string")
    state = ProgressState(total=10)
    renderer = StringRenderer(config)

    output = renderer.render(state, config)

    assert isinstance(output, str)
    assert len(output) > 0


def test_string_renderer_contains_progress_info():
    """Test that output contains basic progress information."""
    config = Config(total=100)
    state = ProgressState(total=100)
    state.completed = 50

    renderer = StringRenderer(config)
    output = renderer.render(state, config)

    assert "50" in output  # Completed count
    assert "100" in output  # Total count


def test_string_renderer_protocol_compliance():
    """Test that StringRenderer implements Renderer protocol."""
    config = Config(total=10)
    renderer = StringRenderer(config)

    # Should have all protocol methods
    assert hasattr(renderer, 'render')
    assert hasattr(renderer, 'start')
    assert hasattr(renderer, 'close')

    # Methods should be callable without error
    renderer.start()
    renderer.close()
