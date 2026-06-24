"""savefile 라운드트립 테스트 — 저장→로드→재실행 검증."""

import os
import tempfile

from sim.engine import SimulationEngine
from sim.savefile import (
    save_game, load_game,
    _serialize_entity, _deserialize_entity,
    _serialize_market, _deserialize_market,
    _serialize_tech_tree, _deserialize_tech_tree,
)
from sim.knowledge import TechnologyTree
from sim.market import Market
from sim import config as _cfg


class TestSavefileRoundtrip:
    def test_engine_roundtrip(self):
        engine = SimulationEngine(seed=42)
        engine.run(max_ticks=30)

        alive_before = [e.eid for e in engine.world.entities.values() if e.alive]
        tick_before = engine.world.tick
        pop_before = len(alive_before)

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name
        try:
            save_game(engine, path)
            engine2 = load_game(path)

            assert engine2.world.tick == tick_before
            alive_after = [e.eid for e in engine2.world.entities.values() if e.alive]
            assert len(alive_after) == pop_before

            engine2.run(max_ticks=30)
            assert engine2.world.tick > tick_before
        finally:
            os.unlink(path)

    def test_entity_state_preserved(self):
        engine = SimulationEngine(seed=99)
        engine.run(max_ticks=20)

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name
        try:
            save_game(engine, path)
            engine2 = load_game(path)

            for eid, orig in engine.world.entities.items():
                loaded = engine2.world.entities.get(eid)
                assert loaded is not None, f"entity {eid} missing"
                assert loaded.x == orig.x
                assert loaded.y == orig.y
                assert loaded.energy == orig.energy
                assert loaded.age == orig.age
                assert loaded.genome.specialization == orig.genome.specialization
                assert loaded.genome.strength == orig.genome.strength
                assert loaded.knowledge.known == orig.knowledge.known
                assert loaded.faction_id == orig.faction_id
                assert loaded.currency.value == orig.currency.value
                assert loaded.money == orig.money
        finally:
            os.unlink(path)

    def test_market_state_preserved(self):
        engine = SimulationEngine(seed=7)
        engine.run(max_ticks=50)

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name
        try:
            save_game(engine, path)
            engine2 = load_game(path)

            assert engine2.market.tick == engine.market.tick
            assert len(engine2.market.buy_orders) == len(engine.market.buy_orders)
            assert len(engine2.market.sell_orders) == len(engine.market.sell_orders)
            for rtype in engine.market.price_history:
                assert len(engine2.market.price_history[rtype]) == len(
                    engine.market.price_history[rtype]
                )
        finally:
            os.unlink(path)

    def test_faction_state_preserved(self):
        engine = SimulationEngine(seed=42)
        engine.run(max_ticks=100)

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name
        try:
            save_game(engine, path)
            engine2 = load_game(path)

            orig_factions = engine.world.faction_registry
            loaded_factions = engine2.world.faction_registry
            assert len(loaded_factions) == len(orig_factions)
            for fid, orig in orig_factions.items():
                loaded = loaded_factions.get(fid)
                assert loaded is not None
                assert loaded.name == orig.name
                assert loaded.leader_id == orig.leader_id
                assert loaded.members == orig.members
        finally:
            os.unlink(path)

    def test_tech_tree_preserved(self):
        engine = SimulationEngine(seed=42)
        engine.run(max_ticks=50)

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name
        try:
            save_game(engine, path)
            engine2 = load_game(path)

            for name, orig_tech in engine.tech_tree.techs.items():
                loaded_tech = engine2.tech_tree.techs.get(name)
                assert loaded_tech is not None
                assert loaded_tech.discovered == orig_tech.discovered
                assert loaded_tech.research_progress == orig_tech.research_progress
        finally:
            os.unlink(path)

    def test_tile_resources_preserved(self):
        engine = SimulationEngine(seed=42)
        engine.run(max_ticks=10)

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name
        try:
            save_game(engine, path)
            engine2 = load_game(path)

            for y in range(engine.world.height):
                for x in range(engine.world.width):
                    orig_tile = engine.world.tile_at(x, y)
                    loaded_tile = engine2.world.tile_at(x, y)
                    assert loaded_tile.biome.value == orig_tile.biome.value
                    for rtype in orig_tile.resources:
                        assert abs(
                            loaded_tile.resources.get(rtype, 0)
                            - orig_tile.resources[rtype]
                        ) < 0.01
        finally:
            os.unlink(path)
