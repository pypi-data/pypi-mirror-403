import pytest

from pycnp.exceptions import (
    InvalidProblemTypeError,
    InvalidSearchStrategyError,
)


class TestInvalidProblemTypeError:
    """Tests for InvalidProblemTypeError exception."""

    def test_inherits_from_value_error(self):
        """Test that InvalidProblemTypeError inherits from ValueError."""
        assert issubclass(InvalidProblemTypeError, ValueError)

    def test_can_be_raised(self):
        """Test that the exception can be raised."""
        with pytest.raises(InvalidProblemTypeError):
            raise InvalidProblemTypeError("Invalid problem type")

    def test_custom_message(self):
        """Test that custom message is preserved."""
        msg = "Custom error message"
        with pytest.raises(InvalidProblemTypeError, match=msg):
            raise InvalidProblemTypeError(msg)


class TestInvalidSearchStrategyError:
    """Tests for InvalidSearchStrategyError exception."""

    def test_inherits_from_value_error(self):
        """Test that InvalidSearchStrategyError inherits from ValueError."""
        assert issubclass(InvalidSearchStrategyError, ValueError)

    def test_can_be_raised(self):
        """Test that the exception can be raised."""
        with pytest.raises(InvalidSearchStrategyError):
            raise InvalidSearchStrategyError("Invalid search strategy")

    def test_custom_message(self):
        """Test that custom message is preserved."""
        msg = "Custom error message"
        with pytest.raises(InvalidSearchStrategyError, match=msg):
            raise InvalidSearchStrategyError(msg)
