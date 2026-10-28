"""Enable ``python -m graphrag`` to invoke the command-line interface."""

from __future__ import annotations

from graphrag.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
