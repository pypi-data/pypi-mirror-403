"""
Development stub - imports from python/qrucible_easy.py

For installed packages, import directly: import qrucible_easy
For development, this stub enables: import qrucible_easy from repo root
"""
import sys
from pathlib import Path

# Add python/ to path if not already there
python_dir = Path(__file__).parent / "python"
if str(python_dir) not in sys.path:
    sys.path.insert(0, str(python_dir))

# Re-export everything from the actual module
# pylint: disable=wrong-import-position
from python.qrucible_easy import *  # noqa: F401, F403, E402
from python.qrucible_easy import __all__  # noqa: E402
