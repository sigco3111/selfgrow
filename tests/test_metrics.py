"""통계 테스트 — 스냅샷 기록, 지니계수, HHI."""

from __future__ import annotations

from sim.metrics import MetricsCollector, Snapshot


def test_metrics_collector_creation():
    mc = MetricsCollector()
    assert mc.snapshots.__len__() == 0


def test_record_birth():
    mc = MetricsCollector()
    mc.record_birth()
    mc.record_birth()
    assert mc._running_births == 2


def test_record_death():
    mc = MetricsCollector()
    mc.record_death()
    assert mc._running_deaths == 1


def test_record_kill():
    mc = MetricsCollector()
    mc.record_kill()
    assert mc._running_kills == 1


def test_compute_gini_equal():
    wealths = [10.0, 10.0, 10.0, 10.0]
    gini = MetricsCollector._compute_gini(wealths)
    assert gini == 0.0


def test_compute_gini_unequal():
    wealths = [0.0, 0.0, 0.0, 100.0]
    gini = MetricsCollector._compute_gini(wealths)
    assert gini > 0.5


def test_compute_gini_empty():
    gini = MetricsCollector._compute_gini([])
    assert gini == 0.0


def test_compute_gini_single():
    gini = MetricsCollector._compute_gini([10.0])
    assert gini == 0.0


def test_compute_entropy_single():
    from collections import Counter
    counter = Counter({"farmer": 10})
    entropy = MetricsCollector._compute_entropy(counter, 10)
    assert entropy == 0.0


def test_compute_entropy_diverse():
    from collections import Counter
    counter = Counter({"farmer": 5, "miner": 5, "merchant": 5, "warrior": 5})
    entropy = MetricsCollector._compute_entropy(counter, 20)
    assert entropy > 0.5


def test_compute_entropy_empty():
    from collections import Counter
    entropy = MetricsCollector._compute_entropy(Counter(), 0)
    assert entropy == 1.0


def test_latest_empty():
    mc = MetricsCollector()
    assert mc.latest() is None


def test_snapshot_dataclass():
    snap = Snapshot(
        tick=100, population=40, births=5, deaths=2, kill_count=1,
        avg_energy=50.0, avg_wealth=20.0, gini_coefficient=0.3,
        specialization_diversity=0.7, total_wealth=800.0,
        total_trades=100, trade_volume=500.0, total_taxes=10.0,
        prices={"food": 2.0}, discovered_techs=3, total_techs=11,
        inventory_distribution={"food": 100.0},
        world_resources={"food": 500.0},
    )
    assert snap.tick == 100
    assert snap.population == 40
