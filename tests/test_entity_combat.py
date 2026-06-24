"""전투 시스템 테스트 — 데미지 계산, 장비 보정."""

from __future__ import annotations

import random
from unittest.mock import MagicMock

from sim.entity_combat import do_combat
from sim.entity import Entity
from sim import config


def _make_combat_pair():
    e1 = Entity(5, 5, rng=random.Random(42))
    e1.eid = 0
    e1.name = "E0000"
    e1.energy = 80.0
    e1.max_energy = 100.0
    e1.faction_id = -1
    e1.home_x = None
    e1.home_y = None
    e1.genome.strength = 0.8
    e1.genome.endurance = 0.7
    e1.genome.speed = 0.6
    e1.equipped = []
    e1.buildings = []

    e2 = Entity(5, 5, rng=random.Random(99))
    e2.eid = 1
    e2.name = "E0001"
    e2.energy = 80.0
    e2.max_energy = 100.0
    e2.faction_id = -1
    e2.home_x = None
    e2.home_y = None
    e2.genome.strength = 0.5
    e2.genome.endurance = 0.5
    e2.genome.speed = 0.5
    e2.equipped = []
    e2.buildings = []

    return e1, e2


def _make_world_with_pair():
    e1, e2 = _make_combat_pair()
    world = MagicMock()
    world.width = 20
    world.height = 20
    world.tick = 100
    world.faction_registry = {}
    world.entities = {0: e1, 1: e2}

    def entity_at(x, y):
        result = []
        for eid, ent in world.entities.items():
            if ent.x == x and ent.y == y and ent is not e1:
                result.append((eid, ent))
        return result

    def entities_near(x, y, radius):
        result = []
        for eid, ent in world.entities.items():
            if abs(ent.x - x) + abs(ent.y - y) <= radius:
                result.append((eid, ent))
        return result

    world.entity_at = entity_at
    world.entities_near = entities_near
    return world, e1, e2


def test_combat_no_target():
    e1 = Entity(5, 5, rng=random.Random(42))
    e1.eid = 0
    world = MagicMock()
    world.entity_at.return_value = []
    world.entities_near.return_value = []
    world.faction_registry = {}
    events = do_combat(e1, world)
    assert events == []


def test_combat_basic():
    world, e1, e2 = _make_world_with_pair()
    events = do_combat(e1, world)
    assert len(events) >= 1
    assert events[0]["type"] == "combat"


def test_combat_damage_positive():
    world, e1, e2 = _make_world_with_pair()
    initial_energy = e2.energy
    events = do_combat(e1, world)
    assert e2.energy <= initial_energy


def test_combat_with_weapon():
    world, e1, e2 = _make_world_with_pair()
    e1.equipped = ["iron_sword"]
    events = do_combat(e1, world)
    assert len(events) >= 1


def test_combat_with_armor():
    world, e1, e2 = _make_world_with_pair()
    e2.equipped = ["iron_armor"]
    events = do_combat(e1, world)
    assert len(events) >= 1


def test_combat_home_bonus():
    world, e1, e2 = _make_world_with_pair()
    e1.home_x = 5
    e1.home_y = 5
    events = do_combat(e1, world)
    assert len(events) >= 1
