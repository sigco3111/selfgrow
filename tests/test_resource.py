"""자원 시스템 테스트 — 바이옴 자원 생성, 타일 속성."""

from __future__ import annotations

import random

from sim.resource import ResourceType, Biome, Tile


def test_resource_type_all():
    all_types = ResourceType.all()
    assert len(all_types) == 5


def test_resource_type_basic():
    basic = ResourceType.basic()
    assert ResourceType.FOOD in basic
    assert ResourceType.IRON not in basic


def test_resource_type_valuable():
    val = ResourceType.valuable()
    assert ResourceType.IRON in val
    assert ResourceType.GOLD in val
    assert ResourceType.FOOD not in val


def test_resource_display_name():
    assert ResourceType.FOOD.display_name() == "식량"
    assert ResourceType.GOLD.display_name() == "금"


def test_biome_all():
    all_biomes = Biome.all()
    assert len(all_biomes) == 7


def test_biome_traversable():
    traversable = Biome.traversable()
    assert Biome.WATER not in traversable
    assert Biome.PLAIN in traversable
    assert Biome.FOREST in traversable


def test_biome_display_chars():
    for b in Biome.all():
        char = b.display_char()
        assert isinstance(char, str)
        assert len(char) == 1


def test_biome_color_codes():
    for b in Biome.all():
        code = b.color_code()
        assert isinstance(code, str)
        assert code.isdigit()


def test_tile_creation():
    rng = random.Random(42)
    t = Tile(5, 10, Biome.FOREST, rng)
    assert t.x == 5 and t.y == 10
    assert t.biome == Biome.FOREST


def test_tile_resources():
    rng = random.Random(42)
    t = Tile(5, 10, Biome.FOREST, rng)
    assert isinstance(t.resources, dict)
    for rtype, amount in t.resources.items():
        assert amount >= 0


def test_tile_gather():
    rng = random.Random(42)
    t = Tile(5, 10, Biome.FOREST, rng)
    food = t.resources.get("food", 0)
    if food > 0:
        taken = t.gather("food", food + 10)
        assert taken == food
        assert t.resources["food"] == 0


def test_tile_gather_no_resource():
    rng = random.Random(42)
    t = Tile(5, 10, Biome.FOREST, rng)
    taken = t.gather("iron", 5)
    assert taken == 0


def test_tile_regenerate():
    rng = random.Random(42)
    t = Tile(5, 10, Biome.FOREST, rng)
    for rtype in t.resources:
        t.resources[rtype] = 0
    t.regenerate(mult=1.0)
    for rtype, amount in t.resources.items():
        assert amount >= 0


def test_tile_total_resources():
    rng = random.Random(42)
    t = Tile(5, 10, Biome.FOREST, rng)
    total = t.total_resources()
    assert total >= 0
    assert total == sum(t.resources.values())


def test_tile_is_water():
    rng = random.Random(42)
    water = Tile(0, 0, Biome.WATER, rng)
    land = Tile(0, 0, Biome.PLAIN, rng)
    assert water.is_water()
    assert not land.is_water()


def test_tile_is_traversable():
    rng = random.Random(42)
    water = Tile(0, 0, Biome.WATER, rng)
    plain = Tile(0, 0, Biome.PLAIN, rng)
    assert not water.is_traversable()
    assert plain.is_traversable()


def test_tile_variation():
    rng1 = random.Random(42)
    rng2 = random.Random(99)
    tiles = [Tile(0, 0, Biome.FOREST, rng1) for _ in range(10)]
    tiles2 = [Tile(0, 0, Biome.FOREST, rng2) for _ in range(10)]
    avg1 = sum(t.total_resources() for t in tiles) / 10
    avg2 = sum(t.total_resources() for t in tiles2) / 10
    assert avg1 > 0
    assert avg2 > 0
