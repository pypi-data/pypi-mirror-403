"""Compatibility utilities for cross-platform imports.

Handles conditional imports for Pyodide/WebAssembly environments where
server dependencies (websockets, aiohttp) are unavailable.
"""

import sys

# Detect Pyodide/Emscripten environment
IS_PYODIDE = sys.platform == "emscripten"


def try_import_server():
    """Attempt to import server components with informative error handling.

    Returns:
        tuple: (Vuer, VuerSession) if available, (None, None) otherwise.
    """
    try:
        from vuer.server import Vuer, VuerSession
        return Vuer, VuerSession
    except ImportError as e:
        if IS_PYODIDE:
            # Expected in Pyodide - silent
            pass
        else:
            # Unexpected on regular Python - provide guidance
            missing = _parse_missing_module(e)
            print(f"vuer: Server unavailable ({missing}). Use VuerClient for client-only mode.")
            print("      Install server deps: pip install websockets aiohttp aiohttp-cors")
        return None, None


def _parse_missing_module(error: ImportError) -> str:
    """Extract the missing module name from an ImportError."""
    if error.name:
        return error.name
    msg = str(error)
    if "No module named" in msg:
        return msg.split("No module named")[-1].strip().strip("'\"")
    return "missing dependency"
