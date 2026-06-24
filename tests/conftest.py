"""테스트 공통 fixture — 시드 기반 재현성 보장."""

from __future__ import annotations

import random

import pytest

from sim import config
from sim.entity import Entity
from sim.engine import SimulationEngine
from sim.market import Market
from sim.world import World


@pytest.fixture
def seeded_rng() -> random.Random:
    return config.create_rng(42, "test")


@pytest.fixture
def sample_world() -> World:
    return World(seed=42, rng=config.create_rng(42, "world"))


@pytest.fixture
def sample_entity(sample_world: World) -> Entity:
    return Entity(x=10, y=10, rng=config.create_rng(42, "entity"))


@pytest.fixture
def sample_market() -> Market:
    return Market(rng=config.create_rng(42, "market"))


@pytest.fixture
def base_engine() -> SimulationEngine:
    return SimulationEngine(seed=42)
