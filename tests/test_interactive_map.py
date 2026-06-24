"""대화형 지도 테스트."""

from __future__ import annotations

import pytest
from sim.ui.interactive_map import (
    render_interactive_map,
    render_entity_info_panel,
    render_season_indicator,
)
from sim.world import World
from sim.entity import Entity
from sim.genome import Genome
from sim.season import Season
import random


@pytest.fixture
def world():
    """테스트용 월드 생성."""
    return World(seed=42)


def test_render_interactive_map(world):
    """대화형 지도 렌더링 테스트."""
    panel = render_interactive_map(world)
    assert panel is not None


def test_render_interactive_map_with_entity(world):
    """개체가 있는 대화형 지도 렌더링 테스트."""
    rng = random.Random(42)
    entity = Entity(10, 10, genome=Genome.random_initial(rng=rng))
    world.spawn_entity(entity)
    
    panel = render_interactive_map(world, tracked_entity=entity)
    assert panel is not None


def test_render_entity_info_panel():
    """개체 정보 패널 렌더링 테스트."""
    rng = random.Random(42)
    entity = Entity(10, 10, genome=Genome.random_initial(rng=rng))
    entity.name = "TestEntity"
    
    panel = render_entity_info_panel(entity)
    assert panel is not None


def test_render_season_indicator():
    """계절 표시 패널 렌더링 테스트."""
    panel = render_season_indicator(Season.SPRING, 100)
    assert panel is not None


def test_render_interactive_map_with_season(world):
    """계절별 대화형 지도 렌더링 테스트."""
    for season in Season:
        panel = render_interactive_map(world, current_season=season)
        assert panel is not None
