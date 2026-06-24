"""무역 네트워크 — 파벌 간 무역 협정, 장거리 무역 경로."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Optional

from . import config

if TYPE_CHECKING:
    from .entity import Entity
    from .world import World
    from .market import Market
    from .faction import Faction


@dataclass
class TradeRoute:
    """무역 경로 — 두 파벌 간의 무역 연결."""
    faction_a_id: int
    faction_b_id: int
    established_tick: int
    volume: float = 0.0  # 누적 거래량
    efficiency: float = 1.0  # 무역 효율 (0.5~1.5)
    
    @property
    def key(self) -> tuple[int, int]:
        return (min(self.faction_a_id, self.faction_b_id),
                max(self.faction_a_id, self.faction_b_id))


@dataclass
class TradeAgreement:
    """무역 협정 — 파벌 간 공식 무역 관계."""
    faction_a_id: int
    faction_b_id: int
    created_tick: int
    duration: int = 200  # 협정 지속 틱
    tax_discount: float = 0.3  # 거래 수수료 할인율
    
    @property
    def is_active(self) -> bool:
        return True  # 단순화: 항상 활성
    
    @property
    def key(self) -> tuple[int, int]:
        return (min(self.faction_a_id, self.faction_b_id),
                max(self.faction_a_id, self.faction_b_id))


class TradeNetwork:
    """무역 네트워크 — 파벌 간 무역 관계 관리."""
    
    def __init__(self):
        self.routes: dict[tuple[int, int], TradeRoute] = {}
        self.agreements: dict[tuple[int, int], TradeAgreement] = {}
        self._next_route_id: int = 0
    
    def establish_agreement(self, faction_a: Faction, faction_b: Faction,
                           world: World) -> Optional[TradeAgreement]:
        """무역 협정 체결.
        
        Args:
            faction_a: 첫 번째 파벌
            faction_b: 두 번째 파벌
            world: 월드 객체
            
        Returns:
            체결된 협정 또는 None
        """
        key = (min(faction_a.faction_id, faction_b.faction_id),
               max(faction_a.faction_id, faction_b.faction_id))
        
        # 이미 협정이 있으면 무시
        if key in self.agreements:
            return None
        
        # 전쟁 중이면 협정 불가
        if faction_a.faction_id in faction_b.wars:
            return None
        
        # 협정 체결
        agreement = TradeAgreement(
            faction_a_id=faction_a.faction_id,
            faction_b_id=faction_b.faction_id,
            created_tick=world.tick,
        )
        self.agreements[key] = agreement
        
        # 무역 경로 생성
        route = TradeRoute(
            faction_a_id=faction_a.faction_id,
            faction_b_id=faction_b.faction_id,
            established_tick=world.tick,
        )
        self.routes[key] = route
        
        return agreement
    
    def get_trade_bonus(self, entity: Entity, faction: Faction) -> float:
        """개체의 무역 보너스 계산.
        
        Args:
            entity: 개체
            faction: 소속 파벌
            
        Returns:
            무역 보너스 배율 (1.0 = 보너스 없음, 1.3 = 30% 보너스)
        """
        if faction.faction_id < 0:
            return 1.0
        
        bonus = 1.0
        
        # 파벌 내 무역 보너스 (사회성에 비례)
        member_bonus = 0.1 + entity.genome.sociability * 0.2
        bonus += member_bonus
        
        # 무역 협정 보너스
        for key, agreement in self.agreements.items():
            if faction.faction_id in key:
                bonus += agreement.tax_discount * 0.5
        
        return min(2.0, bonus)  # 최대 2배
    
    def calculate_trade_volume(self, entity: Entity, faction: Faction,
                              market: Market) -> float:
        """무역 거래량 계산.
        
        Args:
            entity: 개체
            faction: 소속 파벌
            market: 시장
            
        Returns:
            예상 거래량
        """
        if faction.faction_id < 0:
            return 0.0
        
        base_volume = 0.0
        
        # 파벌 멤버 수에 비례
        member_count = faction.member_count
        base_volume += member_count * 0.1
        
        # 무역 경로 효율성
        for key, route in self.routes.items():
            if faction.faction_id in key:
                base_volume *= route.efficiency
        
        # 개체 사회성에 비례
        sociability_bonus = entity.genome.sociability * 0.3
        base_volume *= (1.0 + sociability_bonus)
        
        return base_volume
    
    def process_trades(self, world: World, market: Market, rng) -> list[dict]:
        """무역 처리 — 파벌 간 거래 실행.
        
        Args:
            world: 월드 객체
            market: 시장
            rng: 난수 생성기
            
        Returns:
            거래 이벤트 리스트
        """
        events = []
        
        for key, route in self.routes.items():
            # 무역 경로 업데이트
            route.volume *= 0.95  # 시간에 따른 감쇠
            
            # 무역 효율 변동
            if rng.random() < 0.1:  # 10% 확률로 효율 변동
                route.efficiency = max(0.5, min(1.5, 
                    route.efficiency + rng.uniform(-0.1, 0.1)))
        
        return events
    
    def get_faction_trade_summary(self, faction_id: int) -> dict:
        """파벌의 무역 요약 정보.
        
        Args:
            faction_id: 파벌 ID
            
        Returns:
            무역 요약 딕셔너리
        """
        routes = []
        total_volume = 0.0
        
        for key, route in self.routes.items():
            if faction_id in key:
                partner = key[1] if key[0] == faction_id else key[0]
                routes.append({
                    "partner_faction": partner,
                    "volume": route.volume,
                    "efficiency": route.efficiency,
                })
                total_volume += route.volume
        
        return {
            "route_count": len(routes),
            "total_volume": total_volume,
            "routes": routes,
        }


# 전역 무역 네트워크 인스턴스
_trade_network: Optional[TradeNetwork] = None


def get_trade_network() -> TradeNetwork:
    """무역 네트워크 인스턴스 획득."""
    global _trade_network
    if _trade_network is None:
        _trade_network = TradeNetwork()
    return _trade_network


def reset_trade_network() -> None:
    """무역 네트워크 초기화 (테스트용)."""
    global _trade_network
    _trade_network = None
