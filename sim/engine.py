"""시뮬레이션 엔진 — 메인 루프, 개체 생명주기, 이벤트 디스패치."""

from __future__ import annotations

import random
import time
from collections import deque
from dataclasses import dataclass
from typing import Optional

from . import config
from . import cultural
from . import events as evt
from . import faction_system
from . import messaging
from . import research
from . import season as sea
from .brain import create_brain
from .entity import Entity
from .knowledge import TechnologyTree
from .market import Market
from .metrics import MetricsCollector
from .trade_network import get_trade_network
from .world import World


@dataclass
class EngineState:
    """엔진 상태 요약."""
    tick: int
    population: int
    alive_count: int
    running: bool


class SimulationEngine:
    """시뮬레이션 메인 엔진 — 세계를 생성하고 틱을 실행."""

    def __init__(self, seed: int | None = None):
        self._seed = seed if seed is not None else config.SEED
        self._rng = config.create_rng(self._seed, "engine")
        self.world = World(seed=seed, rng=config.create_rng(self._seed, "world"))
        self.market = Market(rng=config.create_rng(self._seed, "market"))
        self._event_rng = config.create_rng(self._seed, "events")
        self.trade_network = get_trade_network()
        self.tech_tree = TechnologyTree()
        self.metrics = MetricsCollector()

        self.running = False
        self.tick_count = 0
        self.event_log: deque[dict] = deque(maxlen=10000)

        # 기술 발전 관련
        self._global_research_points: dict[str, float] = {}
        self._discovered_techs: set[str] = set()

        # 초기 개체 생성
        self._seed_entities()

    def _seed_entities(self) -> None:
        """초기 개체를 월드에 랜덤 배치."""
        spawnable = []
        for y in range(self.world.height):
            for x in range(self.world.width):
                tile = self.world.tile_at(x, y)
                if tile and tile.is_traversable():
                    spawnable.append((x, y))

        entity_rng = config.create_rng(self._seed, "entity")
        brain_rng = config.create_rng(self._seed, "brain")

        for _ in range(config.INITIAL_ENTITY_COUNT):
            if not spawnable:
                break
            x, y = self._rng.choice(spawnable)
            entity = Entity(x, y, rng=entity_rng)
            # 초기 인벤토리
            entity.inventory["food"] = self._rng.uniform(5, 10)
            entity.inventory["wood"] = self._rng.uniform(2, 5)
            entity.inventory["stone"] = self._rng.uniform(1, 3)

            # 초기 지식 (무작위 1개)
            available = self.tech_tree.get_available(self._discovered_techs)
            if available:
                starter = self._rng.choice(available)
                entity.knowledge.learn(starter.name)

            # 두뇌 할당 (RuleBasedBrain or SmartBrain)
            entity.brain = create_brain(entity, self.world, rng=brain_rng)

            eid = self.world.spawn_entity(entity)
            entity.eid = eid
            entity.name = f"E{eid:04d}"

    # ──────────────────────────────────────────
    # 메인 루프
    # ──────────────────────────────────────────
    def run(self, max_ticks: int = 1000, realtime: bool = False,
            on_tick=None) -> None:
        """시뮬레이션 실행."""
        self.running = True
        self.tick_count = 0

        for _ in range(max_ticks):
            if not self.running:
                break
            self._step()
            self.tick_count += 1

            if on_tick:
                on_tick(self)

            if realtime:
                time.sleep(config.TICK_INTERVAL_MS / 1000.0)

            # 멸종 검사
            alive = [e for e in self.world.entities.values() if e.alive]
            if not alive:
                self.running = False
                break

        self.running = False
        return self.state()

    def _step(self) -> None:
        """한 틱 실행."""
        # 0. 계절 계산
        current_season = sea.compute_season(self.world.tick)
        season_effects = sea.get_season_effects(current_season)

        # 1. 월드 업데이트 (자원 재생성, 계절 효과 적용)
        self.world.tick_update(regen_mult=season_effects.regen_mult)

        # 2. 시장 업데이트 (주문 에이징)
        self.market.tick_update()

        # 3. 랜덤 이벤트 처리
        event_logs = evt.process_events(self.world, rng=self._event_rng)
        for log in event_logs:
            log["tick"] = self.world.tick
            self._log_event(log)

        # 4. 개체 행동
        entities = list(self.world.entities.values())
        self._rng.shuffle(entities)  # 처리 순서 랜덤화

        for entity in entities:
            if not entity.alive:
                # 이벤트/기타 외부 요인으로 사망 — 사망 기록
                self.metrics.record_death()
                continue

            # 나이 먹기
            entity.age_update()

            if not entity.alive:
                self.metrics.record_death()
                continue

            # 계절 속도 보정
            entity._season_speed_mod = season_effects.speed_mult

            # 기술 효과 적용
            entity.apply_knowledge_effects()

            # 주거 기록 (매 틱 현재 타일에서 보낸 시간 증가)
            current_pos = (entity.x, entity.y)
            entity.residence_counter[current_pos] = entity.residence_counter.get(current_pos, 0) + 1
            entity.visited_tiles.append(current_pos)
            # 본거지 결정
            if entity.residence_counter:
                best_tile = max(entity.residence_counter, key=entity.residence_counter.get)
                if (entity.residence_counter[best_tile] >= config.TERRITORY_CLAIM_TICKS
                        and (entity.home_x, entity.home_y) != best_tile):
                    entity.home_x, entity.home_y = best_tile
                    self.world.claim_tile(best_tile[0], best_tile[1], entity.eid)

            # 기아
            if entity.energy <= 0:
                entity.alive = False
                self.metrics.record_death()
                self._log_event({
                    "tick": self.world.tick,
                    "type": "starvation",
                    "entity_id": entity.eid,
                    "entity_name": entity.name,
                })
                continue

            # 행동 결정 및 실행 (계절 에너지 비용 보정)
            before_wealth = entity.total_wealth()
            before_energy = entity.energy
            action = entity.decide_action(self.world, self.market)
            entity._season_energy_mult = season_effects.energy_mult
            entity._season_gather_mult = season_effects.gather_mult
            events = entity.execute_action(action, self.world, self.market)

            # SmartBrain 피드백: 행동 결과 점수 기록
            after_wealth = entity.total_wealth()
            after_energy = entity.energy
            outcome = ((after_wealth - before_wealth) * 0.5
                       + (after_energy - before_energy) * 0.02)
            entity.brain.feedback(entity, entity.last_action, outcome)

            # 이벤트 로그
            for ev in events:
                ev["tick"] = self.world.tick
                self._log_event(ev)
                if ev["type"] == "reproduce":
                    self.metrics.record_birth()
                if ev["type"] == "energy_depleted":
                    self.metrics.record_death()
                if ev.get("data", {}).get("target_alive") is False:
                    self.metrics.record_death()
                    self.metrics.record_kill()
                # 파벌 전투: 파벌 킬/로스 기록
                if ev["type"] == "combat":
                    target_alive = ev.get("data", {}).get("target_alive", True)
                    attacker_faction = self.world.faction_registry.get(
                        getattr(entity, "faction_id", -1), None)
                    if attacker_faction and not target_alive:
                        attacker_faction.total_kills += 1
                if ev["type"] == "equipment_broken":
                    pass  # 이미 entity에서 처리

        # 4. 사망 개체 정리
        dead_ids = [eid for eid, e in self.world.entities.items() if not e.alive]
        for eid in dead_ids:
            self.world.remove_entity(eid)

        # 5. SmartBrain 메시지 수집 및 배달
        self._process_brain_messages()

        # 6. 기술 연구 (글로벌)
        self._process_research()

        # 7. 파벌 생명주기
        self._process_factions()

        # 7.5. 무역 네트워크 처리
        trade_events = self.trade_network.process_trades(
            self.world, self.market, self._rng
        )
        for ev in trade_events:
            ev["tick"] = self.world.tick
            self._log_event(ev)

        # 8. 문화적 진화: 인접 개체 간 지식 전수
        self._cultural_transfer()

        # 9. 이데올로기 전파 (Phase 3.1)
        self._process_ideology()

        # 9. 주기적 스냅샷
        if self.world.tick % config.METRICS_SNAPSHOT_INTERVAL == 0:
            snap = self.metrics.snapshot(
                self.world.tick, self.world, self.market
            )
            snap.discovered_techs = self.tech_tree.discover_count()
            snap.total_techs = self.tech_tree.total_count()
            snap.current_season = current_season.value
            snap.season_name = sea.SEASON_NAMES_KR[current_season]
            snap.active_events = len(self.world.event_registry)
            total_buildings = sum(
                len(e.buildings) for e in self.world.entities.values() if e.alive
            )
            snap.total_buildings = total_buildings

    # ──────────────────────────────────────────
    # 하부 프로세스
    # ──────────────────────────────────────────
    def _process_brain_messages(self) -> None:
        messaging.process_brain_messages(self.world)

    def _process_research(self) -> None:
        research.process_research(
            self.world, self.tech_tree, self._rng,
            self._discovered_techs, self._log_event,
        )

    def _cultural_transfer(self) -> None:
        cultural.cultural_transfer(self.world, self._rng, self._log_event)

    def _process_factions(self) -> None:
        faction_system.process_factions(self.world, self._rng, self._log_event)

    def _process_ideology(self) -> None:
        from .ideology import process_ideology
        ideo_events = process_ideology(self.world, self._rng)
        for ev in ideo_events:
            ev["tick"] = self.world.tick
            self._log_event(ev)

    # ──────────────────────────────────────────
    # 이벤트 로그
    # ──────────────────────────────────────────
    def _log_event(self, event: dict) -> None:
        self.event_log.append(event)

    # ──────────────────────────────────────────
    # 상태 조회
    # ──────────────────────────────────────────
    def state(self) -> EngineState:
        alive = sum(1 for e in self.world.entities.values() if e.alive)
        return EngineState(
            tick=self.world.tick,
            population=len(self.world.entities),
            alive_count=alive,
            running=self.running,
        )

    def get_alive_entities(self) -> list[Entity]:
        return [e for e in self.world.entities.values() if e.alive]
