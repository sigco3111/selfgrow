"""시뮬레이션 엔진 — 메인 루프, 개체 생명주기, 이벤트 디스패치."""

from __future__ import annotations

import random
import time
from dataclasses import dataclass, field
from typing import Optional

from . import config
from .entity import Entity, EntityState
from .genome import Genome
from .knowledge import TechnologyTree
from .market import Market
from .metrics import MetricsCollector
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
        self.world = World(seed=seed)
        self.market = Market()
        self.tech_tree = TechnologyTree()
        self.metrics = MetricsCollector()

        self.running = False
        self.tick_count = 0
        self.event_log: list[dict] = []
        self._max_event_log = 10000  # 메모리 보호

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

        for _ in range(config.INITIAL_ENTITY_COUNT):
            if not spawnable:
                break
            x, y = random.choice(spawnable)
            entity = Entity(x, y)
            # 초기 인벤토리
            entity.inventory["food"] = random.uniform(5, 10)
            entity.inventory["wood"] = random.uniform(2, 5)
            entity.inventory["stone"] = random.uniform(1, 3)

            # 초기 지식 (무작위 1개)
            available = self.tech_tree.get_available(self._discovered_techs)
            if available:
                starter = random.choice(available)
                entity.knowledge.learn(starter.name)

            self.world.spawn_entity(entity)

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
        # 1. 월드 업데이트 (자원 재생성)
        self.world.tick_update()

        # 2. 시장 업데이트 (주문 에이징)
        self.market.tick_update()

        # 3. 개체 행동
        entities = list(self.world.entities.values())
        random.shuffle(entities)  # 처리 순서 랜덤화

        for entity in entities:
            if not entity.alive:
                continue

            # 나이 먹기
            entity.age_update()

            if not entity.alive:
                self.metrics.record_death()
                continue

            # 주거 기록 (매 틱 현재 타일에서 보낸 시간 증가)
            current_pos = (entity.x, entity.y)
            entity.residence_counter[current_pos] = entity.residence_counter.get(current_pos, 0) + 1
            if len(entity.visited_tiles) > config.HOME_SITE_MEMORY:
                entity.visited_tiles.pop(0)
            entity.visited_tiles.append(current_pos)
            # 본거지 결정
            if entity.residence_counter:
                best_tile = max(entity.residence_counter, key=entity.residence_counter.get)
                if (entity.residence_counter[best_tile] >= config.TERRITORY_CLAIM_TICKS
                        and (entity.home_x, entity.home_y) != best_tile):
                    entity.home_x, entity.home_y = best_tile
                    self.world.claim_tile(best_tile[0], best_tile[1], id(entity))

            # 기아
            if entity.energy <= 0:
                entity.alive = False
                self.metrics.record_death()
                self._log_event({
                    "tick": self.world.tick,
                    "type": "starvation",
                    "entity_id": id(entity),
                    "entity_name": entity.name,
                })
                continue

            # 행동 결정 및 실행
            action = entity.decide_action(self.world, self.market)
            events = entity.execute_action(action, self.world, self.market)

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

        # 4. 사망 개체 정리
        dead_ids = [eid for eid, e in self.world.entities.items() if not e.alive]
        for eid in dead_ids:
            self.world.remove_entity(eid)

        # 5. 기술 연구 (글로벌)
        self._process_research()

        # 6. 문화적 진화: 인접 개체 간 지식 전수
        self._cultural_transfer()

        # 7. 주기적 스냅샷
        if self.world.tick % config.METRICS_SNAPSHOT_INTERVAL == 0:
            snap = self.metrics.snapshot(
                self.world.tick, self.world, self.market
            )
            # 기술 정보 갱신
            snap.discovered_techs = self.tech_tree.discover_count()
            snap.total_techs = self.tech_tree.total_count()

    # ──────────────────────────────────────────
    # 하부 프로세스
    # ──────────────────────────────────────────
    def _process_research(self) -> None:
        """개체들이 연구 포인트를 생성하고 기술을 발견."""
        research_points = 0
        for entity in self.world.entities.values():
            if not entity.alive:
                continue
            # 혁신성과 지식 수에 비례해 연구 포인트 생성
            points = entity.genome.innovation_rate * 0.1 * (
                1 + entity.knowledge.count() * 0.2
            )
            research_points += points

        # 연구 포인트를 사용 가능한 기술에 분배
        available = self.tech_tree.get_available(self._discovered_techs)
        if available and research_points > 0:
            # 랜덤하게 하나 선택해 연구
            target = random.choice(available)
            if target.research(research_points):
                self._discovered_techs.add(target.name)
                self._log_event({
                    "tick": self.world.tick,
                    "type": "tech_discovery",
                    "data": {"tech": target.name,
                             "description": target.description},
                })

    def _cultural_transfer(self) -> None:
        """인접 개체 간 지식 전수 (문화적 진화)."""
        entities = list(self.world.entities.values())
        for entity in entities:
            if not entity.alive or entity.genome.sociability < 0.2:
                continue
            # 같은 타일 또는 인접 타일의 개체 찾기
            for other in entities:
                if (other is entity or not other.alive):
                    continue
                dist = abs(other.x - entity.x) + abs(other.y - entity.y)
                if dist <= 1:  # 인접 또는 동일 타일
                    transferred = entity.knowledge.share(
                        other.knowledge, entity.genome.sociability
                    )
                    for tech in transferred:
                        self._log_event({
                            "tick": self.world.tick,
                            "type": "knowledge_transfer",
                            "entity_id": id(entity),
                            "entity_name": entity.name,
                            "data": {"from": entity.name, "to": other.name,
                                     "tech": tech},
                        })

    # ──────────────────────────────────────────
    # 이벤트 로그
    # ──────────────────────────────────────────
    def _log_event(self, event: dict) -> None:
        if len(self.event_log) >= self._max_event_log:
            self.event_log.pop(0)
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
