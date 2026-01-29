"""Testing mode and display utilities for teaching practicals.

This module provides utilities for running notebooks in test mode (reduced datasets,
faster training) and displaying matplotlib plots in terminal environments.

Usage in notebooks:
    from master_mind.teaching.utils import *

Environment Variables:
    TESTING_MODE: Controls test mode behavior
        - "off" (default): Full dataset, normal training, plots displayed
        - "on": Reduced dataset, faster training, plots displayed
        - "full": Reduced dataset, faster training, plots disabled (Agg backend)
"""

import io
import os
import sys

# Parse testing mode from environment
test_mode_value = os.environ.get("TESTING_MODE", "off").lower()
test_mode = test_mode_value in ["on", "full"]
skip_plots = test_mode_value == "full"

if test_mode:
    print(f"#># Testing mode: {test_mode_value}", file=sys.stderr)

# Disable matplotlib GUI when in full test mode
if skip_plots:
    import matplotlib

    matplotlib.use("Agg")  # Non-interactive backend


def print_header(title: str):
    """Print a section header.

    In Python script mode, prints a formatted header with separators.
    In notebook mode, this call is converted to a markdown header by jupytext-filter.

    Args:
        title: The section title to display
    """
    print("=" * 80)
    print(title)
    print("=" * 80)


def is_notebook() -> bool:
    """Check if running in a Jupyter notebook.

    Returns:
        True if running in a Jupyter notebook (ZMQInteractiveShell), False otherwise.
    """
    try:
        from IPython import get_ipython

        shell = get_ipython()
        if shell is None:
            return False
        return shell.__class__.__name__ == "ZMQInteractiveShell"
    except (ImportError, AttributeError):
        return False


def _display_image_terminal(img, title: str = None):
    """Display a single image in terminal using imgcat or similar.

    Args:
        img: PIL Image or similar image object
        title: Optional title to print before the image
    """
    if title:
        print(f"\n{title}")

    # Try imgcat (works in iTerm2, VSCode, Kitty, etc.)
    try:
        import imgcat

        imgcat.imgcat(img)
        return
    except ImportError:
        pass

    # Fallback: print path info
    if hasattr(img, "filename") and img.filename:
        print(f"  [Image: {img.filename}]")
    else:
        print("  [Image displayed - install 'imgcat' for terminal preview]")


def _patch_matplotlib():
    """Patch matplotlib.pyplot.show() for terminal image display.

    When running outside a notebook, this patches plt.show() to render
    figures as images and display them via imgcat (if available).
    """
    import matplotlib.pyplot as plt

    _original_show = plt.show

    def _patched_show(*args, **kwargs):
        """Show plot in terminal by rendering figure to image."""
        fig = plt.gcf()

        # Check if figure has any content
        if fig.axes:
            # Render figure to PNG in memory
            buf = io.BytesIO()
            fig.savefig(buf, format="png", bbox_inches="tight", dpi=100)
            buf.seek(0)

            # Display via imgcat
            try:
                import imgcat
                from PIL import Image

                img = Image.open(buf)
                imgcat.imgcat(img)
                plt.close("all")
                return  # Don't open GUI window when imgcat works
            except ImportError:
                print("[Plot rendered - install 'imgcat' for terminal preview]")

        # Fallback: call original show (or close if skip_plots)
        if not skip_plots:
            _original_show(*args, **kwargs)
        else:
            plt.close("all")

    plt.show = _patched_show


# Patch matplotlib for terminal display when not in notebook
# This allows viewing plots in terminals that support inline images
if not is_notebook():
    _patch_matplotlib()
