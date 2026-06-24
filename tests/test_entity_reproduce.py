"""생식 시스템 테스트 — 후손 생성, 유전자 교차."""

from __future__ import annotations

import random
from unittest.mock import MagicMock

from sim.entity_reproduce import do_reproduce
from sim.entity import Entity
from sim import config


def _make_parent() -> Entity:
    e = Entity(5, 5, rng=random.Random(42))
    e.eid = 0
    e.name = "E0000"
    e.energy = 80.0
    e.max_energy = 100.0
    e.children_count = 0
    e.reproduction_cooldown = 0
    e.inventory["food"] = 20.0
    e.knowledge.learn("basic_agriculture")
    return e


def _make_world_for_repro():
    world = MagicMock()
    world.width = 20
    world.height = 20
    world.tick = 100
    world.faction_registry = {}
    world.entities = {}
    world._next_entity_id = 1

    def get_neighbors(x, y, include_diagonal=False, filter_traversable=True):
        neighbors = []
        for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < 20 and 0 <= ny < 20:
                neighbors.append((nx, ny))
        return neighbors

    def entities_near(x, y, radius):
        return []

    def spawn_entity(entity):
        eid = world._next_entity_id
        world._next_entity_id += 1
        world.entities[eid] = entity
        return eid

    world.get_neighbors = get_neighbors
    world.entities_near = entities_near
    world.spawn_entity = spawn_entity
    return world


def test_do_reproduce_creates_child():
    parent = _make_parent()
    world = _make_world_for_repro()
    events = do_reproduce(parent, world)
    assert len(events) >= 1
    assert events[0]["type"] == "reproduce"
    assert parent.children_count >= 1


def test_do_reproduce_child_in_world():
    parent = _make_parent()
    world = _make_world_for_repro()
    initial_count = len(world.entities)
    do_reproduce(parent, world)
    assert len(world.entities) > initial_count


def test_do_reproduce_cooldown():
    parent = _make_parent()
    world = _make_world_for_repro()
    do_reproduce(parent, world)
    assert parent.reproduction_cooldown > 0


def test_do_reproduce_no_partner():
    parent = _make_parent()
    world = _make_world_for_repro()
    events = do_reproduce(parent, world)
    assert len(events) >= 1


def test_do_reproduce_energy_cost():
    parent = _make_parent()
    parent.energy = 80.0
    world = _make_world_for_repro()
    do_reproduce(parent, world)
    assert parent.energy < 80.0


def test_reproduction_config():
    assert hasattr(config, "REPRODUCTION_COOLDOWN")
    assert hasattr(config, "ENERGY_COST")
    assert "reproduce" in config.ENERGY_COST
