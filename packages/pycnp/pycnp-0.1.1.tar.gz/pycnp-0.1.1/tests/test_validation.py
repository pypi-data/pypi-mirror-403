import pytest

from pycnp.params import MemeticSearchParams
from pycnp.validation import (
    validate_crossover_strategy,
    validate_problem_type,
    validate_reduce_params,
    validate_search_strategy,
)


class TestValidateProblemType:
    """Tests for validate_problem_type function."""

    def test_valid_cnp_string(self):
        """Test valid CNP string."""
        assert validate_problem_type("CNP") == "CNP"
        assert validate_problem_type("cnp") == "CNP"

    def test_valid_dcnp_string(self):
        """Test valid DCNP string."""
        assert validate_problem_type("DCNP") == "DCNP"
        assert validate_problem_type("dcnp") == "DCNP"

    def test_invalid_string(self):
        """Test invalid problem type string."""
        with pytest.raises(Exception):  # InvalidProblemTypeError
            validate_problem_type("INVALID")

    def test_invalid_type(self):
        """Test invalid type (non-string, non-int)."""
        with pytest.raises(Exception):  # InvalidProblemTypeError
            validate_problem_type(3.14)  # type: ignore


class TestValidateSearchStrategy:
    """Tests for validate_search_strategy function."""

    def test_valid_cbnc_for_cnp(self):
        """Test CBNS is valid for CNP."""
        result = validate_search_strategy("CBNS", "CNP")
        assert result == "CBNS"

    def test_valid_chns_for_cnp(self):
        """Test CHNS is valid for CNP."""
        result = validate_search_strategy("CHNS", "CNP")
        assert result == "CHNS"

    def test_valid_dlas_for_cnp(self):
        """Test DLAS is valid for CNP."""
        result = validate_search_strategy("DLAS", "CNP")
        assert result == "DLAS"

    def test_case_insensitive(self):
        """Test that search strategy is case insensitive."""
        assert validate_search_strategy("cbns", "CNP") == "CBNS"
        assert validate_search_strategy("ChNs", "CNP") == "CHNS"

    def test_bcls_for_cnp_raises(self):
        """Test that BCLS raises ValueError for CNP."""
        with pytest.raises(ValueError, match="CNP problem type does not support BCLS"):
            validate_search_strategy("BCLS", "CNP")

    def test_bcls_for_dcnp(self):
        """Test that BCLS is valid for DCNP."""
        result = validate_search_strategy("BCLS", "DCNP")
        assert result == "BCLS"

    def test_chns_for_dcnp_raises(self):
        """Test that CHNS raises ValueError for DCNP."""
        with pytest.raises(
            ValueError,
            match=r"DCNP problem type currently only supports BCLS",
        ):
            validate_search_strategy("CHNS", "DCNP")

    def test_invalid_strategy_raises(self):
        """Test that invalid strategy raises InvalidSearchStrategyError."""
        with pytest.raises(Exception):  # InvalidSearchStrategyError
            validate_search_strategy("INVALID", "CNP")

    def test_integer_raises(self):
        """Test that integer value raises InvalidSearchStrategyError."""
        with pytest.raises(Exception):  # InvalidSearchStrategyError
            validate_search_strategy(1, "CNP")  # type: ignore


