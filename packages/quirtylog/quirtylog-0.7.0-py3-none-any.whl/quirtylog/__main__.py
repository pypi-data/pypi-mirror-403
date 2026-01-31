"""
-----------
__main__.py
-----------

quirtylog main entry point

Example:

    .. code-block:: bash

    python -m quirtylog script.py

"""

from __future__ import annotations
import sys
import importlib
import importlib.util

from .core import configure_logger


def load_module(source: str):
    """
    Read file source and loads it as a module

    :param source: file to load
    :return: loaded module
    """

    spec = importlib.util.spec_from_file_location(source, source)

    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot find or load module from '{source}'")
    module = importlib.util.module_from_spec(spec)
    sys.modules[source] = module
    spec.loader.exec_module(module)

    return module


def wrapper(argv: list[str] | None = None):
    """Execute the script using default log"""
    if argv is None:
        argv = sys.argv[1:]

    if not argv:
        print("Usage: python -m quirtylog <script.py>")
        return 1

    configure_logger()
    script_name = argv[0]

    try:
        load_module(script_name)
    except Exception as e:
        print(f"Error loading script '{script_name}': {e}")
        return 1


sys.exit(wrapper())
