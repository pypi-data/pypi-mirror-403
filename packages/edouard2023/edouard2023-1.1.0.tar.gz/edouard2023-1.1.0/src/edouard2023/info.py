"""
File that regroup all access points visible from the outside world.
"""
from pathlib import Path

__all__ = ["pth_clean"]

pth_clean = Path(__file__).parent / "clean"

if Path(__file__).parent.parent.name == "src":  # provided for convenience only when installed in editable
    __all__.append("pth_raw")
    pth_raw = Path(__file__).parent.parent.parent / "raw"
