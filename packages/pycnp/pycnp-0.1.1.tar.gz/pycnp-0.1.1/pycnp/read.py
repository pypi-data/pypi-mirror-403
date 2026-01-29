from __future__ import annotations

import inspect
import os

from ._pycnp import ProblemData


def read(graph_file: str) -> "ProblemData":
    """
    Read graph file and return a ProblemData object.

    Automatically detects graph file format (adjacency list or edge list)
    and reads data accordingly.

    Parameters
    ----------
    graph_file : str
        Path to graph file (adjacency list or edge list format).

    Returns
    -------
    ProblemData
        A ProblemData object containing the graph data.

    Raises
    ------
    RuntimeError
        When file cannot be opened or has invalid format.
    FileNotFoundError
        When file does not exist.
    """
    # Get directory of caller script
    caller_frame = inspect.stack()[1]
    caller_path = caller_frame.filename
    caller_dir = os.path.dirname(os.path.abspath(caller_path))

    # If file path is not absolute, prepend caller directory
    if not os.path.isabs(graph_file):
        graph_file = os.path.join(caller_dir, graph_file)

    if not os.path.exists(graph_file):
        raise FileNotFoundError(f"Graph file not found: {graph_file}")

    # Determine file format (adjacency list or edge list)
    with open(graph_file, "r", encoding="utf-8") as f:
        first_line = f.readline().strip()

        # Check if first line contains 'p', which is characteristic of edge list format
        if first_line.startswith("p") or "p" in first_line.split():
            # Edge list format
            problem_data = read_edge_list_format(graph_file)
        else:
            # Adjacency list format
            problem_data = read_adjacency_list_format(graph_file)

    return problem_data


def read_adjacency_list_format(filename: str) -> "ProblemData":
    """
    Read data from adjacency list format file.

    Adjacency list format: each line represents a node and its neighbors,
    formatted as "node_id neighbor1 neighbor2 ..."

    Parameters
    ----------
    filename : str
        Path to file.

    Returns
    -------
    ProblemData
        Initialized ProblemData object.

    Raises
    ------
    RuntimeError
        When file cannot be opened or has invalid format.
    """
    try:
        # Call C++ binding function to read adjacency list file
        return ProblemData.read_from_adjacency_list_file(filename)
    except Exception as e:
        raise RuntimeError(f"Failed to read adjacency list file: {e}")


def read_edge_list_format(filename: str) -> "ProblemData":
    """
    Read data from edge list format file.

    Edge list format: typically contains a header line "p edge num_nodes num_edges",
    followed by lines representing edges formatted as "e node1 node2"

    Parameters
    ----------
    filename : str
        Path to file.

    Returns
    -------
    ProblemData
        Initialized ProblemData object.

    Raises
    ------
    RuntimeError
        When file cannot be opened or has invalid format.
    """
    try:
        # Call C++ binding function to read edge list file
        return ProblemData.read_from_edge_list_format(filename)
    except Exception as e:
        raise RuntimeError(f"Failed to read edge list file: {e}")
