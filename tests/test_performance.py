"""성능 벤치마크 테스트 — 다양한 인구 규모에서의 실행 시간 측정."""

from __future__ import annotations

import time
import pytest
from sim.engine import SimulationEngine
from sim import config


@pytest.mark.performance
def test_benchmark_40_entities():
    """기본 인구(40) 100틱 벤치마크."""
    engine = SimulationEngine(seed=42)
    engine.running = True
    
    start = time.time()
    for _ in range(100):
        engine._step()
    elapsed = time.time() - start
    
    assert elapsed < 10.0, f"100틱 실행이 10초 초과: {elapsed:.2f}초"
    alive = sum(1 for e in engine.world.entities.values() if e.alive)
    assert alive > 0, "모든 개체가 사망"


@pytest.mark.performance
def test_benchmark_100_entities():
    """100개 엔티트 100틱 벤치마크."""
    original_count = config.INITIAL_ENTITY_COUNT
    config.INITIAL_ENTITY_COUNT = 100
    
    try:
        engine = SimulationEngine(seed=42)
        engine.running = True
        
        start = time.time()
        for _ in range(100):
            engine._step()
        elapsed = time.time() - start
        
        assert elapsed < 20.0, f"100틱 실행이 20초 초과: {elapsed:.2f}초"
        alive = sum(1 for e in engine.world.entities.values() if e.alive)
        assert alive > 0, "모든 개체가 사망"
    finally:
        config.INITIAL_ENTITY_COUNT = original_count


@pytest.mark.performance
def test_benchmark_200_entities():
    """200개 엔티트 100틱 벤치마크."""
    original_count = config.INITIAL_ENTITY_COUNT
    config.INITIAL_ENTITY_COUNT = 200
    
    try:
        engine = SimulationEngine(seed=42)
        engine.running = True
        
        start = time.time()
        for _ in range(100):
            engine._step()
        elapsed = time.time() - start
        
        assert elapsed < 40.0, f"100틱 실행이 40초 초과: {elapsed:.2f}초"
        alive = sum(1 for e in engine.world.entities.values() if e.alive)
        assert alive > 0, "모든 개체가 사망"
    finally:
        config.INITIAL_ENTITY_COUNT = original_count


@pytest.mark.performance
def test_spatial_index_efficiency():
    """공간 인덱스 효율성 테스트 — entities_near가 빠르게 동작하는지 확인."""
    engine = SimulationEngine(seed=42)
    engine.running = True
    
    # 50틱 실행하여 안정화
    for _ in range(50):
        engine._step()
    
    # entities_near 성능 측정
    start = time.time()
    for _ in range(1000):
        engine.world.entities_near(20, 15, 5)
    elapsed = time.time() - start
    
    assert elapsed < 1.0, f"1000회 entities_near 호출이 1초 초과: {elapsed:.2f}초"
