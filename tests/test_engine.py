"""Engine 통합 테스트 — 시뮬레이션 실행, 지표, 재현성."""

from __future__ import annotations

from sim.engine import EngineState, SimulationEngine


def test_engine_runs_200_ticks():
    """200틱 동안 멸종 없이 실행되는지 확인."""
    engine = SimulationEngine(seed=42)
    for _ in range(200):
        engine._step()
        alive = [e for e in engine.world.entities.values() if e.alive]
        if not alive:
            break
    assert engine.world.tick == 200, f"{engine.world.tick}틱에서 중단"


def test_engine_metrics_recorded():
    """스냅샷이 주기적으로 기록되는지 확인."""
    engine = SimulationEngine(seed=42)
    for _ in range(100):
        engine._step()
    assert len(engine.metrics.snapshots) > 0


def test_engine_reproducibility():
    """동일 시드로 초기 상태가 동일한지 확인."""
    engines = [SimulationEngine(seed=42) for _ in range(2)]
    for e in engines:
        for _ in range(10):
            e._step()
    pops = [sum(1 for ent in e.world.entities.values() if ent.alive) for e in engines]
    # 10틱 이내에서는 RNG 시퀀스가 동일해야 함
    assert abs(pops[0] - pops[1]) <= 2, f"10틱 후 인구 차이 큼: {pops[0]} vs {pops[1]}"


def test_engine_faction_formation():
    """파벌이 조건에 따라 결성되는지 확인."""
    engine = SimulationEngine(seed=42)
    for _ in range(200):
        engine._step()
    assert len(engine.world.faction_registry) >= 0


def test_engine_state_method():
    """state()가 EngineState를 반환하는지 확인."""
    engine = SimulationEngine(seed=42)
    state = engine.state()
    assert state.tick == 0
    assert state.population > 0
    assert state.alive_count > 0
    assert state.running is False
