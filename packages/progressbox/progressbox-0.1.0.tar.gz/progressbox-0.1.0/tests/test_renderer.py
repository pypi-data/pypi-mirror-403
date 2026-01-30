"""Tests for rendering with golden snapshots."""
import pytest
import os
from pathlib import Path
from progressbox.render.ascii import ASCIIRenderer
from progressbox.state import ProgressState
from progressbox.config import Config

GOLDEN_DIR = Path(__file__).parent / "golden"


def save_golden(name: str, content: str) -> None:
    """Save a golden snapshot (use during development)."""
    GOLDEN_DIR.mkdir(exist_ok=True)
    (GOLDEN_DIR / name).write_text(content)


def load_golden(name: str) -> str:
    """Load a golden snapshot."""
    return (GOLDEN_DIR / name).read_text()


class TestASCIIRendererBasic:
    """Basic ASCII renderer tests."""

    def test_ascii_renderer_returns_string(self):
        """Test ASCII renderer returns non-empty string."""
        config = Config(total=10)
        state = ProgressState(total=10)
        renderer = ASCIIRenderer(config)
        output = renderer.render(state, config)

        assert isinstance(output, str)
        assert len(output) > 0

    def test_ascii_renderer_has_box_borders(self):
        """Test output has Unicode box drawing characters."""
        config = Config(total=10)
        state = ProgressState(total=10)
        renderer = ASCIIRenderer(config)
        output = renderer.render(state, config)

        # Should have box characters
        assert "\u2554" in output  # Top-left corner
        assert "\u255a" in output  # Bottom-left corner
        assert "\u2551" in output  # Vertical border

    def test_ascii_renderer_shows_progress(self):
        """Test output shows progress information."""
        config = Config(total=100)
        state = ProgressState(total=100)
        state.completed = 50

        renderer = ASCIIRenderer(config)
        output = renderer.render(state, config)

        assert "50" in output
        assert "100" in output

    def test_ascii_renderer_progress_bar(self):
        """Test output contains progress bar characters."""
        config = Config(total=100)
        state = ProgressState(total=100)
        state.completed = 50

        renderer = ASCIIRenderer(config)
        output = renderer.render(state, config)

        # Should have bar characters
        bar_chars = config.get_bar_chars()
        assert bar_chars.filled in output or bar_chars.empty in output


class TestASCIIRendererWidth:
    """Tests for width handling."""

    def test_fixed_width_60(self):
        """Test 60 character width option."""
        config = Config(total=10, inner_width=60)
        state = ProgressState(total=10)
        renderer = ASCIIRenderer(config)
        output = renderer.render(state, config)

        lines = output.split('\n')
        # All content lines should be width + 2 (for borders)
        for line in lines:
            if line.startswith('\u2551'):
                assert len(line) <= 64  # 60 + 2 borders + some tolerance

    def test_fixed_width_84(self):
        """Test 84 character width option."""
        config = Config(total=10, inner_width=84)
        state = ProgressState(total=10)
        renderer = ASCIIRenderer(config)
        output = renderer.render(state, config)

        lines = output.split('\n')
        for line in lines:
            if line.startswith('\u2551'):
                assert len(line) <= 88


class TestASCIIRendererSections:
    """Tests for different display sections."""

    def test_stage_analysis_shown(self):
        """Test stage analysis section is shown when enabled."""
        config = Config(total=10, show_stage_analysis=True)
        state = ProgressState(total=10)
        state.start_task("task1", stage="loading", worker_id=0)
        state.update_task("task1", stage="processing")
        state.finish_task("task1")

        renderer = ASCIIRenderer(config)
        output = renderer.render(state, config)

        # Should show stage analysis section
        assert "Stage" in output or "stage" in output.lower()

    def test_stage_analysis_hidden(self):
        """Test stage analysis section is hidden when disabled."""
        config = Config(total=10, show_stage_analysis=False)
        state = ProgressState(total=10)
        state.start_task("task1", stage="loading", worker_id=0)
        state.finish_task("task1")

        renderer = ASCIIRenderer(config)
        output = renderer.render(state, config)

        # Stage Analysis header should not appear
        assert "Stage Analysis" not in output

    def test_workers_shown(self):
        """Test active workers section is shown when enabled."""
        config = Config(total=10, show_workers=True)
        state = ProgressState(total=10)
        state.start_task("task1", stage="working", worker_id=0)

        renderer = ASCIIRenderer(config)
        output = renderer.render(state, config)

        assert "Worker" in output or "Active" in output

    def test_workers_hidden(self):
        """Test active workers section is hidden when disabled."""
        config = Config(total=10, show_workers=False)
        state = ProgressState(total=10)
        state.start_task("task1", stage="working", worker_id=0)

        renderer = ASCIIRenderer(config)
        output = renderer.render(state, config)

        # Active Workers header should not appear
        assert "Active Workers" not in output


class TestASCIIRendererGoldenSnapshots:
    """Golden snapshot tests for visual regression."""

    @pytest.mark.skip(reason="Generate golden files first")
    def test_empty_state_golden(self):
        """Test empty state matches golden snapshot."""
        config = Config(total=10, inner_width=68)
        state = ProgressState(total=10)
        renderer = ASCIIRenderer(config)
        output = renderer.render(state, config)

        # Uncomment to save new golden:
        # save_golden("empty_state.txt", output)

        expected = load_golden("empty_state.txt")
        assert output == expected

    @pytest.mark.skip(reason="Generate golden files first")
    def test_partial_progress_golden(self):
        """Test partial progress matches golden snapshot."""
        config = Config(total=100, inner_width=68, show_stage_analysis=False, show_workers=False)
        state = ProgressState(total=100)
        state.completed = 42

        renderer = ASCIIRenderer(config)
        output = renderer.render(state, config)

        # Uncomment to save new golden:
        # save_golden("partial_progress.txt", output)

        expected = load_golden("partial_progress.txt")
        assert output == expected


class TestRendererProtocol:
    """Tests for renderer protocol compliance."""

    def test_ascii_renderer_protocol(self):
        """Test ASCIIRenderer implements protocol."""
        config = Config(total=10)
        renderer = ASCIIRenderer(config)

        assert hasattr(renderer, 'render')
        assert hasattr(renderer, 'start')
        assert hasattr(renderer, 'close')

        renderer.start()
        renderer.close()


class TestRendererEdgeCases:
    """Tests for edge cases."""

    def test_zero_progress(self):
        """Test rendering with zero progress."""
        config = Config(total=100)
        state = ProgressState(total=100)
        state.completed = 0

        renderer = ASCIIRenderer(config)
        output = renderer.render(state, config)

        assert "0%" in output or "0/100" in output

    def test_full_progress(self):
        """Test rendering with full progress."""
        config = Config(total=100)
        state = ProgressState(total=100)
        state.completed = 100
        state.all_completed = True

        renderer = ASCIIRenderer(config)
        output = renderer.render(state, config)

        assert "100" in output

    def test_many_active_tasks(self):
        """Test rendering with many active tasks."""
        config = Config(total=100, max_active_rows=5)
        state = ProgressState(total=100)

        # Start 10 tasks
        for i in range(10):
            state.start_task(f"task{i}", stage="working", worker_id=i)

        renderer = ASCIIRenderer(config)
        output = renderer.render(state, config)

        # Should not crash, should show limited rows
        assert output is not None
