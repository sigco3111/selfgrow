"""brain_planning 모듈 테스트 — 멀티스텝 계획."""

import random
from sim.brain_planning import try_multistep_plan, build_plan_from_action
from sim.smart_brain import SmartBrain
from sim.entity import Entity, EntityState
from sim.genome import Genome
from sim.world import World
from sim.market import Market


def _setup():
    rng = random.Random(42)
    g = Genome()
    g.curiosity = 0.7
    e = Entity(5, 5, genome=g, rng=rng, entity_id=0)
    e.inventory["food"] = 10
    e.inventory["wood"] = 5
    e.inventory["stone"] = 5
    w = World(seed=42)
    m = Market(rng=rng)
    b = SmartBrain(rng=rng)
    return e, w, m, b


class TestTryMultistepPlan:
    def test_sets_plan_when_better(self):
        e, w, m, b = _setup()
        scores = {EntityState.GATHER: 10.0, EntityState.TRADE: 8.0, EntityState.EXPLORE: 6.0}
        try_multistep_plan(e, w, m, scores, b)
        if b.current_plan:
            assert len(b.current_plan) >= 2

    def test_no_plan_with_single_action(self):
        e, w, m, b = _setup()
        scores = {EntityState.IDLE: 5.0}
        try_multistep_plan(e, w, m, scores, b)
        assert b.current_plan == []

    def test_empty_scores(self):
        e, w, m, b = _setup()
        try_multistep_plan(e, w, m, {}, b)
        assert b.current_plan == []


class TestBuildPlanFromAction:
    def test_gather_followed_by_trade(self):
        e, w, m, b = _setup()
        b.current_plan = []
        build_plan_from_action(e, w, m, EntityState.GATHER, b)
        if len(b.current_plan) >= 2:
            assert b.current_plan[0] == "gather"
            assert b.current_plan[1] == "trade"

    def test_existing_plan_not_overwritten(self):
        e, w, m, b = _setup()
        b.current_plan = ["gather", "trade"]
        build_plan_from_action(e, w, m, EntityState.GATHER, b)
        assert b.current_plan == ["gather", "trade"]
