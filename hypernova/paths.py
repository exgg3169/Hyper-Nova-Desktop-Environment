"""Locates HyperNova's data files in a source checkout or an installation."""

import os

_HERE = os.path.dirname(os.path.abspath(__file__))
_CANDIDATES = [
    os.environ.get("HYPERNOVA_DATA_DIR", ""),
    os.path.join(_HERE, "..", "data"),
    "/usr/local/share/hypernova",
    "/usr/share/hypernova",
]


def data_dir():
    for candidate in _CANDIDATES:
        if candidate and os.path.isdir(os.path.join(candidate, "styles")):
            return os.path.abspath(candidate)
    raise FileNotFoundError("HyperNova data directory not found (set HYPERNOVA_DATA_DIR)")


def data_file(*parts):
    return os.path.join(data_dir(), *parts)
