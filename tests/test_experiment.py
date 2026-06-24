"""실험 프레임워크 단위 테스트."""

from __future__ import annotations

import tempfile
from pathlib import Path

from sim.experiment import ExperimentConfig, ExperimentResult, ExperimentRunner


def test_experiment_config_defaults():
    """ExperimentConfig 기본값 확인."""
    cfg = ExperimentConfig()
    assert cfg.base_seed == 42
    assert cfg.trials == 10
    assert cfg.max_ticks == 500
    assert cfg.overrides == {}
    assert cfg.label == ""


def test_experiment_config_from_json():
    """ExperimentConfig를 JSON에서 로드."""
    with tempfile.TemporaryDirectory() as tmp:
        path = str(Path(tmp) / "exp.json")
        Path(path).write_text(
            '{"base_seed": 7, "trials": 3, "max_ticks": 100, '
            '"overrides": {"FOOD_REGEN": 0.1}, "label": "test"}',
            encoding="utf-8",
        )
        cfg = ExperimentConfig.from_json(path)
        assert cfg.base_seed == 7
        assert cfg.trials == 3
        assert cfg.max_ticks == 100
        assert cfg.overrides == {"FOOD_REGEN": 0.1}
        assert cfg.label == "test"


def test_experiment_result_fields():
    """ExperimentResult 필드 존재 확인."""
    result = ExperimentResult(
        config=ExperimentConfig(),
        snapshots=[],
        survival_rates=[],
        final_populations=[],
    )
    assert hasattr(result, "avg_final_gini")
    assert hasattr(result, "std_final_gini")
    assert hasattr(result, "smart_survival")
    assert result.avg_final_gini == 0.0


def test_experiment_runner_single_run():
    """ExperimentRunner가 단일 실행을 수행함."""
    runner = ExperimentRunner()
    cfg = ExperimentConfig(base_seed=42, trials=1, max_ticks=50)
    result = runner.run(cfg)
    assert result.config.trials == 1
    assert len(result.survival_rates) == 1
    assert len(result.final_populations) == 1
    assert result.survival_rates[0] >= 0.0


def test_experiment_runner_multiple_trials():
    """ExperimentRunner가 다중 실행을 수행함."""
    runner = ExperimentRunner()
    cfg = ExperimentConfig(base_seed=42, trials=3, max_ticks=50)
    result = runner.run(cfg)
    assert len(result.survival_rates) == 3
    assert len(result.final_populations) == 3
    assert result.avg_final_gini >= 0.0


def test_experiment_compare():
    """compare()가 여러 결과를 비교함."""
    runner = ExperimentRunner()
    cfg1 = ExperimentConfig(base_seed=42, trials=2, max_ticks=30, label="A")
    cfg2 = ExperimentConfig(base_seed=99, trials=2, max_ticks=30, label="B")
    r1 = runner.run(cfg1)
    r2 = runner.run(cfg2)
    comp = runner.compare([r1, r2])
    assert comp["total_trials"] == 4
    assert len(comp["conditions"]) == 2
    assert "A" in comp["conditions"]
    assert "B" in comp["conditions"]


def test_experiment_report():
    """report()가 텍스트 보고서를 생성함."""
    runner = ExperimentRunner()
    cfg = ExperimentConfig(base_seed=42, trials=1, max_ticks=30, label="test")
    result = runner.run(cfg)
    report = runner.report([result])
    assert isinstance(report, str)
    assert "실험 결과 보고서" in report
    assert "test" in report
