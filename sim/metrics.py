"""통계 수집 — 경제/인구/기술 지표의 시계열 수집."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from . import config
from .genome import SPECIALIZATIONS

if TYPE_CHECKING:
    from .world import World
    from .market import Market


@dataclass
class Snapshot:
    """특정 틱의 전체 상태 스냅샷."""
    tick: int
    population: int
    births: int
    deaths: int
    kill_count: int
    avg_energy: float
    avg_wealth: float
    gini_coefficient: float
    specialization_diversity: float  # 엔트로피 기반 분업 지수
    total_wealth: float
    total_trades: int
    trade_volume: float
    total_taxes: float
    prices: dict[str, float]
    discovered_techs: int
    total_techs: int
    inventory_distribution: dict[str, float]  # 자원별 총량
    world_resources: dict[str, float]


class MetricsCollector:
    """전체 지표 수집기 — 주기적 스냅샷 저장."""

    def __init__(self):
        self.snapshots: list[Snapshot] = []
        self._running_births = 0
        self._running_deaths = 0
        self._running_kills = 0

    def record_birth(self) -> None:
        self._running_births += 1

    def record_death(self) -> None:
        self._running_deaths += 1

    def record_kill(self) -> None:
        self._running_kills += 1

    def snapshot(self, tick: int, world: World, market: Market) -> Snapshot:
        """현재 상태의 스냅샷 생성."""
        entities = list(world.entities.values())
        alive = [e for e in entities if e.alive]
        pop = len(alive)

        if pop == 0:
            return Snapshot(
                tick=tick, population=0, births=self._running_births,
                deaths=self._running_deaths, kill_count=0,
                avg_energy=0, avg_wealth=0, gini_coefficient=0,
                specialization_diversity=0, total_wealth=0,
                total_trades=len(market.trade_history),
                trade_volume=market.trade_volume(),
                total_taxes=market.total_taxes(),
                prices={},
                discovered_techs=0, total_techs=0,
                inventory_distribution={},
                world_resources={},
            )

        # 평균 에너지
        avg_energy = sum(e.energy for e in alive) / pop

        # 부(wealth) 분포
        wealths = [e.total_wealth() for e in alive]
        total_wealth = sum(wealths)
        avg_wealth = total_wealth / pop

        # 지니계수
        gini = self._compute_gini(wealths)

        # 특화 다양성 (엔트로피)
        spec_counts: Counter[str] = Counter()
        for e in alive:
            spec_counts[e.genome.specialization] += 1
        diversity = self._compute_entropy(spec_counts, len(alive))

        # 총 전투 수
        total_kills = self._running_kills

        # 시장 정보
        prices = market.market_summary()["prices"]

        # 기술 정보 (임시 — engine에서 주입)
        discovered_techs = 0
        total_techs = 0

        # 인벤토리 분포
        inv_dist: dict[str, float] = {}
        for e in alive:
            for rtype, amount in e.inventory.items():
                inv_dist[rtype] = inv_dist.get(rtype, 0) + amount

        # 월드 자원
        world_res = world.total_resources()

        snap = Snapshot(
            tick=tick, population=pop,
            births=self._running_births,
            deaths=self._running_deaths,
            kill_count=total_kills,
            avg_energy=round(avg_energy, 1),
            avg_wealth=round(avg_wealth, 2),
            gini_coefficient=round(gini, 4),
            specialization_diversity=round(diversity, 4),
            total_wealth=round(total_wealth, 2),
            total_trades=len(market.trade_history),
            trade_volume=round(market.trade_volume(), 2),
            total_taxes=round(market.total_taxes(), 2),
            prices=prices,
            discovered_techs=discovered_techs,
            total_techs=total_techs,
            inventory_distribution=inv_dist,
            world_resources=world_res,
        )
        self.snapshots.append(snap)
        return snap

    @staticmethod
    def _compute_gini(wealths: list[float]) -> float:
        """지니계수 계산 (0=완전평등, 1=완전불평등)."""
        if not wealths:
            return 0.0
        sorted_w = sorted(wealths)
        n = len(sorted_w)
        cumulative = 0
        numerator = 0
        for i, w in enumerate(sorted_w):
            cumulative += w
            numerator += (i + 1) * w
        if cumulative == 0:
            return 0.0
        gini = (2 * numerator) / (n * cumulative) - (n + 1) / n
        return max(0.0, gini)

    @staticmethod
    def _compute_entropy(counter: Counter, total: int) -> float:
        """허핀달-허쉬만 지수 기반 다양성 (0=단일특화, 1=완전분산)."""
        if total <= 1:
            return 1.0
        n = len(counter)
        if n <= 1:
            return 0.0
        hhi = sum((c / total) ** 2 for c in counter.values())
        # 정규화: (1-HHI)를 (1-1/n)으로 나눠 0~1 범위로
        min_hhi = 1.0 / n
        if hhi <= min_hhi:
            return 1.0
        diversity = (1.0 - hhi) / (1.0 - min_hhi) if min_hhi < 1.0 else 0.0
        return max(0.0, min(1.0, diversity))

    def latest(self) -> Snapshot | None:
        """최신 스냅샷."""
        return self.snapshots[-1] if self.snapshots else None

    def summary_text(self, snap: Snapshot | None = None) -> str:
        """인간이 읽기 쉬운 요약 문자열."""
        s = snap or self.latest()
        if s is None:
            return "(데이터 없음)"
        return (
            f"━━━ 틱 {s.tick} ━━━\n"
            f"인구: {s.population} (출생:{s.births} 사망:{s.deaths} 전투사:{s.kill_count})\n"
            f"평균 에너지: {s.avg_energy} | 평균 자산: {s.avg_wealth}\n"
            f"지니계수: {s.gini_coefficient} | 분업지수: {s.specialization_diversity}\n"
            f"총 거래: {s.total_trades} (총량: {s.trade_volume}, 세금: {s.total_taxes})\n"
            f"가격: {s.prices}\n"
            f"발견 기술: {s.discovered_techs}/{s.total_techs}"
        )
