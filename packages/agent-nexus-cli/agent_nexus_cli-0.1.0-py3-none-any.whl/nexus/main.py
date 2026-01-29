"""Nexus Main Entry Point.

Nexus is a CLI-based AI coding agent powered by LangChain and LangGraph.
"""

import warnings

warnings.filterwarnings(
    "ignore",
    message="Core Pydantic V1 functionality isn't compatible with Python 3.14 or greater",
    category=UserWarning,
)

from nexus.ui.cli import cli  # noqa: E402


def run() -> None:
    """Run Nexus.

    Main entry point for Nexus CLI.

    Args:
        None

    Returns:
        None

    Raises:
        None
    """

    cli()


if __name__ == "__main__":
    run()
