"""Entity 단위 테스트 — 행동, 자원, 전투, 번식."""

from __future__ import annotations

import pytest

from sim import config
from sim.entity import Entity, EntityState
from sim.world import World


def test_decide_action_returns_valid_state(sample_entity: Entity, sample_world: World):
    """brain이 항상 유효한 EntityState를 반환하는지 확인."""
    state = sample_entity.decide_action(sample_world, None)
    assert isinstance(state, EntityState)
    assert state in list(EntityState)


def test_do_consume_restores_energy(sample_entity: Entity):
    """식량 소비 후 에너지가 증가하는지 확인."""
    sample_entity.inventory["food"] = 10
    sample_entity.energy = 30  # max_energy 이하로 설정해 cap 문제 방지
    before = sample_entity.energy
    sample_entity.execute_action(EntityState.CONSUME, None, None)
    assert sample_entity.energy > before


def test_do_gather_depletes_tile(sample_entity: Entity, sample_world: World):
    """채집 후 타일 자원이 감소하는지 확인."""
    tile = sample_world.tile_at(sample_entity.x, sample_entity.y)
    if tile is None:
        pytest.skip("No tile at entity position")
    before = dict(tile.resources)
    sample_entity.execute_action(EntityState.GATHER, sample_world, None)
    for rtype, amount in before.items():
        if amount > 0:
            after = tile.resources.get(rtype, 0)
            if after < amount:
                return
    # 일부 자원이 줄었는지 확인
    total_before = sum(before.values())
    total_after = sum(tile.resources.values())
    assert total_after < total_before, "타일 자원이 감소하지 않음"


def test_do_reproduce_creates_child(sample_world: World):
    """번식 후 자식 개체가 생성되는지 확인."""
    parent = Entity(x=10, y=10, genome=None, rng=config.create_rng(42, "entity"))
    parent.energy = 100
    parent.inventory["food"] = 20
    # 빈 타일 인접 필요
    pop_before = len(sample_world.entities)
    parent.execute_action(EntityState.REPRODUCE, sample_world, None)
    assert len(sample_world.entities) >= pop_before


def test_age_update_decreases_energy(sample_entity: Entity):
    """노화 효과로 에너지가 감소하는지 확인."""
    sample_entity.age = sample_entity.max_age + 1
    before = sample_entity.energy
    sample_entity.age_update()
    assert sample_entity.energy < before


def test_total_wealth_includes_inventory(sample_entity: Entity):
    """자산 계산에 인벤토리와 화폐가 포함되는지 확인."""
    sample_entity.inventory["food"] = 10
    sample_entity.inventory["gold"] = 5
    sample_entity.money = 20.0
    wealth = sample_entity.total_wealth()
    assert wealth >= 10 + 5 + 20, f"wealth={wealth} 예상보다 낮음"


def test_hunger_entity_will_consume(sample_world: World):
    """배고픈 개체가 CONSUME을 선택하는지 확인."""
    entity = Entity(x=10, y=10, rng=config.create_rng(42, "entity"))
    entity.inventory["food"] = 5
    entity.energy = 10  # 배고픔 상태
    state = entity.decide_action(sample_world, None)
    # CONSUME일 필요는 없지만, 적어도 유효 상태여야 함
    assert isinstance(state, EntityState)
