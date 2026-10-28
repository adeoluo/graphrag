"""Entrypoint: `python -m graphrag`."""

from __future__ import annotations

from graphrag import __version__
from graphrag.configuration import settings


def main() -> None:
    header = f"Graphrag v{__version__}"
    status = f"environment={settings.environment}, seed={settings.seed}"
    print(f"{header} - {status}")


if __name__ == "__main__":
    main()
