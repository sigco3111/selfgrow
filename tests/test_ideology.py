"""이데올로기 시스템 단위 테스트."""

from __future__ import annotations

import random

import pytest

from sim import config
from sim.entity import Entity
from sim.ideology import (
    determine_ideology,
    get_action_bias,
    process_ideology,
    ideology_summary,
    same_ideology_bonus,
)
from sim.world import World


@pytest.fixture
def sample_world() -> World:
    return World(seed=42, rng=config.create_rng(42, "world"))


@pytest.fixture
def sample_entity(sample_world: World) -> Entity:
    return Entity(x=10, y=10, rng=config.create_rng(42, "entity"))


def test_determine_ideology_returns_valid(sample_entity: Entity):
    ideology = determine_ideology(sample_entity)
    assert ideology in config.IDEOLOGIES or ideology == "none"


def test_determine_ideology_militarism():
    e = Entity(x=0, y=0, rng=random.Random(0))
    e.genome.aggression = 0.9
    e.genome.loyalty = 0.8
    e.genome.industry = 0.1
    e.genome.sociability = 0.1
    result = determine_ideology(e)
    assert result == "militarism"


def test_get_action_bias_none_ideology(sample_entity: Entity):
    sample_entity.ideology = "none"
    bias = get_action_bias(sample_entity)
    assert bias == {}


def test_get_action_bias_valid(sample_entity: Entity):
    sample_entity.ideology = "materialism"
    bias = get_action_bias(sample_entity)
    assert "trade" in bias
    assert bias["trade"] > 1.0


def test_same_ideology_bonus_same(sample_entity: Entity):
    other = Entity(x=11, y=10, rng=random.Random(1))
    sample_entity.ideology = "militarism"
    other.ideology = "militarism"
    bonus = same_ideology_bonus(sample_entity, other)
    assert bonus == config.IDEOLOGY_SAME_BONUS


def test_same_ideology_bonus_different(sample_entity: Entity):
    other = Entity(x=11, y=10, rng=random.Random(1))
    sample_entity.ideology = "militarism"
    other.ideology = "spiritualism"
    bonus = same_ideology_bonus(sample_entity, other)
    assert bonus == -config.IDEOLOGY_DIFFERENT_PENALTY


def test_same_ideology_bonus_none(sample_entity: Entity):
    other = Entity(x=11, y=10, rng=random.Random(1))
    sample_entity.ideology = "none"
    other.ideology = "militarism"
    bonus = same_ideology_bonus(sample_entity, other)
    assert bonus == 0.0


def test_process_ideology_forms_at_age(sample_world: World):
    e = Entity(x=5, y=5, rng=config.create_rng(1, "entity"))
    e.age = config.IDEOLOGY_FORMATION_TICKS + 10
    sample_world.entities[e.eid] = e
    rng = config.create_rng(42, "ideology")
    events = process_ideology(sample_world, rng)
    formed = [ev for ev in events if ev["type"] == "ideology_formed"]
    assert len(formed) >= 1


def test_ideology_summary(sample_world: World):
    e1 = Entity(x=5, y=5, rng=config.create_rng(1, "e1"), entity_id=100)
    e1.ideology = "militarism"
    e2 = Entity(x=6, y=5, rng=config.create_rng(2, "e2"), entity_id=101)
    e2.ideology = "militarism"
    sample_world.entities[e1.eid] = e1
    sample_world.entities[e2.eid] = e2
    summary = ideology_summary(sample_world)
    assert summary.get("militarism", 0) >= 2
