"""Tests for core Progress class."""
import pytest
import time
import threading
from progressbox.core import Progress
from progressbox.config import Config


class TestProgressInitialization:
    """Tests for Progress initialization."""

    def test_progress_initialization(self):
        """Test Progress initializes correctly."""
        config = Config(total=100, disable_threading=True)
        progress = Progress(config)

        assert progress.config.total == 100
        assert progress.state.total == 100

    def test_progress_context_manager(self):
        """Test Progress works as context manager."""
        config = Config(total=10, disable_threading=True)

        with Progress(config) as progress:
            assert progress._is_started

        assert progress._is_closed


class TestProgressTaskAPI:
    """Tests for task tracking API."""

    def test_task_start(self):
        """Test starting a task."""
        config = Config(total=10, disable_threading=True)

        with Progress(config) as progress:
            progress.task_start("task1", worker=0)
            assert "task1" in progress.state.active_tasks

    def test_task_update(self):
        """Test updating a task."""
        config = Config(total=10, disable_threading=True)

        with Progress(config) as progress:
            progress.task_start("task1", worker=0)
            progress.task_update("task1", stage="processing")

            task = progress.state.active_tasks["task1"]
            assert task.stage == "processing"

    def test_task_finish(self):
        """Test finishing a task."""
        config = Config(total=10, disable_threading=True)

        with Progress(config) as progress:
            progress.task_start("task1", worker=0)
            progress.task_finish("task1")

            assert "task1" not in progress.state.active_tasks
            assert progress.state.completed == 1

    def test_full_task_lifecycle(self):
        """Test complete task lifecycle."""
        config = Config(total=5, disable_threading=True)

        with Progress(config) as progress:
            for i in range(5):
                progress.task_start(f"task{i}", worker=i % 2)
                progress.task_update(f"task{i}", stage="working")
                progress.task_finish(f"task{i}")

            assert progress.state.completed == 5


class TestProgressRichAPI:
    """Tests for rich API aliases."""

    def test_stage_transition(self):
        """Test stage_transition alias."""
        config = Config(total=10, disable_threading=True)

        with Progress(config) as progress:
            progress.task_start("task1", worker=0)
            progress.stage_transition("task1", "processing")

            assert progress.state.active_tasks["task1"].stage == "processing"

    def test_stage_progress(self):
        """Test stage_progress alias."""
        config = Config(total=10, disable_threading=True)

        with Progress(config) as progress:
            progress.task_start("task1", worker=0)
            progress.stage_progress("task1", 0.5)
            # Should not raise

    def test_task_complete(self):
        """Test task_complete alias."""
        config = Config(total=10, disable_threading=True)

        with Progress(config) as progress:
            progress.task_start("task1", worker=0)
            progress.task_complete("task1")

            assert progress.state.completed == 1


class TestProgressFailSafe:
    """Tests for fail-safe error handling."""

    def test_fail_safe_update_unknown_task(self):
        """Test fail_safe mode handles unknown task update."""
        config = Config(total=10, fail_safe=True, disable_threading=True)

        with Progress(config) as progress:
            # Should not raise in fail_safe mode
            progress.task_update("nonexistent", stage="test")

    def test_fail_safe_finish_unknown_task(self):
        """Test fail_safe mode handles unknown task finish."""
        config = Config(total=10, fail_safe=True, disable_threading=True)

        with Progress(config) as progress:
            # Should not raise in fail_safe mode
            progress.task_finish("nonexistent")

    def test_strict_mode_raises(self):
        """Test strict mode raises on errors."""
        config = Config(total=10, fail_safe=False, disable_threading=True)

        with Progress(config) as progress:
            with pytest.raises(KeyError):
                progress.task_finish("nonexistent")

    def test_operations_after_close_are_safe(self):
        """Test operations after close don't crash."""
        config = Config(total=10, fail_safe=True, disable_threading=True)

        progress = Progress(config)
        progress.start()
        progress.close()

        # These should not raise - they should be no-ops after close
        progress.task_start("task1", worker=0)
        progress.task_update("task1", stage="test")
        progress.task_finish("task1")


class TestProgressCallbacks:
    """Tests for callbacks."""

    def test_on_complete_callback(self):
        """Test completion callback is called."""
        callback_data = {}

        def on_complete(snapshot):
            callback_data['called'] = True
            callback_data['snapshot'] = snapshot

        config = Config(total=2, on_complete=on_complete, disable_threading=True)

        with Progress(config) as progress:
            progress.task_start("task1", worker=0)
            progress.task_finish("task1")
            progress.task_start("task2", worker=0)
            progress.task_finish("task2")

        assert callback_data.get('called', False)
        assert 'snapshot' in callback_data

    def test_on_complete_receives_metrics(self):
        """Test completion callback receives metrics."""
        callback_data = {}

        def on_complete(snapshot):
            callback_data['snapshot'] = snapshot

        config = Config(total=1, on_complete=on_complete, disable_threading=True)

        with Progress(config) as progress:
            progress.task_start("task1", worker=0)
            progress.task_finish("task1")

        # Should have metrics in snapshot
        assert 'metrics' in callback_data.get('snapshot', {})


class TestProgressCachedTasks:
    """Tests for cached task handling."""

    def test_cached_task_tracking(self):
        """Test cached tasks are tracked correctly."""
        config = Config(total=10, disable_threading=True)

        with Progress(config) as progress:
            progress.task_start("task1", worker=0, cached=True)
            progress.task_finish("task1")
            progress.task_start("task2", worker=0, cached=False)
            progress.task_finish("task2")

            assert progress.state.cached_loads == 1
            assert progress.state.completed == 2


class TestProgressControlMethods:
    """Tests for control methods."""

    def test_start_stop_start(self):
        """Test start/stop/start sequence."""
        config = Config(total=10, disable_threading=True)

        progress = Progress(config)
        progress.start()
        assert progress._is_started

        progress.stop()
        assert not progress._is_started

        progress.start()
        assert progress._is_started

        progress.close()

    def test_multiple_close_calls_safe(self):
        """Test multiple close calls are safe."""
        config = Config(total=10, disable_threading=True)

        progress = Progress(config)
        progress.start()
        progress.close()
        progress.close()  # Second close should be no-op
        progress.close()  # Third close should be no-op

    def test_tick_forces_render(self):
        """Test tick forces a render."""
        config = Config(total=10, disable_threading=True)

        with Progress(config) as progress:
            progress.task_start("task1", worker=0)
            progress.tick()  # Should not raise


class TestProgressMetricsIntegration:
    """Tests for metrics integration."""

    def test_metrics_track_completion_time(self):
        """Test metrics track task completion times."""
        config = Config(total=5, disable_threading=True)

        with Progress(config) as progress:
            for i in range(5):
                progress.task_start(f"task{i}", worker=0)
                time.sleep(0.01)  # Small delay
                progress.task_finish(f"task{i}")

            # Metrics should have recorded completions
            stats = progress.metrics.get_overall_stats()
            assert stats['completed_count'] == 5


class TestProgressWithMeta:
    """Tests for task metadata."""

    def test_task_with_metadata(self):
        """Test tasks can have metadata."""
        config = Config(total=10, disable_threading=True)

        with Progress(config) as progress:
            progress.task_start("task1", worker=0, meta={"filename": "test.txt"})

            task = progress.state.active_tasks["task1"]
            assert task.meta is not None
            assert task.meta.get("filename") == "test.txt"
