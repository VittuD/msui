# msui/__main__.py
"""
Allows:  python -m msui
Runs the chorus demo.
"""

from __future__ import annotations


def _resolve_entrypoint():
    """
    We expect msui.demos.chorus_demo to expose either:
      - main()
      - run()
      - demo_main()
    This keeps __main__.py stable even if you rename the function later.
    """
    try:
        from msui.demos import chorus_demo
    except Exception as e:  # noqa: BLE001
        raise SystemExit(
            "Could not import msui.demos.chorus_demo.\n"
            "Make sure you have:\n"
            "  msui/demos/__init__.py\n"
            "  msui/demos/chorus_demo.py\n"
            f"Import error: {e}"
        ) from e

    for name in ("main", "run", "demo_main"):
        fn = getattr(chorus_demo, name, None)
        if callable(fn):
            return fn

    raise SystemExit(
        "msui.demos.chorus_demo was imported, but no callable entrypoint was found.\n"
        "Expected one of: main(), run(), demo_main()."
    )


def main() -> None:
    entry = _resolve_entrypoint()
    entry()


if __name__ == "__main__":
    main()
