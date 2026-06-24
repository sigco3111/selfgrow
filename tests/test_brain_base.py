"""brain_base 데이터클래스 및 추상 클래스 테스트."""

import random
from sim.brain_base import Brain, BrainMessage, Experience, Goal


class TestExperience:
    def test_creation(self):
        exp = Experience(state_snapshot={"food": 5.0}, action="gather", outcome_score=1.5)
        assert exp.action == "gather"
        assert exp.outcome_score == 1.5
        assert exp.state_snapshot["food"] == 5.0

    def test_default_values(self):
        exp = Experience(state_snapshot={}, action="", outcome_score=0.0)
        assert exp.state_snapshot == {}


class TestGoal:
    def test_creation(self):
        g = Goal(metric="food_surplus", target_value=12.0, priority=0.9, description="need food")
        assert g.metric == "food_surplus"
        assert g.target_value == 12.0
        assert g.priority == 0.9
        assert g.description == "need food"

    def test_default_description(self):
        g = Goal(metric="iron_stock", target_value=5.0, priority=0.6)
        assert g.description == ""


class TestBrainMessage:
    def test_creation(self):
        msg = BrainMessage(msg_type="trade_offer", sender_id=1, target_id=2,
                           data={"resource": "food", "quantity": 3})
        assert msg.msg_type == "trade_offer"
        assert msg.sender_id == 1
        assert msg.target_id == 2
        assert msg.data["resource"] == "food"

    def test_default_data(self):
        msg = BrainMessage(msg_type="warning", sender_id=0, target_id=1)
        assert msg.data == {}


class TestBrainAbstract:
    def test_cannot_decide(self):
        brain = Brain()
        try:
            brain.decide(None, None)
            assert False, "Should raise NotImplementedError"
        except NotImplementedError:
            pass

    def test_feedback_noop(self):
        brain = Brain()
        brain.feedback(None, "idle", 0.0)

    def test_brain_type(self):
        brain = Brain()
        assert brain.brain_type() == "Brain"
