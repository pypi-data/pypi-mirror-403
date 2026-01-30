"""Jupyter HTML renderer with styled progress display."""
from __future__ import annotations
from typing import List
from progressbox.state import ProgressState
from progressbox.config import Config
from progressbox.metrics import format_time


class JupyterRenderer:
    """HTML renderer optimized for Jupyter notebooks.

    Produces styled HTML output that displays well in Jupyter environments
    with proper monospace fonts and compact layout.
    """

    def __init__(self, config: Config):
        """Initialize with configuration.

        Args:
            config: Configuration object with display settings.
        """
        self.config = config
        self.bar_chars = config.get_bar_chars()

    def _get_styles(self) -> str:
        """Get CSS styles for the progress display."""
        return """
        <style>
            .progressbox-container {
                font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
                font-size: 12px;
                line-height: 1.2;
                background: #1e1e1e;
                color: #d4d4d4;
                padding: 10px;
                border-radius: 4px;
                max-width: 600px;
            }
            .progressbox-title {
                text-align: center;
                font-weight: bold;
                color: #569cd6;
                margin-bottom: 8px;
                padding-bottom: 4px;
                border-bottom: 1px solid #404040;
            }
            .progressbox-bar-container {
                background: #404040;
                border-radius: 2px;
                height: 20px;
                margin: 8px 0;
                overflow: hidden;
            }
            .progressbox-bar-fill {
                background: linear-gradient(90deg, #4ec9b0, #569cd6);
                height: 100%;
                transition: width 0.3s ease;
            }
            .progressbox-stats {
                display: grid;
                grid-template-columns: 1fr 1fr 1fr;
                gap: 4px;
                margin: 8px 0;
                padding: 4px 0;
                border-top: 1px solid #404040;
                border-bottom: 1px solid #404040;
            }
            .progressbox-stat {
                text-align: center;
            }
            .progressbox-stat-label {
                color: #808080;
                font-size: 10px;
            }
            .progressbox-stat-value {
                color: #d4d4d4;
            }
            .progressbox-section {
                margin-top: 8px;
                padding-top: 4px;
                border-top: 1px solid #404040;
            }
            .progressbox-section-title {
                color: #569cd6;
                font-size: 11px;
                margin-bottom: 4px;
            }
            .progressbox-stage-row {
                display: flex;
                justify-content: space-between;
                padding: 2px 0;
            }
            .progressbox-stage-name {
                color: #9cdcfe;
            }
            .progressbox-stage-time {
                color: #ce9178;
            }
            .progressbox-worker-row {
                display: flex;
                justify-content: space-between;
                padding: 2px 0;
            }
            .progressbox-worker-id {
                color: #4ec9b0;
            }
            .progressbox-worker-stage {
                color: #dcdcaa;
            }
            .progressbox-worker-time {
                color: #b5cea8;
            }
        </style>
        """

    def render(self, state: ProgressState, config: Config) -> str:
        """Render progress as styled HTML.

        Args:
            state: Current progress state.
            config: Configuration object.

        Returns:
            HTML string for Jupyter display.
        """
        progress_ratio = state.get_completion_ratio()
        progress_pct = int(progress_ratio * 100)
        elapsed = state.get_elapsed_time()
        active_count = state.get_active_count()
        remaining = state.get_remaining_count()

        parts: List[str] = []

        # Add styles
        parts.append(self._get_styles())

        # Container start
        parts.append('<div class="progressbox-container">')

        # Title
        parts.append('<div class="progressbox-title">Progress Monitoring</div>')

        # Progress bar
        parts.append(f'''
        <div style="text-align: center; margin-bottom: 4px;">
            {state.completed}/{state.total} ({progress_pct}%)
        </div>
        <div class="progressbox-bar-container">
            <div class="progressbox-bar-fill" style="width: {progress_pct}%;"></div>
        </div>
        ''')

        # Stats grid
        avg_time = state.get_average_completion_time()
        avg_str = format_time(avg_time) if avg_time else "N/A"

        parts.append(f'''
        <div class="progressbox-stats">
            <div class="progressbox-stat">
                <div class="progressbox-stat-label">Elapsed</div>
                <div class="progressbox-stat-value">{format_time(elapsed)}</div>
            </div>
            <div class="progressbox-stat">
                <div class="progressbox-stat-label">Avg/Task</div>
                <div class="progressbox-stat-value">{avg_str}</div>
            </div>
            <div class="progressbox-stat">
                <div class="progressbox-stat-label">Active</div>
                <div class="progressbox-stat-value">{active_count}</div>
            </div>
        </div>
        ''')

        # Cached info
        if state.cached_loads > 0:
            cache_pct = int((state.cached_loads / max(state.completed, 1)) * 100)
            parts.append(f'''
            <div style="text-align: center; color: #b5cea8;">
                Cached: {state.cached_loads} ({cache_pct}%)
            </div>
            ''')

        # Stage analysis
        if config.show_stage_analysis:
            stage_stats = state.get_stage_statistics()
            if stage_stats:
                parts.append('<div class="progressbox-section">')
                parts.append('<div class="progressbox-section-title">Stage Analysis</div>')
                for stage, stats in sorted(stage_stats.items()):
                    pct = int(stats['percentage'])
                    parts.append(f'''
                    <div class="progressbox-stage-row">
                        <span class="progressbox-stage-name">{stage}</span>
                        <span class="progressbox-stage-time">{format_time(stats['mean'])} ({pct}%)</span>
                    </div>
                    ''')
                parts.append('</div>')

        # Active workers
        if config.show_workers:
            active_tasks = state.get_active_tasks()
            if active_tasks:
                parts.append('<div class="progressbox-section">')
                parts.append('<div class="progressbox-section-title">Active Workers</div>')
                for task in active_tasks[:config.max_active_rows]:
                    duration = format_time(task.get_task_duration())
                    parts.append(f'''
                    <div class="progressbox-worker-row">
                        <span class="progressbox-worker-id">W{task.worker_id}</span>
                        <span class="progressbox-worker-stage">{task.stage}</span>
                        <span class="progressbox-worker-time">{duration}</span>
                    </div>
                    ''')
                if len(active_tasks) > config.max_active_rows:
                    remaining_workers = len(active_tasks) - config.max_active_rows
                    parts.append(f'<div style="color: #808080;">... and {remaining_workers} more</div>')
                parts.append('</div>')

        # Container end
        parts.append('</div>')

        return ''.join(parts)

    def start(self) -> None:
        """Initialize renderer (no-op for Jupyter renderer)."""
        pass

    def close(self) -> None:
        """Cleanup renderer (no-op for Jupyter renderer)."""
        pass
