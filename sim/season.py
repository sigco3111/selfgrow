from __future__ import annotations

from enum import Enum
from dataclasses import dataclass
from typing import TYPE_CHECKING

from . import config

if TYPE_CHECKING:
    pass


class Season(Enum):
    SPRING = 0
    SUMMER = 1
    AUTUMN = 2
    WINTER = 3


SEASON_NAMES_KR: dict[Season, str] = {
    Season.SPRING: "봄",
    Season.SUMMER: "여름",
    Season.AUTUMN: "가을",
    Season.WINTER: "겨울",
}


@dataclass
class SeasonEffects:
    regen_mult: float = 1.0
    energy_mult: float = 1.0
    gather_mult: float = 1.0
    speed_mult: float = 1.0


def compute_season(tick: int) -> Season:
    idx = (tick // config.SEASON_LENGTH) % 4
    return Season(idx)


def get_season_effects(season: Season) -> SeasonEffects:
    idx = season.value
    return SeasonEffects(
        regen_mult=config.SEASON_RESOURCE_REGEN[idx],
        energy_mult=config.SEASON_ENERGY_COST[idx],
        gather_mult=config.SEASON_GATHER_BONUS[idx],
        speed_mult=config.SEASON_SPEED_MOD[idx],
    )


def season_progress(tick: int) -> float:
    """0.0~1.0: 현재 계절의 진행도."""
    pos = tick % config.SEASON_LENGTH
    return pos / max(1, config.SEASON_LENGTH)
