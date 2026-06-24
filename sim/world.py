"""월드 — 격자 지형, 자원 분배, 공간 질의."""

from __future__ import annotations

import math
import random
from typing import TYPE_CHECKING

from . import config
from .resource import Biome, Tile
from collections import defaultdict

if TYPE_CHECKING:
    from .entity import Entity
    from .faction import Faction


class World:
    """시뮬레이션이 펼쳐지는 2D 격자 공간."""

    def __init__(self, seed: int | None = None, rng: random.Random | None = None):
        self.width = config.WORLD_WIDTH
        self.height = config.WORLD_HEIGHT
        if rng:
            self.rng = rng
        else:
            self.rng = config.create_rng(seed if seed is not None else config.SEED, "world")
        self.tick = 0

        # 타일 그리드
        self.tiles: list[list[Tile]] = []
        self._generate_terrain()

        # 개체 레지스트리
        self.entities: dict[int, Entity] = {}
        self._next_entity_id: int = 0

        # 타일 클레임: (x,y) -> (entity_id, last_claim_tick)
        self.tile_claims: dict[tuple[int, int], tuple[int, int]] = {}

        # 파벌 레지스트리: faction_id -> Faction
        self.faction_registry: dict[int, Faction] = {}

        # 공간 인덱스: (x,y) → [entity_id, ...]
        self._spatial_index: dict[tuple[int, int], list[int]] = {}

        # 이벤트 레지스트리: 활성화된 WorldEvent 목록
        self.event_registry: list = []
        self._last_event_tick: int = 0

    @property
    def faction_count(self) -> int:
        return len(self.faction_registry)

    # ── 지형 생성 ──
    def _generate_terrain(self) -> None:
        """Perlin-like 단순 노이즈로 지형 생성."""
        biomes = list(Biome.all())
        weights = [config.BIOME_WEIGHTS[b.value] for b in biomes]

        for y in range(self.height):
            row: list[Tile] = []
            for x in range(self.width):
                # 단순 가중치 랜덤 + 이웃과의 상관관계 최소화
                biome = self.rng.choices(biomes, weights=weights, k=1)[0]

                # 가장자리는 항상 땅 (물이 경계를 넘지 않도록)
                if biome == Biome.WATER:
                    if (x == 0 or x == self.width - 1 or
                        y == 0 or y == self.height - 1):
                        biome = Biome.PLAIN

                row.append(Tile(x, y, biome, rng=self.rng))
            self.tiles.append(row)

    # ── 타일 접근 ──
    def tile_at(self, x: int, y: int) -> Tile | None:
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.tiles[y][x]
        return None

    def is_traversable(self, x: int, y: int) -> bool:
        tile = self.tile_at(x, y)
        if tile is None:
            return False
        return tile.is_traversable()

    def get_neighbors(self, x: int, y: int, include_diagonal: bool = False,
                      filter_traversable: bool = True) -> list[tuple[int, int]]:
        """인접 타일 좌표 목록. filter_traversable=False면 모든 타일 반환."""
        neighbors = []
        for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < self.width and 0 <= ny < self.height:
                if not filter_traversable or self.is_traversable(nx, ny):
                    neighbors.append((nx, ny))
        if include_diagonal:
            for dx, dy in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
                nx, ny = x + dx, y + dy
                if 0 <= nx < self.width and 0 <= ny < self.height:
                    if not filter_traversable or self.is_traversable(nx, ny):
                        if (nx, ny) not in neighbors:
                            neighbors.append((nx, ny))
        return neighbors

    # ── 공간 인덱스 ──
    def _index_position(self, entity_id: int, x: int, y: int) -> None:
        """공간 인덱스에 개체 위치 등록."""
        key = (x, y)
        if key not in self._spatial_index:
            self._spatial_index[key] = []
        if entity_id not in self._spatial_index[key]:
            self._spatial_index[key].append(entity_id)

    def _unindex_position(self, entity_id: int, x: int, y: int) -> None:
        """공간 인덱스에서 개체 위치 제거."""
        key = (x, y)
        bucket = self._spatial_index.get(key)
        if bucket and entity_id in bucket:
            bucket.remove(entity_id)
            if not bucket:
                del self._spatial_index[key]

    def entities_near(self, x: int, y: int, radius: int) -> list[tuple[int, Entity]]:
        """(O(πr²)) 반경 내 모든 개체를 공간 인덱스로 조회."""
        result: list[tuple[int, Entity]] = []
        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                nx, ny = x + dx, y + dy
                key = (nx, ny)
                bucket = self._spatial_index.get(key)
                if bucket:
                    for eid in bucket:
                        entity = self.entities.get(eid)
                        if entity:
                            dist = abs(entity.x - x) + abs(entity.y - y)
                            if dist <= radius:
                                result.append((eid, entity))
        return result

    # ── 개체 관리 ──
    def spawn_entity(self, entity: Entity) -> int:
        entity_id = self._next_entity_id
        self._next_entity_id += 1
        self.entities[entity_id] = entity
        self._index_position(entity_id, entity.x, entity.y)
        return entity_id

    def remove_entity(self, entity_id: int) -> None:
        entity = self.entities.get(entity_id)
        if entity:
            self._unindex_position(entity_id, entity.x, entity.y)
        self.entities.pop(entity_id, None)
        expired = [pos for pos, (eid, _) in self.tile_claims.items() if eid == entity_id]
        for pos in expired:
            del self.tile_claims[pos]

    def move_entity(self, entity_id: int, new_x: int, new_y: int) -> None:
        """개체 이동 시 공간 인덱스 갱신."""
        entity = self.entities.get(entity_id)
        if entity and (entity.x != new_x or entity.y != new_y):
            self._unindex_position(entity_id, entity.x, entity.y)
            entity.x, entity.y = new_x, new_y
            self._index_position(entity_id, new_x, new_y)

    def entity_at(self, x: int, y: int) -> list[tuple[int, Entity]]:
        """특정 위치의 모든 개체 (공간 인덱스 활용)."""
        result: list[tuple[int, Entity]] = []
        bucket = self._spatial_index.get((x, y))
        if bucket:
            for eid in bucket:
                entity = self.entities.get(eid)
                if entity:
                    result.append((eid, entity))
        return result

    def find_nearest_tile_with(self, x: int, y: int,
                                 resource_type: str | None = None,
                                 max_distance: int = 10) -> tuple[int, int] | None:
        """BFS로 특정 조건의 가장 가까운 타일 찾기."""
        visited = {(x, y)}
        queue = [(x, y, 0)]

        while queue:
            cx, cy, dist = queue.pop(0)
            if dist > max_distance:
                continue

            tile = self.tile_at(cx, cy)
            if tile and tile.is_traversable():
                if resource_type is None:
                    if (cx, cy) != (x, y):
                        return (cx, cy)
                else:
                    if (cx, cy) != (x, y) and tile.resources.get(resource_type, 0) > 0:
                        return (cx, cy)

            for nx, ny in self.get_neighbors(cx, cy):
                if (nx, ny) not in visited:
                    visited.add((nx, ny))
                    queue.append((nx, ny, dist + 1))

        return None

    def find_entities_in_range(self, x: int, y: int, radius: int) -> list[tuple[int, Entity]]:
        """반경 내 모든 개체 (entities_near()로 대체 예정, 호환성 유지)."""
        return self.entities_near(x, y, radius)

    # ── 영토/클레임 ──
    def claim_tile(self, x: int, y: int, entity_id: int) -> None:
        self.tile_claims[(x, y)] = (entity_id, self.tick)

    def is_claimed_by(self, x: int, y: int, entity_id: int) -> bool:
        eid, _ = self.tile_claims.get((x, y), (None, 0))
        return eid == entity_id

    def get_claimant(self, x: int, y: int) -> int | None:
        if (x, y) in self.tile_claims:
            eid, tick = self.tile_claims[(x, y)]
            if self.tick - tick < config.TERRITORY_ABANDON_TICKS:
                return eid
            del self.tile_claims[(x, y)]
        return None

    def is_home_tile(self, x: int, y: int, entity_id: int) -> bool:
        """본거지 근처인지 확인 (본거지 기억 없으면 false)."""
        entity = self.entities.get(entity_id)
        if entity is None:
            return False
        if not hasattr(entity, "home_x") or entity.home_x is None:
            return False
        dist = abs(x - entity.home_x) + abs(y - entity.home_y)
        return dist <= config.TERRITORY_RADIUS

    # ── 틱 업데이트 ──
    def tick_update(self, regen_mult: float = 1.0) -> None:
        self.tick += 1
        for row in self.tiles:
            for tile in row:
                tile.regenerate(mult=regen_mult)

    # ── 통계 ──
    def traversable_tiles(self) -> int:
        return sum(1 for row in self.tiles for t in row if t.is_traversable())

    def total_resources(self) -> dict[str, float]:
        totals: dict[str, float] = {}
        for row in self.tiles:
            for tile in row:
                for rtype, amount in tile.resources.items():
                    totals[rtype] = totals.get(rtype, 0) + amount
        return totals
