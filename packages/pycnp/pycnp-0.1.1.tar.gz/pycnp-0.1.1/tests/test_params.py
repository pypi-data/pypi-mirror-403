
from pycnp.params import MemeticSearchParams, VariablePopulationParams


class TestMemeticSearchParams:
    """Tests for MemeticSearchParams dataclass."""

    def test_default_values(self):
        """Test that default values are set correctly."""
        params = MemeticSearchParams()
        assert params.search == "CHNS"
        assert params.crossover is None
        assert params.is_problem_reduction is True
        assert params.is_pop_variable is True
        assert params.initial_pop_size == 5
        assert params.reduce_params == {"search": "CHNS", "beta": 0.9}

    def test_custom_search(self):
        """Test setting custom search strategy."""
        params = MemeticSearchParams(search="BCLS")
        assert params.search == "BCLS"

    def test_custom_crossover(self):
        """Test setting custom crossover operator."""
        params = MemeticSearchParams(crossover="DBX")
        assert params.crossover == "DBX"

    def test_disable_problem_reduction(self):
        """Test disabling problem reduction."""
        params = MemeticSearchParams(is_problem_reduction=False)
        assert params.is_problem_reduction is False

    def test_custom_pop_size(self):
        """Test setting custom initial population size."""
        params = MemeticSearchParams(initial_pop_size=10)
        assert params.initial_pop_size == 10

    def test_custom_reduce_params(self):
        """Test setting custom reduce parameters."""
        params = MemeticSearchParams(reduce_params={"search": "BCLS", "beta": 0.8})
        assert params.reduce_params["search"] == "BCLS"
        assert params.reduce_params["beta"] == 0.8

    def test_reduce_params_independence(self):
        """Test that default reduce_params are independent copies."""
        params1 = MemeticSearchParams()
        params2 = MemeticSearchParams()
        # Modifying one should not affect the other
        params1.reduce_params["beta"] = 0.5
        assert params2.reduce_params["beta"] == 0.9

    def test_integer_search_strategy(self):
        """Test that integer search strategy is accepted."""
        # Integer constants are used internally
        params = MemeticSearchParams(search=1)  # type: ignore
        assert params.search == 1

    def test_full_custom_config(self):
        """Test creating params with all custom values."""
        params = MemeticSearchParams(
            search="DLAS",
            crossover="IRR",
            is_problem_reduction=False,
            is_pop_variable=False,
            initial_pop_size=8,
            reduce_params={"search": "CHNS", "beta": 0.85},
        )
        assert params.search == "DLAS"
        assert params.crossover == "IRR"
        assert params.is_problem_reduction is False
        assert params.is_pop_variable is False
        assert params.initial_pop_size == 8
        assert params.reduce_params["beta"] == 0.85


class TestVariablePopulationParams:
    """Tests for VariablePopulationParams dataclass."""

    def test_default_values(self):
        """Test that default values are set correctly."""
        params = VariablePopulationParams()
        assert params.max_pop_size == 20
        assert params.increase_pop_size == 3
        assert params.max_idle_gens == 20

    def test_custom_max_pop_size(self):
        """Test setting custom maximum population size."""
        params = VariablePopulationParams(max_pop_size=50)
        assert params.max_pop_size == 50

    def test_custom_increase_pop_size(self):
        """Test setting custom increase population size."""
        params = VariablePopulationParams(increase_pop_size=5)
        assert params.increase_pop_size == 5

    def test_custom_max_idle_gens(self):
        """Test setting custom maximum idle generations."""
        params = VariablePopulationParams(max_idle_gens=30)
        assert params.max_idle_gens == 30

    def test_full_custom_config(self):
        """Test creating params with all custom values."""
        params = VariablePopulationParams(
            max_pop_size=40,
            increase_pop_size=4,
            max_idle_gens=15,
        )
        assert params.max_pop_size == 40
        assert params.increase_pop_size == 4
        assert params.max_idle_gens == 15

    def test_small_values(self):
        """Test that small values are accepted (edge case)."""
        params = VariablePopulationParams(
            max_pop_size=5,
            increase_pop_size=1,
            max_idle_gens=1,
        )
        assert params.max_pop_size == 5
        assert params.increase_pop_size == 1
        assert params.max_idle_gens == 1

    def test_large_values(self):
        """Test that large values are accepted (edge case)."""
        params = VariablePopulationParams(
            max_pop_size=1000,
            increase_pop_size=100,
            max_idle_gens=500,
        )
        assert params.max_pop_size == 1000
        assert params.increase_pop_size == 100
        assert params.max_idle_gens == 500
