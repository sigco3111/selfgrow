"""파벌 시스템 테스트 — 결성, 생명주기, 해체."""

from __future__ import annotations

import random
from unittest.mock import MagicMock

from sim.faction_system import process_factions
from sim.faction import Faction
from sim import config


def _make_world_with_entities(count: int = 5):
    world = MagicMock()
    world.tick = 100
    world.faction_registry = {}
    entities = {}
    for i in range(count):
        e = MagicMock()
        e.alive = True
        e.eid = i
        e.name = f"E{i:04d}"
        e.x = 10 + i
        e.y = 10
        e.faction_id = -1
        e.genome.sociability = 0.8
        e.genome.aggression = 0.3
        e.genome.specialization = "general"
        e.knowledge.count.return_value = 2
        e.total_wealth.return_value = 20.0
        e.energy = 80.0
        e.max_energy = 100.0
        e.kill_count = 0
        e.buildings = []
        e.home_x = 10 + i
        e.home_y = 10
        entities[i] = e
    world.entities = entities
    return world, entities


def test_process_factions_disabled():
    world, _ = _make_world_with_entities()
    logs = []
    old = config.FACTION_ENABLED
    config.FACTION_ENABLED = False
    try:
        process_factions(world, random.Random(42), lambda e: logs.append(e))
        assert len(world.faction_registry) == 0
    finally:
        config.FACTION_ENABLED = old


def test_faction_creation():
    world = MagicMock()
    f = Faction(name="TestFaction", leader_id=0, world=world)
    assert f.name == "TestFaction"
    assert f.leader_id == 0
    assert f.member_count == 1
    assert 0 in f.members


def test_faction_add_member():
    world = MagicMock()
    f = Faction(name="TestFaction", leader_id=0, world=world)
    f.members.add(1)
    assert 1 in f.members
    assert f.member_count == 2


def test_faction_remove_member():
    world = MagicMock()
    f = Faction(name="TestFaction", leader_id=0, world=world)
    f.members.add(1)
    f.members.discard(1)
    assert 1 not in f.members


def test_faction_declare_war():
    world = MagicMock()
    f1 = Faction(name="F1", leader_id=0, world=world)
    f1.declare_war(1)
    assert 1 in f1.wars
    assert f1.wars[1] > 0


def test_faction_is_at_war():
    world = MagicMock()
    f1 = Faction(name="F1", leader_id=0, world=world)
    assert not f1.is_at_war_with(1)
    f1.declare_war(1)
    assert f1.is_at_war_with(1)


def test_faction_tick_wars():
    world = MagicMock()
    f1 = Faction(name="F1", leader_id=0, world=world)
    f1.declare_war(1)
    initial = f1.wars[1]
    f1.tick_wars()
    assert f1.wars[1] < initial


def test_faction_tick_wars_expire():
    world = MagicMock()
    f1 = Faction(name="F1", leader_id=0, world=world)
    f1.wars[1] = 0
    f1.tick_wars()
    assert 1 not in f1.wars


def test_faction_set_cohesion():
    world, entities = _make_world_with_entities(3)
    f = Faction(name="F1", leader_id=0, world=world)
    f.members.add(0)
    f.members.add(1)
    f.members.add(2)
    f.set_cohesion(world.entities)
    assert hasattr(f, "_cohesion")


def test_faction_compute_strength():
    world, entities = _make_world_with_entities(3)
    f = Faction(name="F1", leader_id=0, world=world)
    f.members.add(0)
    f.members.add(1)
    f.members.add(2)
    f.compute_strength(world.entities)
    assert hasattr(f, "_strength")


def test_faction_try_form():
    world, entities = _make_world_with_entities(5)
    for e in entities.values():
        e.genome.sociability = 0.9
        e.genome.curiosity = 0.5
        e.genome.risk_tolerance = 0.5
        e.genome.innovation_rate = 0.5
        e.genome.aggression = 0.3
        e.genome.industry = 0.5
        e.genome.strength = 0.5
        e.genome.endurance = 0.5
        e.genome.speed = 0.5
        e.genome.fertility = 0.5
        e.genome.loyalty = 0.5
        e.total_wealth.return_value = 20.0
        e.energy = 80.0
        e.alive = True
        e.known_techs = set()
        e.knowledge.count.return_value = 2
    new_factions = Faction.try_form_factions(world.entities, world, world.faction_registry)
    assert isinstance(new_factions, list)
