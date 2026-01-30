"""
pygraphx
========

pygraphx is a Python package for the creation, manipulation, and study of the
structure, dynamics, and functions of complex networks.

See https://networkx.org for complete documentation.
"""

__version__ = "1.0.0"


def __getattr__(name):
    """Remove functions and provide informative error messages."""
    if name == "nx_yaml":
        raise ImportError(
            "\nThe nx_yaml module has been removed from pygraphx.\n"
            "Please use the `yaml` package directly for working with yaml data.\n"
            "For example, a pygraphx.Graph `G` can be written to and loaded\n"
            "from a yaml file with:\n\n"
            "    import yaml\n\n"
            "    with open('path_to_yaml_file', 'w') as fh:\n"
            "        yaml.dump(G, fh)\n"
            "    with open('path_to_yaml_file', 'r') as fh:\n"
            "        G = yaml.load(fh, Loader=yaml.Loader)\n\n"
            "Note that yaml.Loader is considered insecure - see the pyyaml\n"
            "documentation for further details.\n\n"
        )
    if name == "read_yaml":
        raise ImportError(
            "\nread_yaml has been removed from pygraphx, please use `yaml`\n"
            "directly:\n\n"
            "    import yaml\n\n"
            "    with open('path', 'r') as fh:\n"
            "        yaml.load(fh, Loader=yaml.Loader)\n\n"
            "Note that yaml.Loader is considered insecure - see the pyyaml\n"
            "documentation for further details.\n\n"
        )
    if name == "write_yaml":
        raise ImportError(
            "\nwrite_yaml has been removed from pygraphx, please use `yaml`\n"
            "directly:\n\n"
            "    import yaml\n\n"
            "    with open('path_for_yaml_output', 'w') as fh:\n"
            "        yaml.dump(G_to_be_yaml, path_for_yaml_output, **kwds)\n\n"
        )
    raise AttributeError(f"module {__name__} has no attribute {name}")


# These are import orderwise
from pygraphx.exception import *

from pygraphx import utils

from pygraphx import classes
from pygraphx.classes import filters
from pygraphx.classes import *

from pygraphx import convert
from pygraphx.convert import *

from pygraphx import convert_matrix
from pygraphx.convert_matrix import *

from pygraphx import relabel
from pygraphx.relabel import *

from pygraphx import generators
from pygraphx.generators import *

from pygraphx import readwrite
from pygraphx.readwrite import *

# Need to test with SciPy, when available
from pygraphx import algorithms
from pygraphx.algorithms import *

from pygraphx import linalg
from pygraphx.linalg import *

from pygraphx.testing.test import run as test

from pygraphx import drawing
from pygraphx.drawing import *
