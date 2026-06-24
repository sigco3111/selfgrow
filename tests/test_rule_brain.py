"""RuleBasedBrain 테스트 — 행동 점수 기반 결정."""

import random
from sim.rule_brain import RuleBasedBrain
from sim.entity import Entity, EntityState
from sim.genome import Genome
from sim.world import World
from sim.market import Market


def _setup():
    rng = random.Random(42)
    g = Genome()
    g.curiosity = 0.5
    g.sociability = 0.5
    g.aggression = 0.3
    g.industry = 0.6
    g.specialization = "general"
    e = Entity(5, 5, genome=g, rng=rng, entity_id=0)
    e.inventory["food"] = 10
    e.inventory["wood"] = 5
    e.inventory["stone"] = 5
    e.energy = e.max_energy * 0.5
    w = World(seed=42)
    m = Market(rng=rng)
    b = RuleBasedBrain(rng=rng)
    e.brain = b
    return e, w, m, b


class TestRuleBrainDecide:
    def test_returns_entity_state(self):
        e, w, m, b = _setup()
        result = b.decide(e, w, m)
        assert isinstance(result, EntityState)

    def test_die_when_no_energy(self):
        e, w, m, b = _setup()
        e.energy = 0
        result = b.decide(e, w, m)
        assert result == EntityState.DIE

    def test_consume_when_hungry(self):
        e, w, m, b = _setup()
        e.energy = e.max_energy * 0.1
        e.inventory["food"] = 5
        result = b.decide(e, w, m)
        assert result == EntityState.CONSUME

    def test_idle_always_scored(self):
        e, w, m, b = _setup()
        result = b.decide(e, w, m)
        assert result is not None

    def test_no_market_still_works(self):
        e, w, _, b = _setup()
        result = b.decide(e, w, None)
        assert isinstance(result, EntityState)


class TestRuleBrainHelpers:
    def test_resource_need(self):
        e, w, m, b = _setup()
        e.inventory["food"] = 0
        need = b._resource_need(e)
        assert need > 0

    def test_has_surplus(self):
        e, w, m, b = _setup()
        e.inventory["food"] = 10
        assert b._has_surplus(e)

    def test_no_surplus(self):
        e, w, m, b = _setup()
        e.inventory["food"] = 1
        e.inventory["wood"] = 1
        e.inventory["stone"] = 1
        assert not b._has_surplus(e)

    def test_can_craft_with_materials(self):
        e, w, m, b = _setup()
        e.inventory["wood"] = 10
        e.inventory["stone"] = 10
        e.inventory["iron"] = 5
        result = b._can_craft_anything(e)
        assert isinstance(result, bool)

    def test_brain_type(self):
        b = RuleBasedBrain()
        assert b.brain_type() == "RuleBasedBrain"

    def test_feedback_noop(self):
        b = RuleBasedBrain()
        b.feedback(None, "idle", 0.0)
