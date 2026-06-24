"""실험 프레임워크 — 다중 실행 비교 및 통계 분석 (Phase 2.2)."""

from __future__ import annotations

import json
import math
import os
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

from . import config
from .engine import SimulationEngine
from .metrics import MetricsCollector, Snapshot


@dataclass
class ExperimentConfig:
    """실험 설정 — 다중 시드/틱/파라미터 오버라이드."""
    base_seed: int = 42
    trials: int = 10
    max_ticks: int = 500
    overrides: dict[str, object] = field(default_factory=dict)
    label: str = ""

    @classmethod
    def from_json(cls, path: str) -> ExperimentConfig:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return cls(**data)


@dataclass
class ExperimentResult:
    """단일 실험 조건의 실행 결과."""
    config: ExperimentConfig
    snapshots: list[Snapshot]
    survival_rates: list[float]
    final_populations: list[int]
    avg_final_gini: float = 0.0
    std_final_gini: float = 0.0
    avg_final_wealth: float = 0.0
    std_final_wealth: float = 0.0
    smart_survival: list[float] = field(default_factory=list)
    rule_survival: list[float] = field(default_factory=list)


class ExperimentRunner:
    """실험 실행기 — 다중 실행, 비교, 보고서 생성."""

    @staticmethod
    def _run_single(base_seed: int, max_ticks: int,
                    overrides: dict[str, object]) -> Snapshot:
        config.apply_overrides(overrides)
        engine = SimulationEngine(seed=base_seed)
        engine.running = True
        for _ in range(max_ticks):
            if not engine.running:
                break
            engine._step()
            alive = [e for e in engine.world.entities.values() if e.alive]
            if not alive:
                break
        engine.running = False
        snap = engine.metrics.latest()
        return snap if snap else Snapshot(
            tick=0, population=0, births=0, deaths=0, kill_count=0,
            avg_energy=0.0, avg_wealth=0.0, gini_coefficient=0.0,
            specialization_diversity=0.0, total_wealth=0.0, total_trades=0,
            trade_volume=0.0, total_taxes=0.0, prices={},
            discovered_techs=0, total_techs=0,
            inventory_distribution={}, world_resources={},
        )

    def run(self, exp_config: ExperimentConfig) -> ExperimentResult:
        snapshots: list[Snapshot] = []
        survival_rates: list[float] = []
        final_pops: list[int] = []
        smart_surv: list[float] = []
        rule_surv: list[float] = []

        for trial in range(exp_config.trials):
            seed = exp_config.base_seed + trial
            snap = self._run_single(seed, exp_config.max_ticks,
                                    exp_config.overrides)
            snapshots.append(snap)

            surv = snap.population / config.INITIAL_ENTITY_COUNT
            survival_rates.append(surv)
            final_pops.append(snap.population)

            total_smart = snap.smart_count + snap.rule_count
            if total_smart > 0:
                smart_surv.append(snap.smart_count / total_smart)
                rule_surv.append(snap.rule_count / total_smart)

        ginis = [s.gini_coefficient for s in snapshots]
        wealths = [s.avg_wealth for s in snapshots]

        return ExperimentResult(
            config=exp_config,
            snapshots=snapshots,
            survival_rates=survival_rates,
            final_populations=final_pops,
            avg_final_gini=sum(ginis) / max(1, len(ginis)),
            std_final_gini=math.sqrt(
                sum((g - sum(ginis) / max(1, len(ginis))) ** 2 for g in ginis)
                / max(1, len(ginis))
            ) if ginis else 0.0,
            avg_final_wealth=sum(wealths) / max(1, len(wealths)),
            std_final_wealth=math.sqrt(
                sum((w - sum(wealths) / max(1, len(wealths))) ** 2 for w in wealths)
                / max(1, len(wealths))
            ) if wealths else 0.0,
            smart_survival=smart_surv,
            rule_survival=rule_surv,
        )

    def compare(self, results: list[ExperimentResult]) -> dict:
        return {
            "total_trials": sum(r.config.trials for r in results),
            "conditions": [r.config.label or str(r.config.overrides)
                          for r in results],
            "avg_survival": [round(sum(r.survival_rates) / max(1, len(r.survival_rates)), 3)
                            for r in results],
            "avg_gini": [round(r.avg_final_gini, 4) for r in results],
            "avg_wealth": [round(r.avg_final_wealth, 2) for r in results],
            "smart_ratio": [
                round(sum(r.smart_survival) / max(1, len(r.smart_survival)), 3)
                if r.smart_survival else 0.0
                for r in results
            ],
        }

    def report(self, results: list[ExperimentResult]) -> str:
        comp = self.compare(results)
        lines = ["=== 실험 결과 보고서 ===", ""]
        for i, r in enumerate(results):
            label = comp["conditions"][i]
            lines.append(f"[조건 {i+1}] {label}")
            lines.append(f"  시행 횟수: {r.config.trials}")
            lines.append(f"  생존율: {comp['avg_survival'][i]*100:.1f}%")
            lines.append(f"  최종 인구 평균: {sum(r.final_populations)/max(1,len(r.final_populations)):.1f}")
            lines.append(f"  지니계수: {comp['avg_gini'][i]:.4f} ± {r.std_final_gini:.4f}")
            lines.append(f"  평균 부: {comp['avg_wealth'][i]:.2f} ± {r.std_final_wealth:.2f}")
            lines.append(f"  SmartBrain 비율: {comp['smart_ratio'][i]*100:.1f}%")
            lines.append("")
        return "\n".join(lines)


def run_experiment_file(exp_path: str) -> str:
    cfg = ExperimentConfig.from_json(exp_path)
    runner = ExperimentRunner()

    overrides_list = cfg.overrides
    param_name = ""
    param_values = []

    for key, value in list(overrides_list.items()):
        if isinstance(value, list):
            param_name = key
            param_values = value
            break

    results: list[ExperimentResult] = []
    if param_values:
        for val in param_values:
            trial_overrides = dict(overrides_list)
            trial_overrides[param_name] = val
            trial_cfg = ExperimentConfig(
                base_seed=cfg.base_seed,
                trials=cfg.trials,
                max_ticks=cfg.max_ticks,
                overrides={k: v for k, v in trial_overrides.items()
                          if not isinstance(v, list)},
                label=f"{param_name}={val}",
            )
            results.append(runner.run(trial_cfg))
    else:
        results.append(runner.run(cfg))

    report_text = runner.report(results)
    out_dir = os.path.dirname(exp_path) or "."
    out_path = os.path.join(out_dir, "experiment_report.txt")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(report_text)
    return report_text
