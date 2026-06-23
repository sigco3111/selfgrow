"""자가발전 문명 시뮬레이션 — Phase 0.

순수 규칙 기반 개체 50마리로 시작하는 경제/문명 시뮬레이션.
LLM 없이 유한 상태 머신 + 유전 알고리즘 + 시장 메커니즘으로
emergent behavior 관찰.
"""

from . import config
from .engine import SimulationEngine
from .metrics import MetricsCollector
from .visualizer import TerminalVisualizer

__all__ = ["config", "SimulationEngine", "MetricsCollector",
           "TerminalVisualizer"]
