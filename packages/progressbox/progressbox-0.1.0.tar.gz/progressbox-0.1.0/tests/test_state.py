"""Tests for state management."""
import pytest
import time
from progressbox.state import ProgressState, TaskInfo


class TestProgressStateInitialization:
    """Tests for ProgressState initialization."""

    def test_state_initialization(self):
        """Test state initializes correctly."""
        state = ProgressState(total=100)
        assert state.total == 100
        assert state.completed == 0
        assert state.cached_loads == 0
        assert len(state.active_tasks) == 0

    def test_state_rejects_zero_total(self):
        """Test state rejects zero total."""
        with pytest.raises(ValueError):
            ProgressState(total=0)

    def test_state_rejects_negative_total(self):
        """Test state rejects negative total."""
        with pytest.raises(ValueError):
            ProgressState(total=-5)


class TestTaskLifecycle:
    """Tests for task start/update/finish lifecycle."""

    def test_start_task(self):
        """Test starting a task."""
        state = ProgressState(total=10)
        worker_id = state.start_task("task1", stage="loading", worker_id=0)

        assert worker_id == 0
        assert "task1" in state.active_tasks
        assert state.active_tasks["task1"].stage == "loading"

    def test_start_task_auto_worker_id(self):
        """Test worker ID auto-assignment."""
        state = ProgressState(total=10)
        w1 = state.start_task("task1", stage="loading")
        w2 = state.start_task("task2", stage="loading")

        assert w1 == 0
        assert w2 == 1

    def test_start_task_duplicate_raises(self):
        """Test starting duplicate task raises error."""
        state = ProgressState(total=10)
        state.start_task("task1", stage="loading", worker_id=0)

        with pytest.raises(ValueError):
            state.start_task("task1", stage="loading", worker_id=1)

    def test_update_task_stage(self):
        """Test updating task stage."""
        state = ProgressState(total=10)
        state.start_task("task1", stage="loading", worker_id=0)
        state.update_task("task1", stage="processing")

        assert state.active_tasks["task1"].stage == "processing"

    def test_update_task_unknown_raises(self):
        """Test updating unknown task raises error."""
        state = ProgressState(total=10)

        with pytest.raises(KeyError):
            state.update_task("nonexistent", stage="processing")

    def test_finish_task(self):
        """Test finishing a task."""
        state = ProgressState(total=10)
        state.start_task("task1", stage="loading", worker_id=0)
        duration = state.finish_task("task1")

        assert state.completed == 1
        assert "task1" not in state.active_tasks
        assert duration >= 0

    def test_finish_task_unknown_raises(self):
        """Test finishing unknown task raises error."""
        state = ProgressState(total=10)

        with pytest.raises(KeyError):
            state.finish_task("nonexistent")

    def test_finish_cached_task(self):
        """Test finishing a cached task increments cache count."""
        state = ProgressState(total=10)
        state.start_task("task1", stage="loading", worker_id=0, cached=True)
        state.finish_task("task1")

        assert state.completed == 1
        assert state.cached_loads == 1


class TestProgressMetrics:
    """Tests for progress calculations."""

    def test_completion_ratio_empty(self):
        """Test completion ratio with no completed tasks."""
        state = ProgressState(total=10)
        assert state.get_completion_ratio() == 0.0

    def test_completion_ratio_partial(self):
        """Test completion ratio with some completed tasks."""
        state = ProgressState(total=10)
        state.completed = 5
        assert state.get_completion_ratio() == 0.5

    def test_completion_ratio_full(self):
        """Test completion ratio when all tasks complete."""
        state = ProgressState(total=10)
        state.completed = 10
        assert state.get_completion_ratio() == 1.0

    def test_active_count(self):
        """Test active task count."""
        state = ProgressState(total=10)
        state.start_task("task1", stage="loading", worker_id=0)
        state.start_task("task2", stage="loading", worker_id=1)

        assert state.get_active_count() == 2

    def test_remaining_count(self):
        """Test remaining task count."""
        state = ProgressState(total=10)
        state.completed = 3
        state.start_task("task1", stage="loading", worker_id=0)
        state.start_task("task2", stage="loading", worker_id=1)

        # Remaining = total - completed - active
        assert state.get_remaining_count() == 5

    def test_elapsed_time(self):
        """Test elapsed time calculation."""
        state = ProgressState(total=10)
        time.sleep(0.05)  # Small delay
        elapsed = state.get_elapsed_time()

        assert elapsed >= 0.05

    def test_average_completion_time_empty(self):
        """Test average completion time with no completed tasks."""
        state = ProgressState(total=10)
        assert state.get_average_completion_time() is None

    def test_average_completion_time(self):
        """Test average completion time calculation."""
        state = ProgressState(total=10)
        state.start_task("task1", stage="work", worker_id=0)
        time.sleep(0.02)
        state.finish_task("task1")

        avg = state.get_average_completion_time()
        assert avg is not None
        assert avg >= 0.02


