import pytest

from pycnp.stop import (
    MaxIterations,
    MaxRuntime,
    NoImprovement,
)


class TestMaxIterations:
    """Tests for MaxIterations stopping criterion."""

    def test_init_valid(self):
        """Test initialization with valid max_iterations."""
        criterion = MaxIterations(100)
        assert criterion.max_iterations == 100
        assert criterion.iterations == 0

    def test_init_invalid_negative(self):
        """Test that negative max_iterations raises ValueError."""
        with pytest.raises(ValueError):
            MaxIterations(-1)

    def test_init_invalid_zero(self):
        """Test that zero max_iterations raises ValueError."""
        with pytest.raises(ValueError):
            MaxIterations(0)

    def test_init_invalid_float(self):
        """Test that float max_iterations raises ValueError."""
        with pytest.raises(ValueError):
            MaxIterations(10.5)

    def test_init_invalid_string(self):
        """Test that string max_iterations raises ValueError."""
        with pytest.raises(ValueError):
            MaxIterations("100")

    def test_call_increments_counter(self):
        """Test that __call__ increments the iteration counter."""
        criterion = MaxIterations(5)
        assert criterion(100.0) is False
        assert criterion.iterations == 1
        assert criterion(100.0) is False
        assert criterion.iterations == 2

    def test_call_stops_at_limit(self):
        """Test that __call__ returns True when limit is reached."""
        criterion = MaxIterations(3)
        assert criterion(100.0) is False
        assert criterion(100.0) is False
        assert criterion(100.0) is True

    def test_get_name(self):
        """Test that get_name returns correct name."""
        assert MaxIterations(10).get_name() == "MaxIterations"


class TestMaxRuntime:
    """Tests for MaxRuntime stopping criterion."""

    def test_init_valid(self):
        """Test initialization with valid runtime."""
        criterion = MaxRuntime(60.0)
        assert criterion.max_runtime == 60.0

    def test_init_valid_int(self):
        """Test initialization with integer runtime."""
        criterion = MaxRuntime(60)
        assert criterion.max_runtime == 60

    def test_init_invalid_negative(self):
        """Test that negative runtime raises ValueError."""
        with pytest.raises(ValueError):
            MaxRuntime(-1.0)

    def test_init_invalid_zero(self):
        """Test that zero runtime raises ValueError."""
        with pytest.raises(ValueError):
            MaxRuntime(0.0)

    def test_init_invalid_string(self):
        """Test that string runtime raises ValueError."""
        with pytest.raises(ValueError):
            MaxRuntime("60")

    def test_call_before_timeout(self):
        """Test that __call__ returns False before timeout."""
        criterion = MaxRuntime(10.0)  # 10 seconds
        # Immediate call should return False
        assert criterion(100.0) is False

    def test_get_name(self):
        """Test that get_name returns correct name."""
        assert MaxRuntime(60).get_name() == "MaxRuntime"


class TestNoImprovement:
    """Tests for NoImprovement stopping criterion."""

    def test_init_valid(self):
        """Test initialization with valid max_idle_iterations."""
        criterion = NoImprovement(20)
        assert criterion.max_idle_iterations == 20
        assert criterion.idle_iterations == 0

    def test_init_invalid_negative(self):
        """Test that negative max_idle_iterations raises ValueError."""
        with pytest.raises(ValueError):
            NoImprovement(-1)

    def test_init_invalid_zero(self):
        """Test that zero max_idle_iterations raises ValueError."""
        with pytest.raises(ValueError):
            NoImprovement(0)

    def test_init_invalid_float(self):
        """Test that float max_idle_iterations raises ValueError."""
        with pytest.raises(ValueError):
            NoImprovement(10.5)

    def test_call_with_improvement(self):
        """Test __call__ when there is improvement."""
        criterion = NoImprovement(3)
        # Improvement resets counter
        assert criterion(100.0) is False
        assert criterion(99.0) is False  # Improvement!
        assert criterion.idle_iterations == 0

    def test_call_without_improvement(self):
        """Test __call__ when there is no improvement."""
        criterion = NoImprovement(3)
        assert criterion(100.0) is False
        assert criterion(100.0) is False
        assert criterion(100.0) is False
        assert criterion(100.0) is True  # 3 idle iterations reached

    def test_get_name(self):
        """Test that get_name returns correct name."""
        assert NoImprovement(10).get_name() == "NoImprovement"
