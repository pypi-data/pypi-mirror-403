import pytest

from pycnp import read
from pycnp._pycnp import ProblemData


def test_read_adjacency_list(tmp_path):
    """
    Test reading adjacency list format.
    Format:
    NumNodes
    NodeID : Neighbor1 Neighbor2 ...
    """
    content = "3\n0 : 1 2\n1 : 0 2\n2 : 0 1"
    graph_file = tmp_path / "graph.adj"
    graph_file.write_text(content, encoding="utf-8")

    # Use absolute path to bypass relative path logic
    data = read(str(graph_file.resolve()))
    assert isinstance(data, ProblemData)


def test_read_edge_list(tmp_path):
    """
    Test reading edge list format.
    Format:
    p edge NumNodes NumEdges
    e Src Dst
    ...
    Indices must be 0-based < NumNodes
    """
    content = "p edge 3 3\ne 0 1\ne 1 2\ne 2 0"
    graph_file = tmp_path / "graph.txt"
    graph_file.write_text(content, encoding="utf-8")

    data = read(str(graph_file.resolve()))
    assert isinstance(data, ProblemData)


def test_file_not_found():
    """
    Test error handling for missing file.
    """
    # Use a clearly non-existent absolute path
    with pytest.raises(FileNotFoundError):
        read("/non/existent/file.txt")
