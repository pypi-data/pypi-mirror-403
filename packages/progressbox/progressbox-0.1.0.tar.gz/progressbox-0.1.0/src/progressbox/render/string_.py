"""String renderer for testing and logging."""
from __future__ import annotations
from progressbox.state import ProgressState
from progressbox.config import Config
from progressbox.metrics import format_time


class StringRenderer:
    """Simple string renderer for testing and non-interactive output.

    Produces a compact, single-line or multi-line string representation
    suitable for logging, testing, or headless environments.
    """

    def __init__(self, config: Config):
        """Initialize with configuration.

        Args:
            config: Configuration object with display settings.
        """
        self.config = config

    def render(self, state: ProgressState, config: Config) -> str:
        """Render progress as a simple string.

        Args:
            state: Current progress state.
            config: Configuration object.

        Returns:
            String representation of current progress.
        """
        progress_ratio = state.get_completion_ratio()
        progress_pct = int(progress_ratio * 100)
        elapsed = state.get_elapsed_time()
        active_count = state.get_active_count()

        lines = [
            f"Progress: {state.completed}/{state.total} ({progress_pct}%)",
            f"Elapsed: {format_time(elapsed)} | Active: {active_count}",
        ]

        # Add cached info if any
        if state.cached_loads > 0:
            lines.append(f"Cached: {state.cached_loads}")

        # Add stage info if available
        stage_stats = state.get_stage_statistics()
        if stage_stats:
            stage_parts = []
            for stage, stats in sorted(stage_stats.items()):
                stage_parts.append(f"{stage}: {format_time(stats['mean'])}")
            lines.append(f"Stages: {', '.join(stage_parts)}")

        return "\n".join(lines)

    def start(self) -> None:
        """Initialize renderer (no-op for string renderer)."""
        pass

    def close(self) -> None:
        """Cleanup renderer (no-op for string renderer)."""
        pass
