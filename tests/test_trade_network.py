"""무역 네트워크 테스트."""

from __future__ import annotations

import random
import pytest
from sim.trade_network import TradeNetwork, TradeRoute, TradeAgreement, get_trade_network, reset_trade_network
from sim.faction import Faction
from sim.world import World
from sim.entity import Entity
from sim.genome import Genome


@pytest.fixture
def world():
    """테스트용 월드 생성."""
    return World(seed=42)


@pytest.fixture
def trade_network():
    """테스트용 무역 네트워크 생성."""
    reset_trade_network()
    return TradeNetwork()


def test_trade_network_creation():
    """무역 네트워크 생성 테스트."""
    tn = TradeNetwork()
    assert tn.routes == {}
    assert tn.agreements == {}


def test_establish_agreement(world):
    """무역 협정 체결 테스트."""
    tn = TradeNetwork()
    
    # 파벌 생성
    faction_a = Faction("FactionA", 1, world)
    faction_b = Faction("FactionB", 2, world)
    world.faction_registry[faction_a.faction_id] = faction_a
    world.faction_registry[faction_b.faction_id] = faction_b
    
    # 협정 체결
    agreement = tn.establish_agreement(faction_a, faction_b, world)
    
    assert agreement is not None
    assert agreement.faction_a_id == faction_a.faction_id
    assert agreement.faction_b_id == faction_b.faction_id
    assert agreement.key in tn.agreements


def test_duplicate_agreement(world):
    """중복 협정 체결 방지 테스트."""
    tn = TradeNetwork()
    
    faction_a = Faction("FactionA", 1, world)
    faction_b = Faction("FactionB", 2, world)
    world.faction_registry[faction_a.faction_id] = faction_a
    world.faction_registry[faction_b.faction_id] = faction_b
    
    # 두 번 협정 체결 시도
    tn.establish_agreement(faction_a, faction_b, world)
    duplicate = tn.establish_agreement(faction_a, faction_b, world)
    
    assert duplicate is None
    assert len(tn.agreements) == 1


def test_trade_bonus(trade_network):
    """무역 보너스 계산 테스트."""
    tn = trade_network
    
    # 개체 생성
    rng = random.Random(42)
    entity = Entity(10, 10, genome=Genome.random_initial(rng=rng))
    entity.genome.sociability = 0.8
    
    # 파벌 생성 (무소속)
    world = World(seed=42)
    faction = Faction("Faction", 1, world)
    faction._members = {1}  # 더미 멤버
    
    # 무역 보너스 계산
    bonus = tn.get_trade_bonus(entity, faction)
    
    assert 1.0 <= bonus <= 2.0


def test_trade_volume(trade_network):
    """무역 거래량 계산 테스트."""
    tn = trade_network
    
    rng = random.Random(42)
    entity = Entity(10, 10, genome=Genome.random_initial(rng=rng))
    entity.genome.sociability = 0.5
    
    world = World(seed=42)
    faction = Faction("Faction", 1, world)
    faction._members = {1, 2, 3}  # 3명 멤버
    
    from sim.market import Market
    market = Market()
    
    volume = tn.calculate_trade_volume(entity, faction, market)
    
    assert volume >= 0.0


def test_process_trades(trade_network, world):
    """무역 처리 테스트."""
    tn = trade_network
    
    # 파벌 생성
    faction_a = Faction("FactionA", 1, world)
    faction_b = Faction("FactionB", 2, world)
    world.faction_registry[faction_a.faction_id] = faction_a
    world.faction_registry[faction_b.faction_id] = faction_b
    
    # 협정 체결
    tn.establish_agreement(faction_a, faction_b, world)
    
    from sim.market import Market
    market = Market()
    
    # 무역 처리
    import random
    rng = random.Random(42)
    events = tn.process_trades(world, market, rng)
    
    assert isinstance(events, list)


def test_faction_trade_summary(trade_network, world):
    """파벌 무역 요약 테스트."""
    tn = trade_network
    
    faction_a = Faction("FactionA", 1, world)
    faction_b = Faction("FactionB", 2, world)
    world.faction_registry[faction_a.faction_id] = faction_a
    world.faction_registry[faction_b.faction_id] = faction_b
    
    tn.establish_agreement(faction_a, faction_b, world)
    
    summary = tn.get_faction_trade_summary(faction_a.faction_id)
    
    assert "route_count" in summary
    assert "total_volume" in summary
    assert summary["route_count"] == 1


def test_get_trade_network():
    """글로벌 무역 네트워크 인스턴스 테스트."""
    reset_trade_network()
    tn1 = get_trade_network()
    tn2 = get_trade_network()
    
    assert tn1 is tn2
