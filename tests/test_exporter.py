"""내보내기 시스템 단위 테스트."""

from __future__ import annotations

import csv
import json
import tempfile
from pathlib import Path

from sim.exporter import export_snapshots_csv, export_snapshots_json
from sim.metrics import Snapshot


def _make_snapshots(n: int = 3) -> list[Snapshot]:
    """테스트용 스냅샷 n개 생성."""
    snapshots = []
    for i in range(n):
        s = Snapshot(
            tick=i,
            population=40 + i,
            births=i,
            deaths=0,
            kill_count=0,
            avg_energy=80.0 + i,
            avg_wealth=100.0 + i * 10,
            gini_coefficient=0.3,
            specialization_diversity=0.8,
            total_wealth=4000 + i * 100,
            total_trades=0,
            trade_volume=0,
            total_taxes=0,
            prices={"food": 1.0, "wood": 1.0, "stone": 1.0, "iron": 1.0, "gold": 1.0},
            discovered_techs=0,
            total_techs=0,
            inventory_distribution={},
            world_resources={},
        )
        snapshots.append(s)
    return snapshots


def test_export_csv_writes_file():
    """CSV 내보내기가 파일을 생성함."""
    with tempfile.TemporaryDirectory() as tmp:
        path = str(Path(tmp) / "out.csv")
        export_snapshots_csv(_make_snapshots(), path)
        assert Path(path).exists()


def test_export_csv_has_header():
    """CSV 파일에 헤더가 포함됨."""
    with tempfile.TemporaryDirectory() as tmp:
        path = str(Path(tmp) / "out.csv")
        export_snapshots_csv(_make_snapshots(2), path)
        with open(path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            assert reader.fieldnames is not None
            assert "tick" in reader.fieldnames
            assert "population" in reader.fieldnames


def test_export_csv_row_count():
    """CSV 행 수가 스냅샷 수와 일치함."""
    with tempfile.TemporaryDirectory() as tmp:
        path = str(Path(tmp) / "out.csv")
        snapshots = _make_snapshots(5)
        export_snapshots_csv(snapshots, path)
        with open(path, encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        assert len(rows) == 5


def test_export_csv_empty_snapshots():
    """빈 스냅샷 리스트는 파일을 생성하지 않음."""
    with tempfile.TemporaryDirectory() as tmp:
        path = str(Path(tmp) / "out.csv")
        export_snapshots_csv([], path)
        assert not Path(path).exists()


def test_export_json_writes_file():
    """JSON 내보내기가 파일을 생성함."""
    with tempfile.TemporaryDirectory() as tmp:
        path = str(Path(tmp) / "out.json")
        export_snapshots_json(_make_snapshots(), path)
        assert Path(path).exists()


def test_export_json_valid_array():
    """JSON 파일이 유효한 JSON Lines를 포함함."""
    with tempfile.TemporaryDirectory() as tmp:
        path = str(Path(tmp) / "out.json")
        export_snapshots_json(_make_snapshots(3), path)
        with open(path, encoding="utf-8") as f:
            lines = [json.loads(line) for line in f if line.strip()]
        assert isinstance(lines, list)
        assert len(lines) == 3


def test_export_json_tick_values():
    """JSON에 올바른 tick 값이 저장됨."""
    with tempfile.TemporaryDirectory() as tmp:
        path = str(Path(tmp) / "out.json")
        export_snapshots_json(_make_snapshots(4), path)
        with open(path, encoding="utf-8") as f:
            lines = [json.loads(line) for line in f if line.strip()]
        ticks = [d["tick"] for d in lines]
        assert ticks == [0, 1, 2, 3]
