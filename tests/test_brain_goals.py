"""brain_goals 모듈 테스트 — 목표 생성 및 행동 보너스."""

from sim.brain_goals import update_goals, goal_action_bonus, goal_relevant_actions
from sim.brain_base import Goal
from sim.entity import Entity, EntityState
from sim.genome import Genome
from sim import config


def _make_entity(food=5, iron=1, aggression=0.5, curiosity=0.7, spec="general"):
    rng = __import__("random").Random(42)
    g = Genome()
    g.aggression = aggression
    g.curiosity = curiosity
    g.specialization = spec
    e = Entity(5, 5, genome=g, rng=rng, entity_id=0)
    e.inventory["food"] = food
    e.inventory["iron"] = iron
    e.inventory["wood"] = 5
    e.inventory["stone"] = 5
    return e


def _make_brain():
    from sim.smart_brain import SmartBrain
    return SmartBrain(rng=__import__("random").Random(42))


def _make_world():
    from sim.world import World
    return World(seed=42)


class TestUpdateGoals:
    def test_low_food_creates_food_goal(self):
        e = _make_entity(food=2)
        b = _make_brain()
        update_goals(e, b)
        metrics = [g.metric for g in b.goals]
        assert "food_surplus" in metrics

    def test_enough_food_no_food_goal(self):
        e = _make_entity(food=15)
        b = _make_brain()
        update_goals(e, b)
        metrics = [g.metric for g in b.goals]
        assert "food_surplus" not in metrics

    def test_warrior_low_iron_creates_iron_goal(self):
        e = _make_entity(iron=1, spec="warrior")
        b = _make_brain()
        update_goals(e, b)
        metrics = [g.metric for g in b.goals]
        assert "iron_stock" in metrics

    def test_no_weapon_high_aggression_creates_equip_goal(self):
        e = _make_entity(aggression=0.5)
        e.equipped = []
        b = _make_brain()
        update_goals(e, b)
        metrics = [g.metric for g in b.goals]
        assert "equip_weapon" in metrics

    def test_high_curiosity_creates_explore_goal(self):
        e = _make_entity(curiosity=0.8)
        b = _make_brain()
        update_goals(e, b)
        metrics = [g.metric for g in b.goals]
        assert "explore" in metrics


class TestGoalActionBonus:
    def test_food_surplus_bonus(self):
        g = Goal("food_surplus", 12.0, 0.9)
        e = _make_entity()
        w = _make_world()
        assert goal_action_bonus(g, e, w) == 15.0

    def test_explore_bonus(self):
        g = Goal("explore", 20.0, 0.5)
        e = _make_entity()
        w = _make_world()
        assert goal_action_bonus(g, e, w) == 10.0

    def test_unknown_metric_default_bonus(self):
        g = Goal("unknown", 1.0, 0.5)
        e = _make_entity()
        w = _make_world()
        assert goal_action_bonus(g, e, w) == 5.0


class TestGoalRelevantActions:
    def test_food_surplus_relevant(self):
        g = Goal("food_surplus", 12.0, 0.9)
        actions = goal_relevant_actions(g)
        assert EntityState.GATHER in actions
        assert EntityState.TRADE in actions

    def test_explore_relevant(self):
        g = Goal("explore", 20.0, 0.5)
        actions = goal_relevant_actions(g)
        assert EntityState.EXPLORE in actions

    def test_unknown_empty(self):
        g = Goal("unknown", 1.0, 0.5)
        assert goal_relevant_actions(g) == []
