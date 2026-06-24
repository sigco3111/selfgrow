"""파벌 외교 시스템 단위 테스트."""

from __future__ import annotations

import pytest

from sim import config
from sim.entity import Entity
from sim.faction import Faction
from sim.world import World


@pytest.fixture
def sample_world() -> World:
    return World(seed=42, rng=config.create_rng(42, "world"))


@pytest.fixture
def faction_a(sample_world: World) -> Faction:
    return Faction("Alpha", leader_id=1, world=sample_world)


@pytest.fixture
def faction_b(sample_world: World) -> Faction:
    return Faction("Beta", leader_id=2, world=sample_world)


def test_set_relation_alliance(faction_a: Faction, faction_b: Faction):
    faction_a.set_relation(faction_b.faction_id, "ALLIANCE")
    assert faction_a.get_relation(faction_b.faction_id) == "ALLIANCE"


def test_set_relation_trade_pact(faction_a: Faction, faction_b: Faction):
    faction_a.set_relation(faction_b.faction_id, "TRADE_PACT")
    assert faction_a.get_relation(faction_b.faction_id) == "TRADE_PACT"


def test_set_relation_invalid(faction_a: Faction, faction_b: Faction):
    faction_a.set_relation(faction_b.faction_id, "INVALID")
    assert faction_a.get_relation(faction_b.faction_id) is None


def test_has_treaty_with(faction_a: Faction, faction_b: Faction):
    faction_a.set_relation(faction_b.faction_id, "ALLIANCE")
    assert faction_a.has_treaty_with(faction_b.faction_id, "ALLIANCE")
    assert not faction_a.has_treaty_with(faction_b.faction_id, "TRADE_PACT")


def test_remove_relation(faction_a: Faction, faction_b: Faction):
    faction_a.set_relation(faction_b.faction_id, "ALLIANCE")
    faction_a.remove_relation(faction_b.faction_id)
    assert faction_a.get_relation(faction_b.faction_id) is None


def test_is_neutral(faction_a: Faction, faction_b: Faction):
    assert faction_a.is_neutral(faction_b.faction_id)
    faction_a.set_relation(faction_b.faction_id, "ALLIANCE")
    assert not faction_a.is_neutral(faction_b.faction_id)


def test_propose_treaty_alliance(faction_a: Faction, faction_b: Faction):
    result = faction_a.propose_treaty(faction_b, "ALLIANCE")
    assert result is True
    assert faction_a.has_treaty_with(faction_b.faction_id, "ALLIANCE")
    assert faction_b.has_treaty_with(faction_a.faction_id, "ALLIANCE")


def test_propose_treaty_trade_pact(faction_a: Faction, faction_b: Faction):
    result = faction_a.propose_treaty(faction_b, "TRADE_PACT")
    assert result is True
    assert faction_a.has_treaty_with(faction_b.faction_id, "TRADE_PACT")
    assert faction_b.has_treaty_with(faction_a.faction_id, "TRADE_PACT")


def test_propose_treaty_non_aggression(faction_a: Faction, faction_b: Faction):
    result = faction_a.propose_treaty(faction_b, "NON_AGGRESSION")
    assert result is True
    assert faction_a.has_treaty_with(faction_b.faction_id, "NON_AGGRESSION")


def test_propose_treaty_invalid(faction_a: Faction, faction_b: Faction):
    result = faction_a.propose_treaty(faction_b, "INVALID")
    assert result is False


def test_propose_treaty_while_at_war(faction_a: Faction, faction_b: Faction):
    faction_a.declare_war(faction_b.faction_id)
    result = faction_a.propose_treaty(faction_b, "ALLIANCE")
    assert result is False


def test_break_treaty_alliance(faction_a: Faction, faction_b: Faction):
    faction_a.propose_treaty(faction_b, "ALLIANCE")
    faction_a.break_treaty(faction_b)
    assert not faction_a.has_treaty_with(faction_b.faction_id, "ALLIANCE")
    assert not faction_b.has_treaty_with(faction_a.faction_id, "ALLIANCE")


def test_break_treaty_reduces_cohesion(faction_a: Faction, faction_b: Faction):
    faction_a.propose_treaty(faction_b, "ALLIANCE")
    cohesion_before = faction_a.cohesion
    faction_a.break_treaty(faction_b)
    assert faction_a.cohesion <= cohesion_before


def test_declare_war(faction_a: Faction, faction_b: Faction):
    faction_a.declare_war(faction_b.faction_id)
    assert faction_a.is_at_war_with(faction_b.faction_id)


def test_tick_wars_decrements(faction_a: Faction, faction_b: Faction):
    faction_a.declare_war(faction_b.faction_id)
    remaining_before = faction_a.wars[faction_b.faction_id]
    faction_a.tick_wars()
    assert faction_a.wars[faction_b.faction_id] == remaining_before - 1


def test_tick_wars_removes_expired(faction_a: Faction, faction_b: Faction):
    faction_a.wars[faction_b.faction_id] = 0
    faction_a.tick_wars()
    assert faction_b.faction_id not in faction_a.wars
