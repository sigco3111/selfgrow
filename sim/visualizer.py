"""웜 컴포트 TUI -- Rich 기반 실시간 시뮬레이션 시각화 (저채도 웜톤 팔레트)."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

from rich.align import Align
from rich.box import HEAVY, ROUNDED
from rich.console import Console, Group
from rich.layout import Layout
from rich.panel import Panel
from rich.style import Style
from rich.table import Table
from rich.text import Text
from rich.theme import Theme

from . import config
from . import season as sea
from .metrics import MetricsCollector
from .ideology import ideology_summary

# 새 UI 모듈 임포트
from .ui import (
    render_timeseries_panel,
    render_event_log_panel,
    render_entity_detail_panel,
    render_map_with_overlay,
    LayoutManager,
    LayoutMode,
)

if TYPE_CHECKING:
    from .engine import SimulationEngine
    from .entity import Entity


# -- Force UTF-8 on Windows cp949 terminals --
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


# ----------------------------------------------
# Warm Comfort Color Theme (눈에 편안한 저채도 웜톤 팔레트)
# ----------------------------------------------
COMFORT_THEME = Theme(
    {
        "cp.magenta": "#cba6f7",   # soft lavender  (was bold #ff00ff)
        "cp.cyan": "#89dceb",      # soft sky       (was bold #00ffff)
        "cp.green": "#a6e3a1",     # soft green     (was bold #00ff41)
        "cp.amber": "#fab387",     # warm peach     (was bold #ffb000)
        "cp.red": "#f38ba8",       # soft coral     (was bold #ff003c)
        "cp.blue": "#89b4fa",      # soft blue      (was bold #0088ff)
        "cp.purple": "#b4befe",    # soft periwinkle (was bold #aa00ff)
        "cp.dim": "#585b70",       # muted warm gray (was #555555)
        "cp.text": "#cdd6f4",      # off-white      (was #c0c0c0)
        "cp.white": "#f5e0dc",     # warm white     (was bold #ffffff)
        "cp.pink": "#f5c2e7",      # soft pink      (was #ff66aa)
    }
)

console = Console(
    theme=COMFORT_THEME,
    legacy_windows=False,
    force_terminal=True,
    highlight=False,
)

# -- Entity symbols (ASCII-safe for cp949) --
SYM = {
    "HD": "#",
    "DB": "%",
    "SG": "o",
    "HR": "+",
    "SK": "x",
    "ST": "*",
    "SW": "@",
    "HM": "&",
    "HT": "H",
    "AR": "->",
}

# -- Specialization -> neon color mapping --
SPEC_STYLES: dict[str, str] = {
    "farmer": "cp.green",
    "miner": "cp.amber",
    "merchant": "cp.purple",
    "warrior": "cp.red",
    "crafter": "cp.blue",
    "explorer": "cp.cyan",
    "general": "cp.text",
}


class TerminalVisualizer:
    """웜 컴포트 TUI 시각화 -- Rich Layout 기반 (저채도 웜톤 팔레트)."""

    def __init__(self, engine: SimulationEngine, layout_mode: str = "default"):
        """시각화 초기화.
        
        Args:
            engine: 시뮬레이션 엔진
            layout_mode: 레이아웃 모드 ("default", "chart", "faction", "entity")
        """
        self.engine = engine
        self.last_tick = -1
        
        # 레이아웃 매니저 초기화
        mode_map = {
            "default": LayoutMode.DEFAULT,
            "chart": LayoutMode.CHART,
            "faction": LayoutMode.FACTION,
            "entity": LayoutMode.ENTITY,
            "tech": LayoutMode.TECH,
        }
        self.layout_manager = LayoutManager(
            initial_mode=mode_map.get(layout_mode, LayoutMode.DEFAULT)
        )

    # ------------------------------------------
    # Main render -- returns a Layout
    # ------------------------------------------
    def render(self) -> Layout:
        """한 프레임을 Layout으로 렌더링 (Live.update()용)."""
        return self.layout_manager.render(self.engine)

    # ------------------------------------------
    # Final Summary
    # ------------------------------------------
    def render_final_summary(self, metrics: MetricsCollector) -> None:
        """시뮬레이션 종료 후 최종 통계 (사이버펑크 스타일)."""
        snap = metrics.latest()
        if snap is None:
            return

        # Header
        console.print()
        header = Panel(
            Align.center(
                Text.assemble(
                    ("⚡ ", "cp.cyan"),
                    ("시뮬레이션 종료", "cp.magenta"),
                    (" ⚡", "cp.cyan"),
                )
            ),
            box=HEAVY,
            border_style="cp.magenta",
        )
        console.print(header)

        # Stats grid
        grid = Table.grid(padding=(0, 4))
        grid.add_column(style="cp.dim", width=20)
        grid.add_column(style="cp.text")

        grid.add_section()
        grid.add_row("[cp.cyan]─" * 35 + "[/]", "")
        grid.add_row("[cp.cyan]인구 통계[/]", "")
        grid.add_row("[cp.cyan]─" * 35 + "[/]", "")
        grid.add_row("총 틱", f"{snap.tick}")
        grid.add_row("최종 인구", f"{snap.population}")
        grid.add_row("총 출생", f"[cp.green]{snap.births}[/]")
        grid.add_row("총 사망", f"[cp.red]{snap.deaths}[/]")
        grid.add_row("전투 사망", f"[cp.red]{snap.kill_count}[/]")

        grid.add_section()
        grid.add_row("[cp.amber]─" * 35 + "[/]", "")
        grid.add_row("[cp.amber]경제 지표[/]", "")
        grid.add_row("[cp.amber]─" * 35 + "[/]", "")
        grid.add_row("지니계수", f"{snap.gini_coefficient:.4f}")
        grid.add_row("분업지수", f"{snap.specialization_diversity:.4f}")
        grid.add_row("평균 부", f"{snap.avg_wealth:.2f}")
        grid.add_row("총 거래량", f"{snap.trade_volume:.2f}")
        grid.add_row("총 세금", f"{snap.total_taxes:.2f}")

        grid.add_section()
        grid.add_row("[cp.green]─" * 35 + "[/]", "")
        grid.add_row("[cp.green]최종 가격[/]", "")
        grid.add_row("[cp.green]─" * 35 + "[/]", "")
        for rtype, price in snap.prices.items():
            grid.add_row(f"  {rtype}", f"{price:.2f}")

        # Tech
        tech_tree = self.engine.tech_tree
        grid.add_section()
        grid.add_row("[cp.cyan]─" * 35 + "[/]", "")
        grid.add_row("[cp.cyan]기술[/]", "")
        grid.add_row("[cp.cyan]─" * 35 + "[/]", "")
        grid.add_row(
            "발견",
            f"[cp.cyan]{tech_tree.discover_count()}[/][cp.dim]/[/][cp.cyan]{tech_tree.total_count()}[/]",
        )
        for tech in tech_tree.get_discovered():
            grid.add_row(f"  {SYM['ST']}", f"[cp.green]{tech.name}[/]")

        # Brain Comparison
        grid.add_section()
        grid.add_row("[cp.cyan]─" * 35 + "[/]", "")
        grid.add_row("[cp.cyan]두뇌 비교 (실험)[/]", "")
        grid.add_row("[cp.cyan]─" * 35 + "[/]", "")
        if snap.population > 0:
            total_brain = snap.smart_count + snap.rule_count
            def safe_pct(val):
                return f"{val / total_brain * 100:.1f}%" if total_brain > 0 else "N/A"
            grid.add_row("", "")
            grid.add_row("[cp.cyan]SmartBrain[/]", f"{snap.smart_count}명 ({safe_pct(snap.smart_count)})")
            grid.add_row("  평균 부", f"[cp.green]{snap.smart_avg_wealth:.2f}[/]")
            grid.add_row("  평균 에너지", f"{snap.smart_avg_energy:.1f}")
            grid.add_row("  총 킬", f"{snap.smart_total_kills}")
            grid.add_row("  1인당 킬", f"{snap.smart_total_kills / max(1, snap.smart_count):.2f}")
            if snap.smart_count > 0:
                grid.add_row("  총 자산", f"{snap.smart_total_wealth:.2f}")
            grid.add_row("", "")
            grid.add_row("[cp.text]RuleBasedBrain[/]", f"{snap.rule_count}명 ({safe_pct(snap.rule_count)})")
            grid.add_row("  평균 부", f"{snap.rule_avg_wealth:.2f}")
            grid.add_row("  평균 에너지", f"{snap.rule_avg_energy:.1f}")
            grid.add_row("  총 킬", f"{snap.rule_total_kills}")
            grid.add_row("  1인당 킬", f"{snap.rule_total_kills / max(1, snap.rule_count):.2f}")
            if snap.rule_count > 0:
                grid.add_row("  총 자산", f"{snap.rule_total_wealth:.2f}")
            grid.add_row("", "")
            wealth_gap = snap.smart_avg_wealth - snap.rule_avg_wealth
            gap_s = "cp.green" if wealth_gap >= 0 else "cp.red"
            grid.add_row("  [cp.cyan]부 격차[/]", f"[{gap_s}]{wealth_gap:+.2f}[/]")

        # Specialization
        spec_counts: dict[str, int] = {}
        for e in self.engine.world.entities.values():
            if e.alive:
                spec_counts[e.genome.specialization] = (
                    spec_counts.get(e.genome.specialization, 0) + 1
                )
        grid.add_section()
        grid.add_row("[cp.purple]─" * 35 + "[/]", "")
        grid.add_row("[cp.purple]직업 분포[/]", "")
        grid.add_row("[cp.purple]─" * 35 + "[/]", "")
        for spec, count in sorted(spec_counts.items()):
            bar = "█" * count
            st = SPEC_STYLES.get(spec, "cp.text")
            grid.add_row(f"  [{st}]{spec}[/]", f"{count} {bar}")

        console.print(Panel(grid, box=ROUNDED, border_style="cp.cyan"))
        console.print()
