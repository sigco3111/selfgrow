"""브레인 기반 클래스 — Experience, Goal, BrainMessage, Brain."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Experience:
    """과거 행동의 기록 — 유사 상황에서 더 나은 선택을 위해 사용."""
    state_snapshot: dict[str, float]
    action: str
    outcome_score: float


@dataclass
class Goal:
    """개체의 단기 목표 — SmartBrain이 자동 생성/추적."""
    metric: str
    target_value: float
    priority: float
    description: str = ""


@dataclass
class BrainMessage:
    """개체 간 구조화된 메시지 (LLM 없음, 정해진 프로토콜)."""
    msg_type: str
    sender_id: int
    target_id: int
    data: dict = field(default_factory=dict)


class Brain:
    """두뇌의 추상 기반. 모든 두뇌는 decide()로 행동을 선택."""

    def decide(self, entity, world, market=None):
        raise NotImplementedError

    def feedback(self, entity, action: str, outcome_score: float) -> None:
        pass

    def brain_type(self) -> str:
        return self.__class__.__name__
