"""Tests for metrics calculations."""
import pytest
from progressbox.metrics import WelfordAccumulator, EWMA, MetricsEngine, format_time


class TestWelfordAccumulator:
    """Tests for Welford online statistics algorithm."""

    def test_empty_accumulator(self):
        """Test empty accumulator returns zero."""
        acc = WelfordAccumulator()
        assert acc.n == 0
        assert acc.mean == 0.0
        assert acc.variance == 0.0
        assert acc.std == 0.0

    def test_single_value(self):
        """Test accumulator with single value."""
        acc = WelfordAccumulator()
        acc.update(5.0)

        assert acc.n == 1
        assert acc.mean == 5.0
        assert acc.variance == 0.0

    def test_multiple_values(self):
        """Test accumulator with multiple values."""
        acc = WelfordAccumulator()
        values = [2.0, 4.0, 4.0, 4.0, 5.0, 5.0, 7.0, 9.0]
        for v in values:
            acc.update(v)

        assert acc.n == 8
        assert abs(acc.mean - 5.0) < 0.01  # Mean should be 5.0
        assert acc.std > 0  # Should have some variance

    def test_known_statistics(self):
        """Test with values that have known statistics."""
        acc = WelfordAccumulator()
        # Values: 1, 2, 3 -> mean=2
        for v in [1.0, 2.0, 3.0]:
            acc.update(v)

        assert acc.n == 3
        assert abs(acc.mean - 2.0) < 0.01

    def test_min_max_tracking(self):
        """Test min/max value tracking."""
        acc = WelfordAccumulator()
        for v in [5.0, 2.0, 8.0, 1.0, 9.0]:
            acc.update(v)

        assert acc.min_val == 1.0
        assert acc.max_val == 9.0

    def test_reset(self):
        """Test accumulator reset."""
        acc = WelfordAccumulator()
        acc.update(5.0)
        acc.update(10.0)
        acc.reset()

        assert acc.n == 0
        assert acc.mean == 0.0


class TestEWMA:
    """Tests for exponentially weighted moving average."""

    def test_ewma_initial(self):
        """Test EWMA with initial value."""
        ewma = EWMA(alpha=0.5)
        result = ewma.update(10.0)

        assert result == 10.0  # First value is returned as-is

    def test_ewma_smoothing(self):
        """Test EWMA smooths values."""
        ewma = EWMA(alpha=0.5)
        ewma.update(10.0)
        result = ewma.update(20.0)

        # With alpha=0.5: 0.5*20 + 0.5*10 = 15
        assert abs(result - 15.0) < 0.01

    def test_ewma_tracks_trend(self):
        """Test EWMA tracks upward trend."""
        ewma = EWMA(alpha=0.3)

        # Feed increasing values
        for v in [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]:
            result = ewma.update(float(v))

        # Should be tracking upward, but lagging
        assert result > 5  # Above midpoint
        assert result < 10  # But below max due to smoothing

    def test_ewma_invalid_alpha(self):
        """Test EWMA rejects invalid alpha."""
        with pytest.raises(ValueError):
            EWMA(alpha=0.0)

        with pytest.raises(ValueError):
            EWMA(alpha=1.5)

    def test_ewma_reset(self):
        """Test EWMA reset."""
        ewma = EWMA(alpha=0.5)
        ewma.update(10.0)
        ewma.update(20.0)
        ewma.reset()

        assert ewma.value is None
        assert ewma.n == 0


class TestMetricsEngine:
    """Tests for the metrics engine."""

    def test_engine_initialization(self):
        """Test engine initializes correctly."""
        engine = MetricsEngine()
        assert engine is not None
        assert engine.completed_count == 0

    def test_record_task_completion(self):
        """Test recording task completions."""
        engine = MetricsEngine()
        engine.record_task_completion(1.5, cached=False)
        engine.record_task_completion(2.0, cached=False)

        stats = engine.get_overall_stats()
        assert stats['completed_count'] == 2

    def test_record_cached_task(self):
        """Test recording cached task completions."""
        engine = MetricsEngine()
        engine.record_task_completion(0.5, cached=True)
        engine.record_task_completion(1.0, cached=False)

        stats = engine.get_overall_stats()
        assert stats['completed_count'] == 2
        assert stats['cached_count'] == 1

    def test_record_stage_time(self):
        """Test recording stage timing."""
        engine = MetricsEngine()
        engine.record_stage_time("loading", 0.5, cached=False)
        engine.record_stage_time("loading", 0.6, cached=False)
        engine.record_stage_time("processing", 2.0, cached=False)

        stage_stats = engine.get_stage_summary()
        assert "loading" in stage_stats
        assert "processing" in stage_stats

    def test_calculate_eta(self):
        """Test ETA calculation."""
        engine = MetricsEngine()

        # Record some completions to establish rate
        for _ in range(5):
            engine.record_task_completion(1.0, cached=False)

        eta = engine.calculate_eta(remaining=10)
        # Should estimate ~10 seconds (10 tasks * ~1s each)
        assert eta is None or eta > 0

    def test_engine_reset(self):
        """Test engine reset."""
        engine = MetricsEngine()
        engine.record_task_completion(1.0, cached=False)
        engine.reset()

        stats = engine.get_overall_stats()
        assert stats['completed_count'] == 0


class TestFormatTime:
    """Tests for time formatting utility."""

    def test_format_seconds(self):
        """Test formatting seconds."""
        result = format_time(45.0)
        assert "s" in result

    def test_format_minutes(self):
        """Test formatting minutes."""
        result = format_time(125.0)
        assert "m" in result or "min" in result.lower() or "2" in result

    def test_format_hours(self):
        """Test formatting hours."""
        result = format_time(3700.0)
        assert "h" in result or "hour" in result.lower() or "1" in result

    def test_format_zero(self):
        """Test formatting zero time."""
        result = format_time(0.0)
        assert "0" in result

    def test_format_small_time(self):
        """Test formatting sub-second time."""
        result = format_time(0.5)
        assert result is not None
        assert len(result) > 0

    def test_format_negative_time(self):
        """Test formatting negative time returns zero."""
        result = format_time(-5.0)
        assert "0" in result


class TestStageStatistics:
    """Tests for stage statistics from engine."""

    def test_stage_summary_empty(self):
        """Test empty stage summary."""
        engine = MetricsEngine()
        summary = engine.get_stage_summary()
        assert summary == {}

    def test_stage_summary_with_data(self):
        """Test stage summary with recorded data."""
        engine = MetricsEngine()
        engine.record_stage_time("loading", 0.5, cached=False)
        engine.record_stage_time("loading", 0.7, cached=False)
        engine.record_stage_time("processing", 2.0, cached=False)

        summary = engine.get_stage_summary()

        assert "loading" in summary
        assert summary["loading"]["count"] == 2
        assert abs(summary["loading"]["mean"] - 0.6) < 0.01

        assert "processing" in summary
        assert summary["processing"]["count"] == 1
