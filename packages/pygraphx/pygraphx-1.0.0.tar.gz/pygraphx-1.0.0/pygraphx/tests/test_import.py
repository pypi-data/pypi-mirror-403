import pytest


def test_namespace_alias():
    with pytest.raises(ImportError):
        from pygraphx import nx


def test_namespace_nesting():
    with pytest.raises(ImportError):
        from pygraphx.exception import NetworkX
