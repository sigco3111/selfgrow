"""시뮬레이션 결과 내보내기 — CSV/JSON 익스포트."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .engine import SimulationEngine
    from .metrics import Snapshot


def export_snapshots_csv(snapshots: list[Snapshot], path: str) -> None:
    """스냅샷을 CSV 파일로 저장."""
    if not snapshots:
        return
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        fieldnames = [
            "tick", "population", "births", "deaths", "kill_count",
            "avg_energy", "avg_wealth", "gini_coefficient",
            "specialization_diversity", "total_wealth", "total_trades",
            "trade_volume", "total_taxes",
            "food_price", "wood_price", "stone_price", "iron_price", "gold_price",
            "discovered_techs", "total_techs",
            "smart_count", "rule_count",
            "smart_avg_wealth", "rule_avg_wealth",
            "smart_avg_energy", "rule_avg_energy",
            "smart_total_kills", "rule_total_kills",
            "smart_total_wealth", "rule_total_wealth",
            "faction_count", "avg_faction_size", "total_buildings",
            "current_season", "season_name", "active_events",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for s in snapshots:
            row = {
                "tick": s.tick,
                "population": s.population,
                "births": s.births,
                "deaths": s.deaths,
                "kill_count": s.kill_count,
                "avg_energy": s.avg_energy,
                "avg_wealth": s.avg_wealth,
                "gini_coefficient": s.gini_coefficient,
                "specialization_diversity": s.specialization_diversity,
                "total_wealth": s.total_wealth,
                "total_trades": s.total_trades,
                "trade_volume": s.trade_volume,
                "total_taxes": s.total_taxes,
                "food_price": s.prices.get("food", 0),
                "wood_price": s.prices.get("wood", 0),
                "stone_price": s.prices.get("stone", 0),
                "iron_price": s.prices.get("iron", 0),
                "gold_price": s.prices.get("gold", 0),
                "discovered_techs": s.discovered_techs,
                "total_techs": s.total_techs,
                "smart_count": s.smart_count,
                "rule_count": s.rule_count,
                "smart_avg_wealth": s.smart_avg_wealth,
                "rule_avg_wealth": s.rule_avg_wealth,
                "smart_avg_energy": s.smart_avg_energy,
                "rule_avg_energy": s.rule_avg_energy,
                "smart_total_kills": s.smart_total_kills,
                "rule_total_kills": s.rule_total_kills,
                "smart_total_wealth": s.smart_total_wealth,
                "rule_total_wealth": s.rule_total_wealth,
                "faction_count": s.faction_count,
                "avg_faction_size": s.avg_faction_size,
                "total_buildings": s.total_buildings,
                "current_season": s.current_season,
                "season_name": s.season_name,
                "active_events": s.active_events,
            }
            writer.writerow(row)


def export_snapshots_json(snapshots: list[Snapshot], path: str) -> None:
    """스냅샷을 JSON Lines로 저장."""
    if not snapshots:
        return
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for s in snapshots:
            data = {
                "tick": s.tick,
                "population": s.population,
                "births": s.births,
                "deaths": s.deaths,
                "kill_count": s.kill_count,
                "avg_energy": s.avg_energy,
                "avg_wealth": s.avg_wealth,
                "gini_coefficient": s.gini_coefficient,
                "specialization_diversity": s.specialization_diversity,
                "total_wealth": s.total_wealth,
                "total_trades": s.total_trades,
                "trade_volume": s.trade_volume,
                "total_taxes": s.total_taxes,
                "prices": s.prices,
                "discovered_techs": s.discovered_techs,
                "total_techs": s.total_techs,
                "smart_count": s.smart_count,
                "rule_count": s.rule_count,
                "smart_avg_wealth": s.smart_avg_wealth,
                "rule_avg_wealth": s.rule_avg_wealth,
                "smart_avg_energy": s.smart_avg_energy,
                "rule_avg_energy": s.rule_avg_energy,
                "smart_total_kills": s.smart_total_kills,
                "rule_total_kills": s.rule_total_kills,
                "smart_total_wealth": s.smart_total_wealth,
                "rule_total_wealth": s.rule_total_wealth,
                "faction_count": s.faction_count,
                "avg_faction_size": s.avg_faction_size,
                "total_buildings": s.total_buildings,
                "current_season": s.current_season,
                "season_name": s.season_name,
                "active_events": s.active_events,
            }
            f.write(json.dumps(data, ensure_ascii=False) + "\n")


def export_event_log(events: list[dict], path: str) -> None:
    """이벤트 로그를 JSON Lines로 저장."""
    if not events:
        return
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for ev in events:
            f.write(json.dumps(ev, ensure_ascii=False) + "\n")


def export_prices_csv(snapshots: list[Snapshot], path: str) -> None:
    """가격 시계열을 CSV로 저장."""
    if not snapshots:
        return
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["tick", "food", "wood", "stone", "iron", "gold"])
        for s in snapshots:
            writer.writerow([
                s.tick,
                s.prices.get("food", 0),
                s.prices.get("wood", 0),
                s.prices.get("stone", 0),
                s.prices.get("iron", 0),
                s.prices.get("gold", 0),
            ])


def export_metadata_json(engine: SimulationEngine, path: str) -> None:
    """메타데이터(JSON) 저장: 시드, 설정, 실행 시간 등."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    from . import config
    data = {
        "seed": engine._seed,
        "tick_count": engine.tick_count,
        "config": {
            "WORLD_WIDTH": config.WORLD_WIDTH,
            "WORLD_HEIGHT": config.WORLD_HEIGHT,
            "INITIAL_ENTITY_COUNT": config.INITIAL_ENTITY_COUNT,
            "SMART_BRAIN_RATIO": config.SMART_BRAIN_RATIO,
            "FACTION_ENABLED": config.FACTION_ENABLED,
            "DIPLOMACY_ENABLED": config.DIPLOMACY_ENABLED,
        },
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def export_all(engine: SimulationEngine, path: str, fmt: str = "csv") -> None:
    """전체 내보내기: 스냅샷, 이벤트, 가격, 메타데이터."""
    export_dir = Path(path)
    export_dir.mkdir(parents=True, exist_ok=True)

    snapshots = engine.metrics.snapshots

    if fmt == "csv":
        export_snapshots_csv(snapshots, str(export_dir / "snapshots.csv"))
    elif fmt == "json":
        export_snapshots_json(snapshots, str(export_dir / "snapshots.jsonl"))
    else:
        raise ValueError(f"Unknown format: {fmt}")

    export_event_log(engine.event_log, str(export_dir / "events.jsonl"))
    export_prices_csv(snapshots, str(export_dir / "prices.csv"))
    export_metadata_json(engine, str(export_dir / "metadata.json"))