"""자가발전 문명 시뮬레이션 — 순수 규칙 기반.

유전 알고리즘 + 시장 메커니즘 + 듀얼 브레인 시스템(RuleBasedBrain/SmartBrain)으로
emergent behavior를 관찰하는 시뮬레이션.
**LLM/외부 AI는 영원히 사용하지 않습니다.**
"""

from . import config
from .brain import Brain, RuleBasedBrain, SmartBrain
from .engine import SimulationEngine
from .faction import Faction
from .metrics import MetricsCollector
from .visualizer import TerminalVisualizer

__all__ = ["config", "SimulationEngine", "MetricsCollector",
           "TerminalVisualizer", "Faction", "Brain",
           "RuleBasedBrain", "SmartBrain"]
