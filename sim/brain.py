"""듀얼 브레인 시스템 — 개체의 의사결정 엔진.

RuleBasedBrain: 기존 행동 점수 기반 FSM (일반 개체)
SmartBrain:   경험 학습 + 멀티스텝 계획 + 목표 설정 + 메시징 (똑똑한 개체)
LLM/외부 API는 절대 사용하지 않습니다 — 모든 연산은 순수 로컬 알고리즘.
"""

from __future__ import annotations

import random

from . import config
from .brain_base import Brain, BrainMessage, Experience, Goal
from .rule_brain import RuleBasedBrain
from .smart_brain import SmartBrain

__all__ = [
    "Brain", "BrainMessage", "Experience", "Goal",
    "Goal",
    "RuleBasedBrain", "SmartBrain",
    "create_brain",
]


def create_brain(entity, world, rng: random.Random) -> Brain:
    """개체의 유전자와 환경에 따라 적절한 두뇌를 생성."""
    smart_chance = config.SMART_BRAIN_RATIO
    innovation_bonus = entity.genome.innovation_rate * 0.3
    smart_chance = min(1.0, smart_chance + innovation_bonus)

    if rng.random() < smart_chance:
        return SmartBrain(rng=rng)
    return RuleBasedBrain(rng=rng)
