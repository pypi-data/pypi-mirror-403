import pytest


def test_utils_namespace():
    """Ensure objects are not unintentionally exposed in utils namespace."""
    with pytest.raises(ImportError):
        from pygraphx.utils import nx
    with pytest.raises(ImportError):
        from pygraphx.utils import sys
    with pytest.raises(ImportError):
        from pygraphx.utils import defaultdict, deque
