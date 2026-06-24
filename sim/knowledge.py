"""지식/기술 시스템 — 발견, 전수, 연구."""

from __future__ import annotations

import random
import copy
from dataclasses import dataclass, field

from . import config


@dataclass
class Knowledge:
    """하나의 지식/기술 노드."""

    name: str
    description: str = ""
    prerequisites: list[str] = field(default_factory=list)
    research_cost: int = 20
    research_progress: int = 0
    discovered: bool = False
    # 발견 시 적용되는 효과 (entity가 참조)
    effects: dict = field(default_factory=dict)

    @property
    def is_researched(self) -> bool:
        return self.discovered

    def research(self, points: int) -> bool:
        """연구 포인트를 투입. 완료되면 True 반환."""
        if self.discovered:
            return False
        self.research_progress += points
        if self.research_progress >= self.research_cost:
            self.discovered = True
            return True
        return False


# ──────────────────────────────────────────────
# TechnologyTree — 모든 발견 가능 기술 관리
# ──────────────────────────────────────────────
class TechnologyTree:
    """전 세계 공유 기술 트리."""

    def __init__(self):
        self.techs: dict[str, Knowledge] = {}
        for tdef in config.TECH_TREE:
            self.techs[tdef.name] = Knowledge(
                name=tdef.name,
                description=tdef.description,
                prerequisites=tdef.prerequisites,
                research_cost=tdef.discovery_cost,
                effects=tdef.effect,
            )

    def get_available(self, discovered: set[str]) -> list[Knowledge]:
        """현재 연구 가능한 기술 목록 (선행 조건 충족 + 미발견)."""
        result = []
        for tech in self.techs.values():
            if tech.discovered:
                continue
            prereqs_met = all(p in discovered for p in tech.prerequisites)
            if prereqs_met:
                result.append(tech)
        return result

    def get_discovered(self) -> list[Knowledge]:
        return [t for t in self.techs.values() if t.discovered]

    def get_by_name(self, name: str) -> Knowledge | None:
        return self.techs.get(name)

    def all_techs(self) -> list[Knowledge]:
        return list(self.techs.values())

    def discover_count(self) -> int:
        return sum(1 for t in self.techs.values() if t.discovered)

    def total_count(self) -> int:
        return len(self.techs)


# ──────────────────────────────────────────────
# KnowledgeBook — 개체가 보유한 지식
# ──────────────────────────────────────────────
class KnowledgeBook:
    """개체별 지식 저장소. 배운 기술 + 연구 중인 기술."""

    def __init__(self):
        self.known: set[str] = set()
        self.researching: str | None = None  # 현재 연구 중인 기술명

    def know(self, tech_name: str) -> bool:
        """이미 알고 있으면 True."""
        return tech_name in self.known

    def learn(self, tech_name: str) -> None:
        """기술 습득."""
        self.known.add(tech_name)

    def forget(self, tech_name: str) -> None:
        """기술 상실 (문화적 진화에서 퇴보 시나리오)."""
        self.known.discard(tech_name)

    def share(self, other: KnowledgeBook, sociability: float,
              rng: random.Random | None = None) -> list[str]:
        """사회성에 비례해 보유 지식을 상대에게 전수. 전수된 목록 반환."""
        rng = rng or random
        transferred = []
        if rng.random() > sociability:
            return transferred
        share_count = max(1, int(len(self.known) * sociability))
        candidates = [t for t in self.known if not other.know(t)]
        if candidates:
            selected = rng.sample(candidates, min(share_count, len(candidates)))
            for tech in selected:
                other.learn(tech)
                transferred.append(tech)
        return transferred

    def copy_from(self, other: KnowledgeBook) -> None:
        """모든 지식을 복사 (문화적 전파)."""
        self.known = self.known | other.known

    def count(self) -> int:
        return len(self.known)
