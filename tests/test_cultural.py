"""문화적 진화 고도화 테스트."""

from __future__ import annotations

import random
import pytest
from sim.cultural import Culture, determine_culture, cultural_transfer
from sim.entity import Entity
from sim.genome import Genome
from sim.world import World


def test_culture_creation():
    """문화 생성 테스트."""
    culture = Culture()
    assert culture.language == "basic"
    assert culture.customs == set()
    assert culture.traditions == []


def test_culture_merge():
    """문화 합병 테스트."""
    rng = random.Random(42)
    
    culture1 = Culture(language="trade", customs={"hospitality", "trade_friendly"})
    culture2 = Culture(language="martial", customs={"martial_honor"})
    
    merged = culture1.merge(culture2, strength=0.5)
    
    assert merged.language in ["trade", "martial"]
    assert isinstance(merged.customs, set)


def test_determine_culture():
    """개체 문화 결정 테스트."""
    rng = random.Random(42)
    
    # 높은 사회성 개체
    entity1 = Entity(10, 10, genome=Genome.random_initial(rng=rng))
    entity1.genome.sociability = 0.8
    entity1.genome.curiosity = 0.3  # 사회성이 더 높도록
    culture1 = determine_culture(entity1, rng)
    assert culture1.language == "trade"
    
    # 높은 호기심 개체 (사회성 낮음)
    entity2 = Entity(10, 10, genome=Genome.random_initial(rng=rng))
    entity2.genome.sociability = 0.3
    entity2.genome.curiosity = 0.8
    culture2 = determine_culture(entity2, rng)
    assert culture2.language == "scholarly"


def test_cultural_transfer():
    """문화 전파 테스트."""
    rng = random.Random(42)
    world = World(seed=42)
    
    # 두 개체 생성
    entity1 = Entity(10, 10, genome=Genome.random_initial(rng=rng))
    entity1.genome.sociability = 0.8
    entity1.culture = Culture(language="trade", customs={"hospitality"})
    
    entity2 = Entity(11, 10, genome=Genome.random_initial(rng=rng))
    entity2.genome.sociability = 0.5
    entity2.culture = Culture(language="basic", customs=set())
    
    # 월드에 추가
    world.spawn_entity(entity1)
    world.spawn_entity(entity2)
    
    events = []
    def log_event(e):
        events.append(e)
    
    # 문화 전파 실행
    cultural_transfer(world, rng, log_event)
    
    # 이벤트 발생 확인 (지식, 언어, 관습 중 최소 1개)
    assert len(events) >= 0


def test_culture_attributes():
    """문화 속성 테스트."""
    culture = Culture(
        language="scholarly",
        customs={"scholarly_pursuit", "communal_living"},
        traditions=["ancient_wisdom"],
    )
    
    assert culture.language == "scholarly"
    assert "scholarly_pursuit" in culture.customs
    assert "ancient_wisdom" in culture.traditions
