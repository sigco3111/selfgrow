import sys

import pytest

sys.path.insert(0, r'C:\Users\신희정\selfgrow')

from sim import config
from sim.world import World
from sim.events import EventType, WorldEvent, in_event_area, generate_event, process_events


class TestEventArea:
    def test_center_is_in_area(self):
        ev = WorldEvent(EventType.WILDFIRE, 10, 5, 5, 5, 1.0)
        assert in_event_area(ev, 5, 5)

    def test_edge_is_in_area(self):
        ev = WorldEvent(EventType.WILDFIRE, 10, 5, 5, 5, 1.0)
        assert in_event_area(ev, 10, 5)

    def test_beyond_radius_is_out(self):
        ev = WorldEvent(EventType.WILDFIRE, 10, 5, 5, 5, 1.0)
        assert not in_event_area(ev, 11, 5)

    def test_far_point_is_out(self):
        ev = WorldEvent(EventType.WILDFIRE, 10, 5, 5, 5, 1.0)
        assert not in_event_area(ev, 100, 100)


class TestGenerateEvent:
    def test_generates_valid_event(self):
        world = World(seed=42, rng=config.create_rng(42, "world"))
        ev = generate_event(world, config.create_rng(42, "events"))
        assert ev is not None
        assert ev.event_type in list(EventType)
        assert 0 <= ev.center_x < world.width
        assert 0 <= ev.center_y < world.height
        assert ev.remaining > 0
        assert 0 < ev.severity <= 1.0


class TestProcessEvents:
    def test_event_lifecycle(self):
        world = World(seed=42, rng=config.create_rng(42, "world"))
        world.event_registry = []
        world._last_event_tick = 0

        ev = WorldEvent(EventType.BOUNTIFUL_HARVEST, remaining=2, center_x=15, center_y=15, radius=5, severity=0.5)
        world.event_registry = [ev]

        logs1 = process_events(world, config.create_rng(42, "events"))
        active1 = world.event_registry
        assert len(active1) == 1
        assert len([l for l in logs1 if l["type"] == "event_started"]) == 0

        logs2 = process_events(world, config.create_rng(42, "events"))
        active2 = world.event_registry
        assert len(active2) == 0
        ended = [l for l in logs2 if l["type"] == "event_ended"]
        assert len(ended) == 1
