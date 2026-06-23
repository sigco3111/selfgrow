"""자원 시스템 — 자원 타입, 지형별 분포, 재생성."""

from __future__ import annotations

import random
from enum import Enum
from typing import NamedTuple

from . import config


class ResourceType(str, Enum):
    """시뮬레이션 내 모든 자원."""
    FOOD = "food"
    WOOD = "wood"
    STONE = "stone"
    IRON = "iron"
    GOLD = "gold"

    @classmethod
    def all(cls) -> list[ResourceType]:
        return list(cls)

    @classmethod
    def basic(cls) -> list[ResourceType]:
        """모든 개체가 직간접적으로 필요로 하는 기초 자원."""
        return [cls.FOOD, cls.WOOD, cls.STONE]

    @classmethod
    def valuable(cls) -> list[ResourceType]:
        """희소 가치가 있는 자원."""
        return [cls.IRON, cls.GOLD]

    def display_name(self) -> str:
        return {
            "food": "식량", "wood": "목재", "stone": "돌",
            "iron": "철", "gold": "금",
        }[self.value]


# ──────────────────────────────────────────────
# Biome (지형)
# ──────────────────────────────────────────────
class Biome(str, Enum):
    PLAIN = "plain"
    FOREST = "forest"
    MOUNTAIN = "mountain"
    WATER = "water"
    DESERT = "desert"
    HILL = "hill"
    SWAMP = "swamp"

    @classmethod
    def traversable(cls) -> set[Biome]:
        """개체가 통과 가능한 지형."""
        return {cls.PLAIN, cls.FOREST, cls.MOUNTAIN,
                cls.DESERT, cls.HILL, cls.SWAMP}

    @classmethod
    def all(cls) -> list[Biome]:
        return list(cls)

    def display_char(self) -> str:
        return {
            "plain": ".", "forest": "T", "mountain": "^",
            "water": "~", "desert": ",", "hill": "n", "swamp": "=",
        }[self.value]

    def color_code(self) -> str:
        """ANSI 색상 코드."""
        return {
            "plain": "92",   # 초록
            "forest": "32",  # 진한 초록
            "mountain": "37",# 흰색
            "water": "94",   # 파랑
            "desert": "93",  # 노랑
            "hill": "33",    # 갈색
            "swamp": "90",   # 회색
        }[self.value]


# ──────────────────────────────────────────────
# Tile — 타일 1칸
# ──────────────────────────────────────────────
class Tile:
    """월드의 한 칸. 지형 + 현재 자원량."""

    def __init__(self, x: int, y: int, biome: Biome):
        self.x = x
        self.y = y
        self.biome = biome
        # config.MAX_TILE_RESOURCES에 정의된 최대량 기준으로 초기화
        # 타일별 편차(VARIATION)를 적용해 부유한 타일과 빈약한 타일 차이 극대화
        self.resources: dict[str, float] = {}
        var = config.RESOURCE_TILE_VARIATION
        tile_modifier = random.uniform(1.0 - var, 1.0 + var)
        max_res = config.MAX_TILE_RESOURCES.get(biome.value, {})
        for rtype, amount in max_res.items():
            base = amount * tile_modifier
            self.resources[rtype] = max(0.0, base * random.uniform(0.5, 1.0))

    def gather(self, resource_type: str, amount: float) -> float:
        """자원 채취. 실제 채취된 양 반환."""
        available = self.resources.get(resource_type, 0.0)
        taken = min(amount, available)
        self.resources[resource_type] = available - taken
        return taken

    def regenerate(self) -> None:
        """매 틱마다 자원이 최대치 방향으로 소량 회복."""
        max_res = config.MAX_TILE_RESOURCES.get(self.biome.value, {})
        for rtype, max_val in max_res.items():
            current = self.resources.get(rtype, 0.0)
            if current < max_val:
                delta = max_val * config.RESOURCE_REGEN_RATE
                self.resources[rtype] = min(max_val, current + delta)

    def total_resources(self) -> float:
        """이 타일의 전체 자원량."""
        return sum(self.resources.values())

    def is_water(self) -> bool:
        return self.biome == Biome.WATER

    def is_traversable(self) -> bool:
        return self.biome in Biome.traversable()

    def display_char(self) -> str:
        return self.biome.display_char()

    def color_code(self) -> str:
        return self.biome.color_code()
