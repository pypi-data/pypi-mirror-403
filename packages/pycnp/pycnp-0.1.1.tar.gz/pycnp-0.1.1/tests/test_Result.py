import math

from pycnp.Result import Result


def test_result_init():
    """
    Test Result initialization and defaults.
    """
    res = Result()
    assert res.best_solution == set()
    assert res.best_obj_value == math.inf
    assert res.num_iterations == 0
    assert res.runtime == 0.0


def test_result_valid_values():
    """
    Test Result with valid values.
    """
    res = Result(
        best_solution={1, 2, 3}, best_obj_value=10.5, num_iterations=100, runtime=5.0
    )
    assert res.best_solution == {1, 2, 3}
    assert res.best_obj_value == 10.5
    assert res.num_iterations == 100
    assert res.runtime == 5.0


