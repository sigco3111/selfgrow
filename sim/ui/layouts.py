"""레이아웃 매니저 — 다양한 레이아웃 옵션 지원."""

from __future__ import annotations

from enum import Enum, auto
from typing import TYPE_CHECKING

from rich.layout import Layout
from rich.panel import Panel
from rich.text import Text

from .charts import render_timeseries_panel
from .event_log import render_event_log_panel
from .entity_view import render_entity_detail_panel, render_entity_list
from .map_overlay import render_map_with_overlay, render_faction_legend, render_minimap
from .tech_tree import render_tech_tree_panel
from .resource_heatmap import render_resource_heatmap
from .faction_graph import render_faction_graph

if TYPE_CHECKING:
    from ..engine import SimulationEngine
    from ..entity import Entity


class LayoutMode(Enum):
    """레이아웃 모드 열거형."""
    DEFAULT = auto()    # 기본 레이아웃
    CHART = auto()      # 차트 중심
    FACTION = auto()    # 파벌 중심
    ENTITY = auto()     # 개체 중심
    TECH = auto()       # 기술 트리 + 자원 히트맵


class LayoutManager:
    """레이아웃 매니저 — 다양한 레이아웃 모드 지원.
    
    Attributes:
        current_mode: 현재 레이아웃 모드
        selected_entity: 선택된 개체 (개체 중심 모드용)
        selected_faction_id: 선택된 파벌 ID (파벌 중심 모드용)
        event_filter: 이벤트 필터 카테고리
    """
    
    def __init__(self, initial_mode: LayoutMode = LayoutMode.DEFAULT):
        """레이아웃 매니저 초기화.
        
        Args:
            initial_mode: 초기 레이아웃 모드
        """
        self.current_mode = initial_mode
        self.selected_entity: Entity | None = None
        self.selected_faction_id: int | None = None
        self.event_filter: str | None = None
    
    def set_mode(self, mode: LayoutMode) -> None:
        """레이아웃 모드 변경."""
        self.current_mode = mode
    
    def set_selected_entity(self, entity: Entity | None) -> None:
        """선택된 개체 설정."""
        self.selected_entity = entity
    
    def set_selected_faction(self, faction_id: int | None) -> None:
        """선택된 파벌 설정."""
        self.selected_faction_id = faction_id
    
    def set_event_filter(self, category: str | None) -> None:
        """이벤트 필터 설정."""
        self.event_filter = category
    
    def render(self, engine: SimulationEngine) -> Layout:
        """현재 모드에 따라 레이아웃 렌더링.

        Args:
            engine: 시뮬레이션 엔진

        Returns:
            Rich Layout 객체
        """
        if self.current_mode == LayoutMode.CHART:
            return self._render_chart_layout(engine)
        elif self.current_mode == LayoutMode.FACTION:
            return self._render_faction_layout(engine)
        elif self.current_mode == LayoutMode.ENTITY:
            return self._render_entity_layout(engine)
        elif self.current_mode == LayoutMode.TECH:
            return self._render_tech_layout(engine)
        else:
            return self._render_default_layout(engine)
    
    def _render_header(self, engine: SimulationEngine) -> Panel:
        """헤더 패널 렌더링."""
        state = engine.state()
        tick_str = f"틱 {state.tick:05d}"
        pop_str = f"생존 {state.alive_count}/{state.population}"
        
        # 모드 표시
        mode_names = {
            LayoutMode.DEFAULT: "기본",
            LayoutMode.CHART: "차트",
            LayoutMode.FACTION: "파벌",
            LayoutMode.ENTITY: "개체",
            LayoutMode.TECH: "기술",
        }
        mode_str = mode_names.get(self.current_mode, "기본")
        
        title = Text.assemble(
            (">> ", "cp.cyan"),
            ("자가발전 문명", "cp.magenta"),
            (f" [{mode_str}]", "cp.amber"),
        )
        status = Text.assemble(
            (tick_str, "cp.cyan"),
            ("  |  ", "cp.dim"),
            (pop_str, "cp.green"),
        )
        
        inner = Text.assemble(title, "\n", status)
        return Panel(
            inner,
            title="[cp.magenta]⚡ Header[/]",
            border_style="cp.magenta",
            padding=(0, 1),
        )
    
    def _render_default_layout(self, engine: SimulationEngine) -> Layout:
        """기본 레이아웃 (현재 구조 유지)."""
        layout = Layout()
        
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="body"),
            Layout(name="footer", size=12),
        )
        
        layout["header"].update(self._render_header(engine))
        layout["body"].split_row(
            Layout(name="map", ratio=3),
            Layout(name="panel", ratio=2),
        )
        layout["map"].update(render_map_with_overlay(engine.world))
        layout["panel"].update(self._render_info_panel(engine))
        layout["footer"].update(render_event_log_panel(
            engine.event_log,
            filter_category=self.event_filter,
        ))
        
        return layout
    
    def _render_chart_layout(self, engine: SimulationEngine) -> Layout:
        """차트 중심 레이아웃 — 시계열 차트 크게."""
        layout = Layout()
        
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="body"),
            Layout(name="footer", size=10),
        )
        
        layout["header"].update(self._render_header(engine))
        layout["body"].split_row(
            Layout(name="map", ratio=2),
            Layout(name="charts", ratio=3),
        )
        layout["map"].update(render_map_with_overlay(engine.world))
        layout["charts"].update(render_timeseries_panel(engine.metrics))
        layout["footer"].update(render_event_log_panel(
            engine.event_log,
            filter_category=self.event_filter,
        ))
        
        return layout
    
    def _render_faction_layout(self, engine: SimulationEngine) -> Layout:
        """파벌 중심 레이아웃 — 파벌 정보 크게."""
        layout = Layout()
        
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="body"),
            Layout(name="footer", size=10),
        )
        
        layout["header"].update(self._render_header(engine))
        layout["body"].split_row(
            Layout(name="map", ratio=2),
            Layout(name="faction_info", ratio=3),
        )
        layout["map"].update(render_map_with_overlay(
            engine.world,
            highlight_faction_id=self.selected_faction_id,
        ))
        layout["faction_info"].update(self._render_faction_panel(engine))
        layout["footer"].update(render_event_log_panel(
            engine.event_log,
            filter_category="전투",  # 파벌 모드에서는 전투 이벤트 우선
        ))
        
        return layout
    
    def _render_entity_layout(self, engine: SimulationEngine) -> Layout:
        """개체 중심 레이아웃 — 선택 개체 상세 정보 크게."""
        layout = Layout()
        
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="body"),
            Layout(name="footer", size=10),
        )
        
        layout["header"].update(self._render_header(engine))
        layout["body"].split_row(
            Layout(name="map", ratio=2),
            Layout(name="entity_detail", ratio=3),
        )
        layout["map"].update(render_map_with_overlay(
            engine.world,
            highlight_entity=self.selected_entity,
        ))
        
        # 개체 상세 정보 또는 개체 목록 표시
        if self.selected_entity:
            layout["entity_detail"].update(
                render_entity_detail_panel(self.selected_entity)
            )
        else:
            alive_entities = [e for e in engine.world.entities.values() if e.alive]
            layout["entity_detail"].update(
                render_entity_list(alive_entities)
            )
        
        layout["footer"].update(render_event_log_panel(
            engine.event_log,
            filter_category=self.event_filter,
        ))

        return layout

    def _render_tech_layout(self, engine: SimulationEngine) -> Layout:
        """기술 트리 + 자원 히트맵 레이아웃."""
        layout = Layout()

        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="body"),
            Layout(name="footer", size=10),
        )

        layout["header"].update(self._render_header(engine))
        layout["body"].split_row(
            Layout(name="tech_tree", ratio=2),
            Layout(name="heatmap", ratio=1),
        )

        alive = [e for e in engine.world.entities.values() if e.alive]
        known: set[str] = set()
        for e in alive:
            known.update(e.knowledge.known)

        layout["tech_tree"].update(
            render_tech_tree_panel(engine.tech_tree, known_techs=known)
        )
        layout["heatmap"].update(
            render_resource_heatmap(engine.world, resource_type="food")
        )
        layout["footer"].update(render_event_log_panel(
            engine.event_log,
            filter_category=self.event_filter,
        ))

        return layout

    def _render_info_panel(self, engine: SimulationEngine) -> Panel:
        """기본 정보 패널 렌더링 (기존 visualizer.py의 _render_info_panel 참고)."""
        from ..ui import charts
        
        # 시계열 차트 패널 통합
        return charts.render_timeseries_panel(engine.metrics)
    
    def _render_faction_panel(self, engine: SimulationEngine) -> Panel:
        """파벌 정보 패널 렌더링."""
        from rich.table import Table
        
        faction_reg = engine.world.faction_registry
        
        if not faction_reg:
            return Panel(
                Text("(파벌 없음)", style="cp.dim"),
                title="[cp.red]🔥 파벌 정보[/]",
                border_style="cp.dim",
            )
        
        table = Table.grid(padding=(0, 2))
        table.add_column(style="cp.dim", width=14)
        table.add_column(style="cp.text")
        
        table.add_row("파벌 수", f"{len(faction_reg)}")
        table.add_row("[cp.dim]─" * 14 + "[/]", "")
        
        for fid, faction in sorted(faction_reg.items()):
            color = faction.color
            leader = engine.world.entities.get(faction.leader_id)
            leader_name = leader.name if leader else "?"
            
            table.add_row(
                f"[{color}]{faction.name}[/]",
                f"n={faction.member_count} k={faction.total_kills}",
            )
            table.add_row(
                "  지도자",
                f"{leader_name}",
            )
            table.add_row(
                "  결속력",
                f"{faction.cohesion:.2f}",
            )
            if faction.wars:
                table.add_row(
                    "  [cp.red]전쟁[/]",
                    f"[cp.red]{len(faction.wars)}개국[/]",
                )
            table.add_row("", "")
        
        return Panel(
            table,
            title="[cp.red]🔥 파벌 정보[/]",
            border_style="cp.red",
            padding=(0, 1),
        )
