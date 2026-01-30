"""Rendering backends for ProgressBox."""
from __future__ import annotations
from typing import TYPE_CHECKING, Literal
import logging

from progressbox.render.base import Renderer
from progressbox.render.ascii import ASCIIRenderer

if TYPE_CHECKING:
    from progressbox.config import Config

logger = logging.getLogger(__name__)

__all__ = ["Renderer", "ASCIIRenderer", "get_renderer"]


RendererType = Literal["ascii", "rich", "jupyter", "string"]


def get_renderer(config: "Config", *, auto_detect: bool = True) -> Renderer:
    """Get appropriate renderer based on config and environment.

    Args:
        config: Configuration object with renderer preference.
        auto_detect: If True, may override config.renderer based on environment.

    Returns:
        Configured renderer instance.

    The factory supports the following renderer types:
    - "ascii": Terminal renderer with Unicode box drawing (default)
    - "string": Simple string renderer for testing/logging
    - "jupyter": HTML renderer for Jupyter notebooks
    - "rich": Rich library renderer (falls back to ascii if not installed)

    Auto-detection behavior (when auto_detect=True):
    - In Jupyter notebooks: Uses jupyter renderer
    - In headless/non-TTY: Uses string renderer
    - Otherwise: Uses config.renderer setting
    """
    renderer_type = config.renderer

    # Auto-detect environment if enabled
    if auto_detect:
        renderer_type = _detect_best_renderer(config)

    # Create renderer based on type
    return _create_renderer(renderer_type, config)


def _detect_best_renderer(config: "Config") -> RendererType:
    """Detect the best renderer for current environment.

    Args:
        config: Configuration object.

    Returns:
        Recommended renderer type string.
    """
    from progressbox.utils.terminal import is_jupyter, is_tty

    # Check for Jupyter first
    if is_jupyter():
        logger.debug("Jupyter environment detected, using jupyter renderer")
        return "jupyter"

    # Check for non-TTY (headless) environment
    if not is_tty() and config.headless_ok:
        logger.debug("Headless environment detected, using string renderer")
        return "string"

    # Use configured renderer
    return config.renderer


def _create_renderer(renderer_type: RendererType, config: "Config") -> Renderer:
    """Create a renderer instance of the specified type.

    Args:
        renderer_type: Type of renderer to create.
        config: Configuration object.

    Returns:
        Configured renderer instance.

    Raises:
        ValueError: If renderer_type is not recognized.
    """
    if renderer_type == "ascii":
        return ASCIIRenderer(config)

    elif renderer_type == "string":
        from progressbox.render.string_ import StringRenderer
        return StringRenderer(config)

    elif renderer_type == "jupyter":
        from progressbox.render.jupyter import JupyterRenderer
        return JupyterRenderer(config)

    elif renderer_type == "rich":
        # Try to use rich, fall back to ASCII if not available
        try:
            from progressbox.render.rich_ import RichRenderer
            return RichRenderer(config)
        except ImportError:
            logger.warning("Rich library not installed, falling back to ASCII renderer")
            return ASCIIRenderer(config)

    else:
        raise ValueError(f"Unknown renderer type: {renderer_type}")
