from pycnp.Statistics import Statistics


def test_statistics_init():
    """
    Test initialization of Statistics.
    """
    stats = Statistics()
    assert stats.is_collecting()
    assert stats.num_iterations == 0
    assert stats.data == []

    stats_no_collect = Statistics(collect_stats=False)
    assert not stats_no_collect.is_collecting()


def test_collect_stats():
    """
    Test collecting statistics.
    """
    stats = Statistics()
    stats.collect(best_obj_value=100.0, population_size=10, num_idle_generations=0)

    assert stats.num_iterations == 1
    assert len(stats.data) == 1

    datum = stats.data[0]
    assert datum.best_obj_value == 100.0
    assert datum.population_size == 10
    assert datum.num_idle_generations == 0
    assert datum.runtime >= 0.0


def test_collect_stats_disabled():
    """
    Test that statistics are not collected when disabled.
    """
    stats = Statistics(collect_stats=False)
    stats.collect(100.0, 10, 0)

    assert stats.num_iterations == 0
    assert len(stats.data) == 0
