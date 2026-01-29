from pycnp import Model
from pycnp._pycnp import ProblemData


def test_model_init():
    """
    Tests that a Model can be initialized and is empty.
    """
    model = Model()
    assert len(model.nodes) == 0
    assert model.adj_list == []


def test_add_node():
    """
    Tests adding nodes.
    """
    model = Model()
    model.add_node(1)
    assert len(model.nodes) == 1
    assert 1 in model.nodes

    # Add same node again (should not increase count)
    model.add_node(1)
    assert len(model.nodes) == 1

    # Add another node
    model.add_node(2)
    assert len(model.nodes) == 2


def test_add_edge():
    """
    Tests adding edges.
    """
    model = Model()
    # Add edge between new nodes
    model.add_edge(1, 2)
    assert len(model.nodes) == 2
    assert 1 in model.nodes and 2 in model.nodes

    # Check edge was added (undirected)
    assert 2 in model.adj_list[1]
    assert 1 in model.adj_list[2]

    # Add edge to existing nodes
    model.add_edge(2, 3)
    assert 3 in model.nodes
    assert 2 in model.adj_list[3]

    # Add duplicate edge (should not increase count if set is used)
    model.add_edge(1, 2)
    # Still just 2 in each neighbor list
    assert len(model.adj_list[1]) == 1


def test_from_data_structure():
    """
    Tests that creating a model from ProblemData works as expected.
    """
    # Create a model and populate it
    model = Model()
    model.add_edge(0, 1)

    # Create ProblemData using the public property
    data = model.problem_data
    assert isinstance(data, ProblemData)

    # Create new model from data
    new_model = Model.from_data(data)

    # The new model should hold the reference
    assert new_model.problem_data is data
