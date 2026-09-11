"""Compatibility entry point. Prefer: python -m rocket_workbench --help"""

from rocket_workbench.cli import main


if __name__ == "__main__":
    raise SystemExit(main())
