"""SmartBrain 테스트 — 의사결정, 경험 학습, 메시징."""

import random
from sim.smart_brain import SmartBrain
from sim.brain_base import Experience
from sim.entity import Entity, EntityState
from sim.genome import Genome
from sim.world import World
from sim.market import Market


def _setup():
    rng = random.Random(42)
    g = Genome()
    g.curiosity = 0.7
    g.sociability = 0.6
    g.aggression = 0.4
    g.industry = 0.5
    e = Entity(5, 5, genome=g, rng=rng, entity_id=0)
    e.inventory["food"] = 10
    e.inventory["wood"] = 5
    e.inventory["stone"] = 5
    e.energy = e.max_energy * 0.5
    w = World(seed=42)
    m = Market(rng=rng)
    b = SmartBrain(rng=rng)
    e.brain = b
    return e, w, m, b


class TestSmartBrainDecide:
    def test_returns_entity_state(self):
        e, w, m, b = _setup()
        result = b.decide(e, w, m)
        assert isinstance(result, EntityState)

    def test_die_when_no_energy(self):
        e, w, m, b = _setup()
        e.energy = 0
        result = b.decide(e, w, m)
        assert result == EntityState.DIE

    def test_process_messages_called(self):
        e, w, m, b = _setup()
        b.decide(e, w, m)
        assert b._current_tick == w.tick

    def test_goals_updated(self):
        e, w, m, b = _setup()
        e.inventory["food"] = 1
        b.decide(e, w, m)
        assert len(b.goals) > 0

    def test_plan_executed(self):
        e, w, m, b = _setup()
        b.current_plan = ["gather"]
        result = b.decide(e, w, m)
        assert result == EntityState.GATHER
        assert b.current_plan == []


class TestSmartBrainFeedback:
    def test_stores_experience(self):
        e, w, m, b = _setup()
        b._current_tick = 1
        b._last_state_snapshot = {"food": 5.0}
        b.feedback(e, "gather", 1.0)
        assert len(b.experiences) == 1
        assert b.experiences[0].action == "gather"
        assert b.experiences[0].outcome_score == 1.0

    def test_memory_limit(self):
        e, w, m, b = _setup()
        b._current_tick = 1
        for i in range(200):
            b._last_state_snapshot = {"food": float(i)}
            b.feedback(e, "gather", 1.0)
        assert len(b.experiences) <= 100


class TestSmartBrainSnapshot:
    def test_make_snapshot(self):
        e, w, m, b = _setup()
        snap = b._make_snapshot(e)
        assert "energy_ratio" in snap
        assert "food" in snap
        assert "age" in snap

    def test_state_similarity_identical(self):
        e, w, m, b = _setup()
        s = b._make_snapshot(e)
        assert b._state_similarity(s, s) == 1.0

    def test_state_similarity_different(self):
        e, w, m, b = _setup()
        a = {"food": 1.0, "wood": 1.0}
        b_ = {"food": 10.0, "wood": 10.0}
        sim = b._state_similarity(a, b_)
        assert 0.0 < sim < 1.0

    def test_state_similarity_empty(self):
        e, w, m, b = _setup()
        assert b._state_similarity({}, {}) == 0.0


class TestSmartBrainActionMap:
    def test_action_name_to_state(self):
        e, w, m, b = _setup()
        assert b._action_name_to_state("gather") == EntityState.GATHER
        assert b._action_name_to_state("trade") == EntityState.TRADE
        assert b._action_name_to_state("idle") == EntityState.IDLE
        assert b._action_name_to_state("unknown") is None


class TestSmartBrainPlanValid:
    def test_gather_valid_on_resource_tile(self):
        e, w, m, b = _setup()
        assert b._is_plan_valid("gather", e, w)

    def test_consume_valid_with_food(self):
        e, w, m, b = _setup()
        e.inventory["food"] = 5
        assert b._is_plan_valid("consume", e, w)

    def test_consume_invalid_without_food(self):
        e, w, m, b = _setup()
        e.inventory["food"] = 0
        assert not b._is_plan_valid("consume", e, w)
