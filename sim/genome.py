"""개체 유전자 — 진화 가능한 모든 형질과 돌연변이/교차 메커니즘."""

from __future__ import annotations

import copy
import random
from dataclasses import dataclass, field
from typing import ClassVar

from . import config


# ──────────────────────────────────────────────
# 특화 직업 (유전적 성향, 고정된 enum이 아니라 genome이 결정함
# ──────────────────────────────────────────────
SPECIALIZATIONS = [
    "general",    # 만능
    "farmer",     # 식량 채집 특화
    "miner",      # 광물 채집 특화
    "merchant",   # 거래 특화
    "warrior",    # 전투 특화
    "crafter",    # 제작 특화
    "explorer",   # 탐험 특화
]


@dataclass
class Genome:
    """개체의 유전 정보 — 진화의 단위.

    모든 수치는 0.0~1.0 범위로 정규화.
    """

    # ── 성향 (personality traits) ──
    risk_tolerance: float = 0.5       # 모험 성향 (높을수록 위험 감수)
    specialization: str = "general"   # 직업 성향
    curiosity: float = 0.5            # 탐험 성향 (높을수록 멀리 이동)
    sociability: float = 0.5          # 사회성 (거래/지식공유 빈도)
    aggression: float = 0.3           # 공격성 (전투 개시 확률)
    industry: float = 0.5             # 생산성 (제작/가공 선호)
    innovation_rate: float = 0.3      # 혁신성 (새 기술 채택 속도)

    # ── 신체 형질 (physical traits) ──
    strength: float = 0.5             # 힘 (공격력 보정)
    endurance: float = 0.5            # 체력 (최대 에너지 보정)
    speed: float = 0.5                # 민첩 (이동 속도 보정)
    fertility: float = 0.5            # 생식력 (번식 성공률)

    # ── 사회 형질 (social traits) ──
    loyalty: float = 0.5              # 충성심 (파벌 결속력, 이탈 방지)

    # ── 메타 ──
    generation: int = 0               # 현재 세대 수

    _trait_names: ClassVar[list[str]] = [
        "risk_tolerance", "curiosity", "sociability",
        "aggression", "industry", "innovation_rate",
        "strength", "endurance", "speed", "fertility",
        "loyalty",
    ]

    def mutate(self, rng: random.Random) -> Genome:
        """돌연변이: 설정된 확률/크기로 유전자 무작위 변경."""
        child = copy.deepcopy(self)
        child.generation = self.generation + 1

        for trait in self._trait_names:
            if rng.random() < config.MUTATION_RATE:
                delta = rng.uniform(-config.MUTATION_MAGNITUDE,
                                    config.MUTATION_MAGNITUDE)
                setattr(child, trait, max(0.0, min(1.0, getattr(child, trait) + delta)))

        # 직업도 소수 변이
        if rng.random() < config.MUTATION_RATE * 0.5:
            child.specialization = rng.choice(SPECIALIZATIONS)

        return child

    @classmethod
    def crossover(cls, parent1: Genome, parent2: Genome,
                  rng: random.Random) -> Genome:
        """두 부모 유전자의 균일 교차 (uniform crossover)."""
        child = copy.deepcopy(parent1)
        child.generation = max(parent1.generation, parent2.generation) + 1

        for trait in cls._trait_names:
            if rng.random() < 0.5:
                setattr(child, trait, getattr(parent2, trait))

        # 직업: 50% 확률로 한쪽 부모를 따름
        if rng.random() < 0.5:
            child.specialization = parent2.specialization

        return child

    def get_trait(self, name: str) -> float:
        """형질 값을 안전하게 조회."""
        return getattr(self, name, 0.5)

    def summary(self) -> str:
        """유전자 요약 (디버깅/시각화용)."""
        traits = {t: f"{getattr(self, t):.2f}" for t in self._trait_names}
        return (f"gen={self.generation} spec={self.specialization} "
                f"{traits}")

    @classmethod
    def random_initial(cls, rng: random.Random) -> Genome:
        """초기 개체용 무작위 유전자 생성."""
        g = cls()
        for trait in cls._trait_names:
            setattr(g, trait, rng.random())
        g.specialization = rng.choice(SPECIALIZATIONS)
        g.generation = 0
        # 초기 aggression은 약간 낮게
        g.aggression = rng.random() * 0.5
        return g
