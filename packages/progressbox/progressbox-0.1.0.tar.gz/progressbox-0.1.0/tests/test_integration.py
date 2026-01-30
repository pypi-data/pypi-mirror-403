"""Integration tests for end-to-end workflows."""
import pytest
import time
import threading
from progressbox import Progress, Config, create_default_config
from progressbox.render import get_renderer
from progressbox.render.string_ import StringRenderer
from progressbox.render.jupyter import JupyterRenderer


class TestEndToEndWorkflow:
    """End-to-end workflow tests."""

    def test_simple_workflow(self):
        """Test simple task processing workflow."""
        config = Config(total=10, disable_threading=True)

        with Progress(config) as progress:
            for i in range(10):
                progress.task_start(f"task_{i}", worker=i % 2)
                progress.task_finish(f"task_{i}")

        assert progress.state.completed == 10

    def test_staged_workflow(self):
        """Test workflow with stage transitions."""
        config = Config(total=5, disable_threading=True)

        with Progress(config) as progress:
            for i in range(5):
                progress.task_start(f"task_{i}", worker=0)
                progress.task_update(f"task_{i}", stage="loading")
                progress.task_update(f"task_{i}", stage="processing")
                progress.task_update(f"task_{i}", stage="saving")
                progress.task_finish(f"task_{i}")

        assert progress.state.completed == 5

    def test_mixed_cached_workflow(self):
        """Test workflow with mix of cached and non-cached tasks."""
        config = Config(total=10, disable_threading=True)

        with Progress(config) as progress:
            for i in range(10):
                cached = (i % 3 == 0)  # Every 3rd task is cached
                progress.task_start(f"task_{i}", worker=0, cached=cached)
                progress.task_finish(f"task_{i}")

        assert progress.state.completed == 10
        assert progress.state.cached_loads == 4  # Tasks 0, 3, 6, 9


class TestRendererIntegration:
    """Tests for renderer integration."""

    def test_string_renderer_workflow(self):
        """Test workflow with string renderer."""
        config = Config(total=5, renderer="string", disable_threading=True)

        with Progress(config) as progress:
            for i in range(5):
                progress.task_start(f"task_{i}", worker=0)
                progress.task_finish(f"task_{i}")

                # Force render
                progress.tick()

        assert progress.state.completed == 5

    def test_renderer_factory_string(self):
        """Test renderer factory creates string renderer."""
        config = Config(total=10, renderer="string")
        renderer = get_renderer(config, auto_detect=False)

        assert isinstance(renderer, StringRenderer)

    def test_renderer_factory_jupyter(self):
        """Test renderer factory creates jupyter renderer."""
        config = Config(total=10, renderer="jupyter")
        renderer = get_renderer(config, auto_detect=False)

        assert isinstance(renderer, JupyterRenderer)

    def test_renderer_output_contains_progress(self):
        """Test rendered output contains progress information."""
        config = Config(total=100, renderer="string")
        renderer = StringRenderer(config)

        from progressbox.state import ProgressState
        state = ProgressState(total=100)
        state.completed = 42

        output = renderer.render(state, config)

        assert "42" in output
        assert "100" in output


class TestCallbackIntegration:
    """Tests for callback integration."""

    def test_completion_callback_workflow(self):
        """Test completion callback in full workflow."""
        results = {}

        def on_complete(snapshot):
            results['completed'] = snapshot['completed']
            results['total'] = snapshot['total']

        config = Config(total=5, on_complete=on_complete, disable_threading=True)

        with Progress(config) as progress:
            for i in range(5):
                progress.task_start(f"task_{i}", worker=0)
                progress.task_finish(f"task_{i}")

        assert results['completed'] == 5
        assert results['total'] == 5

    def test_snapshot_contains_metrics(self):
        """Test snapshot includes metrics data."""
        results = {}

        def on_complete(snapshot):
            results['snapshot'] = snapshot

        config = Config(total=3, on_complete=on_complete, disable_threading=True)

        with Progress(config) as progress:
            for i in range(3):
                progress.task_start(f"task_{i}", worker=0)
                time.sleep(0.01)
                progress.task_finish(f"task_{i}")

        assert 'metrics' in results['snapshot']
        assert results['snapshot']['metrics']['completed_count'] == 3


class TestErrorHandling:
    """Tests for error handling in workflows."""

    def test_fail_safe_continues_on_error(self):
        """Test fail_safe mode continues despite errors."""
        config = Config(total=5, fail_safe=True, disable_threading=True)

        with Progress(config) as progress:
            # Start and finish some tasks normally
            progress.task_start("task_0", worker=0)
            progress.task_finish("task_0")

            # Try to finish a non-existent task (should not raise)
            progress.task_finish("nonexistent")

            # Continue with more tasks
            progress.task_start("task_1", worker=0)
            progress.task_finish("task_1")

        assert progress.state.completed == 2

    def test_strict_mode_raises(self):
        """Test strict mode raises on errors."""
        config = Config(total=5, fail_safe=False, disable_threading=True)

        with Progress(config) as progress:
            with pytest.raises(KeyError):
                progress.task_finish("nonexistent")


class TestConcurrentOperations:
    """Tests for concurrent task operations."""

    def test_concurrent_task_processing(self):
        """Test concurrent task processing from multiple threads."""
        config = Config(total=20, fail_safe=True, disable_threading=True)
        errors = []

        def worker(progress, worker_id, task_range):
            try:
                for i in task_range:
                    task_id = f"task_{i}"
                    progress.task_start(task_id, worker=worker_id)
                    time.sleep(0.001)
                    progress.task_finish(task_id)
            except Exception as e:
                errors.append(e)

        with Progress(config) as progress:
            threads = []
            # 4 workers, each processing 5 tasks
            for w in range(4):
                t = threading.Thread(
                    target=worker,
                    args=(progress, w, range(w * 5, (w + 1) * 5))
                )
                threads.append(t)
                t.start()

            for t in threads:
                t.join()

        assert len(errors) == 0
        assert progress.state.completed == 20


class TestConfigVariations:
    """Tests for different configuration variations."""

    def test_minimal_config(self):
        """Test with minimal configuration."""
        config = Config(total=5, disable_threading=True)

        with Progress(config) as progress:
            for i in range(5):
                progress.task_start(f"task_{i}")
                progress.task_finish(f"task_{i}")

        assert progress.state.completed == 5

    def test_custom_width_config(self):
        """Test with custom display width."""
        config = Config(total=5, inner_width=84, disable_threading=True)

        with Progress(config) as progress:
            progress.task_start("task_0")
            progress.tick()  # Force render
            progress.task_finish("task_0")

        assert progress.state.completed == 1

    def test_disabled_features_config(self):
        """Test with disabled display features."""
        config = Config(
            total=5,
            show_stage_analysis=False,
            show_workers=False,
            disable_threading=True
        )

        with Progress(config) as progress:
            for i in range(5):
                progress.task_start(f"task_{i}")
                progress.task_finish(f"task_{i}")

        assert progress.state.completed == 5


class TestHelperFunctions:
    """Tests for helper functions."""

    def test_create_default_config(self):
        """Test create_default_config helper."""
        config = create_default_config(total=100, n_workers=8)

        assert config.total == 100
        assert config.n_workers == 8
        assert config.inner_width == 'auto'

    def test_create_default_config_with_overrides(self):
        """Test create_default_config with custom overrides."""
        config = create_default_config(
            total=50,
            renderer="string",
            show_stage_analysis=False
        )

        assert config.total == 50
        assert config.renderer == "string"
        assert config.show_stage_analysis == False
