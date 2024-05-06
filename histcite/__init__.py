"""Welcome to use `histcite-python`. You can get detailed information about the package here."""

__version__ = "2.2.0"

from .compute_metrics import ComputeMetrics
from .network_graph import CitNetExplorer, GraphViz
from .process_file import BuildCitation, BuildRef
from .read_file import ReadFile

__all__ = [
    "ComputeMetrics",
    "CitNetExplorer",
    "GraphViz",
    "BuildRef",
    "BuildCitation",
    "ReadFile",
]

import platform
import sys
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
