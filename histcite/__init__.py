"""
Welcome to use `histcite-python`. You can get detailed information about the package here.
"""

__version__ = "1.0.1"

from .compute_metrics import ComputeMetrics
from .network_graph import GraphViz
from .parse_reference import ParseReference
from .process_file import ProcessFile
from .read_file import ReadFile
from .recognize_reference import RecognizeReference

__all__ = [
    "ComputeMetrics",
    "GraphViz",
    "ParseReference",
    "ProcessFile",
    "ReadFile",
    "RecognizeReference",
]

import sys
import platform
from importlib.metadata import version


def show_versions():
    uname_result = platform.uname()
    info = {
        "python": ".".join([str(i) for i in sys.version_info]),
        "OS": uname_result.system + " " + uname_result.release,
        "pandas": version("pandas"),
        "pyarrow": version("pyarrow"),
    }
    for k, v in info.items():
        print(f"{k}: {v}")
