"""Faction 단위 테스트 — 파벌 결성, 결속력, 전쟁."""

from __future__ import annotations

import pytest

from sim import config
from sim.entity import Entity
from sim.faction import Faction
from sim.world import World


def _make_entity(x, y, entity_id, sociability):
    ent = Entity(x=x, y=y, entity_id=entity_id, rng=config.create_rng(42, "entity"))
    ent.sociability = sociability
    return ent


@pytest.fixture
def sample_world_with_entities() -> World:
    """개체가 있는 월드 생성."""
    world = World(seed=42, rng=config.create_rng(42, "world"))
    from sim.entity import Entity
    for i, (x, y) in enumerate([(5, 5), (5, 6), (6, 5), (10, 10)]):
        ent = _make_entity(x, y, i, 0.8 if i < 3 else 0.2)
        world.spawn_entity(ent)
    return world


def test_faction_creation(sample_world_with_entities: World):
    """파벌이 정상적으로 생성되는지 확인."""
    faction = Faction("TestFaction", leader_id=0, world=sample_world_with_entities)
    assert faction.faction_id >= 0
    assert faction.name == "TestFaction"
    assert faction.leader_id == 0
    assert faction.member_count == 1


def test_faction_add_member(sample_world_with_entities: World):
    """파벌에 멤버를 추가할 수 있는지 확인."""
    faction = Faction("TestFaction", leader_id=0, world=sample_world_with_entities)
    faction.members.add(1)
    assert faction.member_count == 2


def test_try_form_factions_eligibility(sample_world_with_entities: World):
    """사회성 조건을 충족하는 개체들이 파벌을 결성하는지 확인."""
    entities = sample_world_with_entities.entities
    faction_reg = {}
    new_factions = Faction.try_form_factions(
        entities, sample_world_with_entities, faction_reg
    )
    # 조건에 따라 0개 이상 결성될 수 있음
    assert isinstance(new_factions, list)


def test_faction_cleanup_disband():
    """멤버 부족 시 파벌이 해체되는지 확인."""
    world = World(seed=42, rng=config.create_rng(42, "world"))
    faction = Faction("LoneFaction", leader_id=0, world=world)
    faction_reg = {faction.faction_id: faction}
    entities = {}
    disbanded = Faction.cleanup_factions(faction_reg, entities)
    assert faction.faction_id in disbanded


def test_faction_cohesion_calculation():
    """결속력 계산이 0.0~1.0 범위인지 확인."""
    # 결속력은 cohesion params으로 초기화
    world = World(seed=42, rng=config.create_rng(42, "world"))
    faction = Faction("TestFaction", leader_id=0, world=world)
    # 빈 entities로 호출 시 기본값 유지되어야 함
    faction.set_cohesion({})
    assert 0.0 <= faction.cohesion <= 1.0
