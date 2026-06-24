"""Pytest configuration — mock heavy optional imports for unit tests."""
from __future__ import annotations

import sys
from unittest.mock import MagicMock


def _mock_heavy_deps() -> None:
    """Insert mock stubs for packages not available in the test environment.

    Only the pure math / parsing functions are tested; no actual model inference
    is performed, so mocking ultralytics and torch is safe.
    """
    # Core heavy deps
    for name in ['ultralytics', 'torch', 'torchvision', 'torchaudio',
                 'ultralytics.engine', 'ultralytics.models']:
        if name not in sys.modules:
            sys.modules[name] = MagicMock()

    # Make ultralytics.YOLO importable as a class
    yolo_mock = MagicMock()
    yolo_mock.__name__ = 'YOLO'
    sys.modules['ultralytics'].YOLO = yolo_mock


_mock_heavy_deps()
