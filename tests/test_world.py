"""월드 테스트 — 지형 생성, 엔티티 관리, 공간 질의, 영토."""

from __future__ import annotations

import random

from sim.world import World
from sim.resource import Biome
from sim.entity import Entity


def _make_world(seed: int = 42) -> World:
    return World(seed=seed)


def test_world_dimensions():
    w = _make_world()
    assert w.width == 40
    assert w.height == 30


def test_terrain_not_all_water():
    w = _make_world()
    land = sum(1 for row in w.tiles for t in row if t.biome != Biome.WATER)
    assert land > 0


def test_border_tiles_are_land():
    w = _make_world()
    for x in range(w.width):
        for y in [0, w.height - 1]:
            assert w.tiles[y][x].biome != Biome.WATER
    for y in range(w.height):
        for x in [0, w.width - 1]:
            assert w.tiles[y][x].biome != Biome.WATER


def test_tile_at_in_bounds():
    w = _make_world()
    t = w.tile_at(5, 5)
    assert t is not None
    assert t.x == 5 and t.y == 5


def test_tile_at_out_of_bounds():
    w = _make_world()
    assert w.tile_at(-1, 0) is None
    assert w.tile_at(0, -1) is None
    assert w.tile_at(w.width, 0) is None
    assert w.tile_at(0, w.height) is None


def test_spawn_and_remove_entity():
    w = _make_world()
    e = Entity(5, 5, rng=random.Random(1))
    eid = w.spawn_entity(e)
    assert eid >= 0
    assert eid in w.entities
    assert (eid,) in [tuple([k]) for k in w._spatial_index.get((5, 5), [])]
    w.remove_entity(eid)
    assert eid not in w.entities


def test_entity_at():
    w = _make_world()
    e = Entity(10, 10, rng=random.Random(1))
    eid = w.spawn_entity(e)
    result = w.entity_at(10, 10)
    assert len(result) == 1
    assert result[0][0] == eid


def test_entity_at_empty():
    w = _make_world()
    result = w.entity_at(0, 0)
    assert result == []


def test_move_entity():
    w = _make_world()
    e = Entity(5, 5, rng=random.Random(1))
    eid = w.spawn_entity(e)
    w.move_entity(eid, 10, 10)
    assert e.x == 10 and e.y == 10
    assert (eid,) in [tuple([k]) for k in w._spatial_index.get((10, 10), [])]


def test_entities_near():
    w = _make_world()
    e1 = Entity(5, 5, rng=random.Random(1))
    e2 = Entity(6, 5, rng=random.Random(2))
    w.spawn_entity(e1)
    w.spawn_entity(e2)
    nearby = w.entities_near(5, 5, 2)
    assert len(nearby) == 2


def test_entities_near_empty():
    w = _make_world()
    nearby = w.entities_near(0, 0, 1)
    assert len(nearby) == 0


def test_is_traversable():
    w = _make_world()
    for y in range(w.height):
        for x in range(w.width):
            t = w.tile_at(x, y)
            if t.biome == Biome.WATER:
                assert not w.is_traversable(x, y)
            else:
                assert w.is_traversable(x, y)


def test_get_neighbors():
    w = _make_world()
    neighbors = w.get_neighbors(5, 5, filter_traversable=False)
    assert len(neighbors) == 4
    for nx, ny in neighbors:
        assert abs(nx - 5) + abs(ny - 5) == 1


def test_get_neighbors_corner():
    w = _make_world()
    neighbors = w.get_neighbors(0, 0)
    assert (1, 0) in neighbors
    assert (0, 1) in neighbors
    assert (-1, 0) not in [(n) for n in neighbors]


def test_claim_tile():
    w = _make_world()
    w.claim_tile(5, 5, 1)
    assert w.is_claimed_by(5, 5, 1)
    assert not w.is_claimed_by(5, 5, 2)


def test_get_claimant():
    w = _make_world()
    w.claim_tile(5, 5, 1)
    assert w.get_claimant(5, 5) == 1


def test_tick_update():
    w = _make_world()
    initial_tick = w.tick
    w.tick_update()
    assert w.tick == initial_tick + 1


def test_total_resources():
    w = _make_world()
    res = w.total_resources()
    assert isinstance(res, dict)
    assert "food" in res


def test_traversable_tiles():
    w = _make_world()
    traversable = w.traversable_tiles()
    assert traversable > 0
    assert traversable <= w.width * w.height


def test_faction_registry_initially_empty():
    w = _make_world()
    assert len(w.faction_registry) == 0
