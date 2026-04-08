from __future__ import annotations

__all__ = ["app", "main"]


def __getattr__(name: str):
    if name == "app":
        from pkpd_xc7.cli.app import app as _app

        return _app
    if name == "main":
        from pkpd_xc7.cli.app import main as _main

        return _main
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
