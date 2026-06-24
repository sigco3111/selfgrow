"""개체 행동 테스트 — 탐험, 채집, 소비."""

from __future__ import annotations

import random
from unittest.mock import MagicMock

from sim.entity_action import do_explore, do_gather, do_consume
from sim.entity import Entity
from sim.resource import Biome, Tile


def _make_entity(x: int = 5, y: int = 5) -> Entity:
    e = Entity(x, y, rng=random.Random(42))
    e.eid = 0
    e.name = "E0000"
    e.energy = 80.0
    e.max_energy = 100.0
    e.inventory["food"] = 20.0
    return e


def _make_world(width: int = 20, height: int = 20):
    world = MagicMock()
    world.width = width
    world.height = height
    world.tick = 0
    world.entities = {}
    world.faction_registry = {}

    tiles = {}
    for y in range(height):
        for x in range(width):
            tile = MagicMock()
            tile.biome = Biome.PLAIN
            tile.resources = {"food": 10.0, "wood": 5.0, "stone": 3.0}
            tile.is_traversable.return_value = True
            tile.gather.side_effect = lambda rtype, amt: min(amt, tile.resources.get(rtype, 0))
            tiles[(x, y)] = tile

    def tile_at(x, y):
        return tiles.get((x, y))

    world.tile_at = tile_at

    def get_neighbors(x, y, include_diagonal=False, filter_traversable=True):
        neighbors = []
        for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < width and 0 <= ny < height:
                neighbors.append((nx, ny))
        return neighbors

    world.get_neighbors = get_neighbors
    return world


def test_do_explore():
    entity = _make_entity()
    world = _make_world()
    entity._rng = random.Random(42)
    events = do_explore(entity, world)
    assert len(events) >= 1
    assert events[0]["type"] == "move"


def test_do_gather():
    entity = _make_entity()
    world = _make_world()
    entity._rng = random.Random(42)
    entity.inventory = {}
    entity.known_techs = set()
    events, gathered = do_gather(entity, world)
    assert gathered >= 0.0
    assert isinstance(events, list)


def test_do_consume_has_food():
    entity = _make_entity()
    entity.inventory["food"] = 10.0
    entity.energy = 50.0
    entity._rng = random.Random(42)
    events = do_consume(entity)
    assert len(events) >= 1
    assert events[0]["type"] == "consume"


def test_do_consume_no_food():
    entity = _make_entity()
    entity.inventory = {}
    entity.energy = 50.0
    events = do_consume(entity)
    assert len(events) == 0


def test_do_consume_food_consumed():
    entity = _make_entity()
    entity.inventory["food"] = 10.0
    entity.energy = 50.0
    initial_food = entity.inventory["food"]
    events = do_consume(entity)
    assert entity.inventory["food"] < initial_food