class TestStageStatistics:
    """Tests for stage timing statistics."""

    def test_stage_statistics_empty(self):
        """Test stage stats with no completed stages."""
        state = ProgressState(total=10)
        stats = state.get_stage_statistics()
        assert stats == {}

    def test_stage_statistics_with_data(self):
        """Test stage stats after completing a task with stages."""
        state = ProgressState(total=10)
        state.start_task("task1", stage="loading", worker_id=0)
        time.sleep(0.01)
        state.update_task("task1", stage="processing")
        time.sleep(0.01)
        state.finish_task("task1")

        stats = state.get_stage_statistics()
        # Should have at least the processing stage recorded
        assert len(stats) >= 1


class TestActiveTasksList:
    """Tests for getting active tasks."""

    def test_get_active_tasks_empty(self):
        """Test getting active tasks when none exist."""
        state = ProgressState(total=10)
        tasks = state.get_active_tasks()
        assert tasks == []

    def test_get_active_tasks_returns_list(self):
        """Test that active tasks returns a list of TaskInfo."""
        state = ProgressState(total=10)
        state.start_task("task1", stage="loading", worker_id=0)

        tasks = state.get_active_tasks()
        assert len(tasks) == 1
        assert isinstance(tasks[0], TaskInfo)

    def test_get_active_tasks_returns_copies(self):
        """Test that active tasks returns copies, not references."""
        state = ProgressState(total=10)
        state.start_task("task1", stage="loading", worker_id=0)

        tasks = state.get_active_tasks()
        tasks[0].stage = "modified"

        # Original should be unchanged
        assert state.active_tasks["task1"].stage == "loading"


class TestTaskInfo:
    """Tests for TaskInfo class."""

    def test_task_info_duration(self):
        """Test task duration calculation."""
        task = TaskInfo(
            task_id="test",
            worker_id=0,
            stage="working",
            start_time=time.time() - 1.0,  # Started 1 second ago
            stage_start=time.time() - 0.5
        )

        assert task.get_task_duration() >= 1.0
        assert task.get_stage_duration() >= 0.5

    def test_task_info_transition_stage(self):
        """Test stage transition."""
        task = TaskInfo(
            task_id="test",
            worker_id=0,
            stage="loading",
            start_time=time.time(),
            stage_start=time.time()
        )

        time.sleep(0.01)
        duration = task.transition_stage("processing")

        assert task.stage == "processing"
        assert duration >= 0.01


class TestThreadSafety:
    """Tests for thread-safe operations."""

    def test_concurrent_start_finish(self):
        """Test concurrent task operations don't corrupt state."""
        import threading

        state = ProgressState(total=100)
        errors = []

        def worker(worker_id):
            try:
                for i in range(10):
                    task_id = f"w{worker_id}_t{i}"
                    state.start_task(task_id, stage="work", worker_id=worker_id * 100 + i)
                    state.finish_task(task_id)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
        assert state.completed == 50


class TestSnapshot:
    """Tests for state snapshot functionality."""

    def test_create_snapshot(self):
        """Test creating a state snapshot."""
        state = ProgressState(total=10)
        state.start_task("task1", stage="loading", worker_id=0)
        state.finish_task("task1")

        snapshot = state.create_snapshot()

        assert 'total' in snapshot
        assert 'completed' in snapshot
        assert snapshot['total'] == 10
        assert snapshot['completed'] == 1