class TestValidateCrossoverStrategy:
    """Tests for validate_crossover_strategy function."""

    def test_rsc_when_problem_reduction(self):
        """Test that RSC is used when is_problem_reduction=True."""
        params = MemeticSearchParams(is_problem_reduction=True)
        result = validate_crossover_strategy(params, "CNP")
        assert result == "RSC"

    def test_dbx_when_no_reduction(self):
        """Test DBX is valid when is_problem_reduction=False."""
        params = MemeticSearchParams(is_problem_reduction=False, crossover="DBX")
        result = validate_crossover_strategy(params, "CNP")
        assert result == "DBX"

    def test_case_insensitive_crossover(self):
        """Test that crossover is case insensitive."""
        params = MemeticSearchParams(is_problem_reduction=False, crossover="dbx")
        result = validate_crossover_strategy(params, "CNP")
        assert result == "DBX"

    def test_no_crossover_raises(self):
        """Test that None crossover raises when is_problem_reduction=False."""
        params = MemeticSearchParams(is_problem_reduction=False, crossover=None)
        with pytest.raises(ValueError, match="crossover must be explicitly set"):
            validate_crossover_strategy(params, "CNP")

    def test_rsc_when_no_reduction_raises(self):
        """Test that RSC crossover raises when is_problem_reduction=False."""
        params = MemeticSearchParams(is_problem_reduction=False, crossover="RSC")
        with pytest.raises(ValueError, match="RSC is reserved for problem reduction"):
            validate_crossover_strategy(params, "CNP")

    def test_irr_for_cnp_raises(self):
        """Test that IRR raises for CNP problem type."""
        params = MemeticSearchParams(
            is_problem_reduction=False,
            crossover="IRR",
            initial_pop_size=3,
            is_pop_variable=False,
        )
        with pytest.raises(
            ValueError, match=r"IRR crossover is only supported for DCNP"
        ):
            validate_crossover_strategy(params, "CNP")

    def test_irr_for_dcnp(self):
        """Test IRR is valid for DCNP with correct params."""
        params = MemeticSearchParams(
            is_problem_reduction=False,
            crossover="IRR",
            initial_pop_size=3,
            is_pop_variable=False,
        )
        result = validate_crossover_strategy(params, "DCNP")
        assert result == "IRR"

    def test_irr_wrong_pop_size_raises(self):
        """Test IRR raises when initial_pop_size != 3."""
        params = MemeticSearchParams(
            is_problem_reduction=False,
            crossover="IRR",
            initial_pop_size=5,  # Must be 3
            is_pop_variable=False,
        )
        with pytest.raises(ValueError, match="requires exactly 3 individuals"):
            validate_crossover_strategy(params, "DCNP")

    def test_irr_with_variable_pop_raises(self):
        """Test IRR raises when is_pop_variable=True."""
        params = MemeticSearchParams(
            is_problem_reduction=False,
            crossover="IRR",
            initial_pop_size=3,
            is_pop_variable=True,  # Must be False
        )
        with pytest.raises(
            ValueError, match=r"does not support variable population size"
        ):
            validate_crossover_strategy(params, "DCNP")


class TestValidateReduceParams:
    """Tests for validate_reduce_params function."""

    def test_valid_defaults(self):
        """Test valid default reduce_params."""
        result = validate_reduce_params({}, "CNP")
        assert result["search"] == "CHNS"
        assert result["beta"] == 0.9

    def test_custom_reduce_params(self):
        """Test custom reduce_params."""
        result = validate_reduce_params({"search": "DLAS", "beta": 0.8}, "CNP")
        assert result["search"] == "DLAS"
        assert result["beta"] == 0.8

    def test_invalid_type_raises(self):
        """Test that non-dict raises TypeError."""
        with pytest.raises(TypeError, match="reduce_params must be a dict"):
            validate_reduce_params("invalid", "CNP")

    def test_invalid_search_raises(self):
        """Test that invalid search raises ValueError."""
        with pytest.raises(
            ValueError, match=r"Unsupported search strategy for reduce_params"
        ):
            validate_reduce_params({"search": "INVALID"}, "CNP")

    def test_beta_out_of_range_raises(self):
        """Test that beta outside [0, 1] raises ValueError."""
        with pytest.raises(ValueError, match=r"beta.*must be in"):
            validate_reduce_params({"beta": 1.5}, "CNP")

    def test_beta_negative_raises(self):
        """Test that negative beta raises ValueError."""
        with pytest.raises(ValueError, match=r"beta.*must be in"):
            validate_reduce_params({"beta": -0.1}, "CNP")

    def test_bcls_for_cnp_raises(self):
        """Test that BCLS reduce search raises for CNP."""
        with pytest.raises(ValueError, match=r"BCLS.*only supported for DCNP"):
            validate_reduce_params({"search": "BCLS"}, "CNP")

    def test_bcls_for_dcnp(self):
        """Test that BCLS reduce search is valid for DCNP."""
        result = validate_reduce_params({"search": "BCLS"}, "DCNP")
        assert result["search"] == "BCLS"

    def test_chns_for_dcnp_raises(self):
        """Test that CHNS reduce search raises for DCNP."""
        with pytest.raises(
            ValueError, match=r"reduce_params.*search.*must be.*BCLS"
        ):
            validate_reduce_params({"search": "CHNS"}, "DCNP")

    def test_case_insensitive_search(self):
        """Test that search is case insensitive."""
        result = validate_reduce_params({"search": "cbns"}, "CNP")
        assert result["search"] == "CBNS"

    def test_partial_params_use_defaults(self):
        """Test that partial params use defaults for missing keys."""
        result = validate_reduce_params({"beta": 0.7}, "CNP")
        assert result["search"] == "CHNS"  # default
        assert result["beta"] == 0.7
