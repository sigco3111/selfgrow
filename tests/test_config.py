"""설정 테스트 — 설정 오버라이드, create_rng 결정론."""

from __future__ import annotations

import random

from sim import config


def test_create_rng_same_seed_same_output():
    rng1 = config.create_rng(42, "test")
    rng2 = config.create_rng(42, "test")
    vals1 = [rng1.random() for _ in range(10)]
    vals2 = [rng2.random() for _ in range(10)]
    assert vals1 == vals2


def test_create_rng_different_subsystem():
    rng1 = config.create_rng(42, "engine")
    rng2 = config.create_rng(42, "world")
    vals1 = [rng1.random() for _ in range(10)]
    vals2 = [rng2.random() for _ in range(10)]
    assert vals1 != vals2


def test_create_rng_different_seed():
    rng1 = config.create_rng(42, "test")
    rng2 = config.create_rng(99, "test")
    vals1 = [rng1.random() for _ in range(10)]
    vals2 = [rng2.random() for _ in range(10)]
    assert vals1 != vals2


def test_create_rng_default_seed():
    rng = config.create_rng()
    assert isinstance(rng, random.Random)


def test_config_constants_exist():
    assert hasattr(config, "WORLD_WIDTH")
    assert hasattr(config, "WORLD_HEIGHT")
    assert hasattr(config, "INITIAL_ENTITY_COUNT")
    assert hasattr(config, "SEED")


def test_config_world_dimensions():
    assert config.WORLD_WIDTH > 0
    assert config.WORLD_HEIGHT > 0


def test_config_entity_count():
    assert config.INITIAL_ENTITY_COUNT > 0


def test_overridable_constants():
    assert hasattr(config, "BIOME_WEIGHTS")
    assert hasattr(config, "MAX_TILE_RESOURCES")
    assert hasattr(config, "RESOURCE_REGEN_RATE")


def test_config_dataclass_exists():
    assert hasattr(config, "TERRITORY_CLAIM_TICKS")
    assert hasattr(config, "TERRITORY_RADIUS")
