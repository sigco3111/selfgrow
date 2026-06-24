"""Brain 단위 테스트 — RuleBasedBrain / SmartBrain 의사결정."""

from __future__ import annotations

import pytest

from sim.brain import RuleBasedBrain, SmartBrain
from sim.entity import Entity, EntityState
from sim.world import World


@pytest.fixture
def rule_brain() -> RuleBasedBrain:
    return RuleBasedBrain()


@pytest.fixture
def smart_brain() -> SmartBrain:
    return SmartBrain()


def test_rule_based_returns_valid_state(rule_brain: RuleBasedBrain,
                                         sample_entity: Entity,
                                         sample_world: World):
    """RuleBasedBrain이 항상 유효한 EntityState를 반환하는지 확인."""
    state = rule_brain.decide(sample_entity, sample_world, None)
    assert isinstance(state, EntityState)


def test_smart_brain_experience_learning(smart_brain: SmartBrain,
                                          sample_entity: Entity):
    """SmartBrain이 피드백을 통해 경험을 저장할 수 있는지 확인."""
    assert len(smart_brain.experiences) == 0
    smart_brain.feedback(sample_entity, "gather", 1.0)
    assert len(smart_brain.experiences) == 1
    exp = smart_brain.experiences[0]
    assert exp.action == "gather"
    assert exp.outcome_score == 1.0


def test_smart_brain_goal_generation(smart_brain: SmartBrain,
                                      sample_entity: Entity):
    """SmartBrain이 목표를 자동 생성할 수 있는지 확인."""
    smart_brain._update_goals(sample_entity)
    assert hasattr(smart_brain, "goals")


def test_smart_brain_message_handling(smart_brain: SmartBrain,
                                       sample_entity: Entity,
                                       sample_world: World):
    """SmartBrain이 outbox에 메시지를 추가할 수 있는지 확인."""
    msg_count_before = len(smart_brain.outbox)
    smart_brain.send_trade_offer(
        sample_entity, sample_world,
        target_id=2, resource="food", quantity=5,
    )
    assert len(smart_brain.outbox) == msg_count_before + 1
    msg = smart_brain.outbox[-1]
    assert msg.target_id == 2
    assert msg.msg_type == "trade_offer"
    assert msg.data.get("resource") == "food"


def test_state_similarity_identical():
    """동일한 상태의 유사도는 1.0이어야 함."""
    brain = SmartBrain()
    s = {"energy_ratio": 0.8, "food_count": 5}
    sim = brain._state_similarity(s, s)
    assert sim == 1.0


def test_state_similarity_different():
    """완전히 다른 상태의 유사도는 < 0.5여야 함."""
    brain = SmartBrain()
    a = {"energy_ratio": 0.8, "food_count": 5}
    b = {"energy_ratio": 0.1, "food_count": 0}
    sim = brain._state_similarity(a, b)
    assert sim < 0.5


def test_smart_brain_feedback_updates_scores(smart_brain: SmartBrain,
                                              sample_entity: Entity):
    """feedback()이 오류 없이 실행되고 경험을 추가하는지 확인."""
    smart_brain.feedback(sample_entity, "gather", 0.5)
    smart_brain.feedback(sample_entity, "trade", 2.0)
    assert len(smart_brain.experiences) == 2
