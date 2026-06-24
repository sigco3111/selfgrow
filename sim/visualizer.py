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

# -- Biome -> tile style mapping --
TILE_STYLES: dict[str, str] = {
    "plain": "cp.green",
    "forest": "#8bd5ca",      # soft teal (was harsh "green")
    "mountain": "cp.white",
    "water": "cp.blue",
    "desert": "cp.amber",
    "hill": "#eed49f",        # soft warm yellow (was harsh "yellow")
    "swamp": "cp.dim",
}

TILE_CHARS: dict[str, str] = {
    "plain": ".",
    "forest": "T",
    "mountain": "^",
    "water": "~",
    "desert": ",",
    "hill": "n",
    "swamp": "=",
}


class TerminalVisualizer:
    """웜 컴포트 TUI 시각화 -- Rich Layout 기반 (저채도 웜톤 팔레트)."""

    def __init__(self, engine: SimulationEngine):
        self.engine = engine
        self.last_tick = -1

    # ------------------------------------------
    # Main render -- returns a Layout
    # ------------------------------------------
    def render(self) -> Layout:
        """한 프레임을 Layout으로 렌더링 (Live.update()용)."""
        state = self.engine.state()
        layout = Layout()

        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="body"),
            Layout(name="footer", size=12),
        )

        layout["header"].update(self._render_header(state))
        layout["body"].split_row(
            Layout(name="map", ratio=3),
            Layout(name="panel", ratio=2),
        )
        layout["map"].update(self._render_map_panel())
        layout["panel"].update(self._render_info_panel())
        layout["footer"].update(self._render_events_panel())

        return layout

    # ------------------------------------------
    # Header
    # ------------------------------------------
    def _render_header(self, state) -> Panel:
        tick_str = f"틱 {state.tick:05d}"
        pop_str = f"생존 {state.alive_count}/{state.population}"

        snap = self.engine.metrics.latest()
        season_str = ""
        if snap:
            season_emoji = {0: "\ud83c\udf38", 1: "\u2600\ufe0f", 2: "\ud83c\udf42", 3: "\u2744\ufe0f"}
            se = season_emoji.get(snap.current_season, "")
            season_str = f"{se} {snap.season_name}"

        title = Text.assemble(
            (">> ", "cp.cyan"),
            ("자가발전 문명", "cp.magenta"),
            ("  v0.1", "cp.dim"),
        )
        status = Text.assemble(
            (tick_str, "cp.cyan"),
            ("  |  ", "cp.dim"),
            (pop_str, "cp.green"),
        )
        if season_str:
            status.append(Text.assemble(
                ("  |  ", "cp.dim"),
                (season_str, "cp.amber"),
            ))
        bar = Text.assemble(
            (" ", "cp.dim"),
        )
        inner = Text.assemble(title, "\n", status)
        return Panel(
            Align.center(inner),
            box=HEAVY,
            border_style="cp.magenta",
            padding=(0, 1),
        )

    # ------------------------------------------
    # Map Panel
    # ------------------------------------------
    def _render_map_panel(self) -> Panel:
        """월드 맵을 네온 그린 스타일로 렌더링."""
        world = self.engine.world
        map_text = Text()

        entity_positions: dict[tuple[int, int], list[Entity]] = {}
        for entity in world.entities.values():
            if entity.alive:
                entity_positions.setdefault((entity.x, entity.y), []).append(entity)

        for y in range(world.height):
            for x in range(world.width):
                tile = world.tile_at(x, y)
                if not tile:
                    map_text.append(" ", "cp.dim")
                    continue

                is_claimed = (x, y) in world.tile_claims
                entities_at = entity_positions.get((x, y), [])

                # 파벌 영토 색상 오버레이
                faction_territory_color = None
                faction_reg = world.faction_registry
                for fid, faction in faction_reg.items():
                    if (x, y) in faction.territory:
                        faction_territory_color = faction.color
                        break

                if entities_at:
                    count = len(entities_at)
                    first = entities_at[0]
                    on_home = (
                        hasattr(first, "home_x")
                        and first.home_x == x
                        and first.home_y == y
                    )
                    if count >= 3:
                        ch = SYM["HD"]
                    elif count == 2:
                        ch = SYM["DB"]
                    elif on_home:
                        ch = SYM["HT"]
                    else:
                        ch = SYM["SG"]
                    base_style = SPEC_STYLES.get(first.genome.specialization, "cp.text")
                    # 파벌 멤버는 파벌 색상으로 표시
                    if first.faction_id >= 0 and faction_territory_color:
                        style = faction_territory_color
                    else:
                        style = base_style
                    map_text.append(ch, style=style)
                elif is_claimed:
                    base = Style(dim=True, color="#585b70")
                    if faction_territory_color:
                        map_text.append(".", style=Style(dim=True, color="#6c7086"))
                    else:
                        map_text.append(".", style=base)
                else:
                    biome = tile.biome.value
                    t_style = TILE_STYLES.get(biome, "cp.dim")
                    t_char = TILE_CHARS.get(biome, "?")
                    map_text.append(t_char, style=t_style)

            map_text.append("\n")

        return Panel(
            map_text,
            title=Text.assemble(("[M]", "cp.cyan"), (" 월드 맵", "cp.cyan")),
            box=ROUNDED,
            border_style="cp.green",
            padding=(0, 1),
        )

    # ------------------------------------------
    # Info Panel
    # ------------------------------------------
    def _render_info_panel(self) -> Panel:
        """경제/인구/기술 정보를 테이블로 표시."""
        world = self.engine.world
        market = self.engine.market
        snap = self.engine.metrics.latest()

        groups: list[Panel] = []

        # -- Economy --
        econ = Table.grid(padding=(0, 2))
        econ.add_column(style="cp.dim", width=14)
        econ.add_column(style="cp.text")
        if snap:
            econ.add_row("지니계수", f"{snap.gini_coefficient:.4f}")
            econ.add_row("분업지수", f"{snap.specialization_diversity:.4f}")
            econ.add_row("평균 부", f"{snap.avg_wealth:.1f}")
            econ.add_row("거래량", f"{snap.trade_volume:.1f}")
            econ.add_row("세금", f"{snap.total_taxes:.2f}")
        prices = market.market_summary()["prices"]
        price_items = "  ".join(
            f"[cp.green]{k}[/]:{v:.1f}" for k, v in prices.items()
        )
        econ.add_row("가격", price_items)
        groups.append(
            Panel(econ, title="[cp.amber][+] 경제[/]", box=ROUNDED, border_style="cp.dim")
        )

        # -- Population --
        pop = Table.grid(padding=(0, 2))
        pop.add_column(style="cp.dim", width=14)
        pop.add_column(style="cp.text")
        if snap:
            pop.add_row("인구", f"{snap.population}")
            pop.add_row("출생", f"[cp.green]{snap.births}[/]")
            pop.add_row("사망", f"[cp.red]{snap.deaths}[/]")
            pop.add_row("전투 사망", f"[cp.red]{snap.kill_count}[/]")
            pop.add_row("평균 에너지", f"{snap.avg_energy:.1f}")
        claimed_tiles = len(world.tile_claims)
        home_owners = sum(
            1
            for e in world.entities.values()
            if e.alive and hasattr(e, "home_x") and e.home_x is not None
        )
        pop.add_row("영토", f"{claimed_tiles}")
        pop.add_row("주택", f"{home_owners}")

        spec_counts: dict[str, int] = {}
        for e in world.entities.values():
            if e.alive:
                s = e.genome.specialization
                spec_counts[s] = spec_counts.get(s, 0) + 1
        spec_items = "  ".join(
            f"[{SPEC_STYLES.get(k, 'cp.text')}]{k[:3]}[/]:{v}"
            for k, v in sorted(spec_counts.items())
        )
        pop.add_row("직업", spec_items)
        groups.append(
            Panel(pop, title="[cp.cyan][~] 인구[/]", box=ROUNDED, border_style="cp.dim")
        )

        # -- Tech --
        tech = Table.grid(padding=(0, 2))
        tech.add_column(style="cp.dim", width=14)
        tech.add_column(style="cp.text")
        tech_tree = self.engine.tech_tree
        discovered = tech_tree.get_discovered()
        tech.add_row(
            "진척도",
            f"[cp.cyan]{len(discovered)}[/][cp.dim]/[/][cp.cyan]{tech_tree.total_count()}[/]",
        )
        if discovered:
            tech_names = ", ".join(
                f"[cp.green]{t.name}[/]" for t in discovered[-5:]
            )
            tech.add_row("최근", tech_names)
        groups.append(
            Panel(tech, title="[cp.cyan]\U0001f4a1 기술 트리[/]", box=ROUNDED, border_style="cp.dim")
        )

        # -- Factions --
        faction_reg = world.faction_registry
        if faction_reg:
            fac = Table.grid(padding=(0, 2))
            fac.add_column(style="cp.dim", width=14)
            fac.add_column(style="cp.text")
            fac.add_row("파벌", f"{len(faction_reg)}")
            for fid, f in sorted(faction_reg.items()):
                leader = world.entities.get(f.leader_id)
                leader_name = leader.name if leader else "?"
                fac.add_row(
                    f"  [{f.color}]{f.name}[/]",
                    f"n={f.member_count} {f.total_kills}k "
                    f"l={leader_name[:10]}"
                    f"{' [WAR]' if f.wars else ''}",
                )
            groups.append(
                Panel(fac, title="[cp.red]\U0001f525 파벌[/]", box=ROUNDED, border_style="cp.dim")
            )
        else:
            fac = Panel(
                Text("(파벌 없음)", style="cp.dim"),
                title="[cp.red]\U0001f525 파벌[/]", box=ROUNDED, border_style="cp.dim"
            )
            groups.append(fac)

        # -- Ideology --
        ideo_counts = ideology_summary(world)
        if ideo_counts:
            ideo = Table.grid(padding=(0, 2))
            ideo.add_column(style="cp.dim", width=14)
            ideo.add_column(style="cp.text")
            ideo.add_row("이데올로기", f"{sum(ideo_counts.values())}명")
            ideo_names = {
                "materialism": "[cp.amber]유물론[/]",
                "militarism": "[cp.red]군국주의[/]",
                "spiritualism": "[cp.purple]영성주의[/]",
                "egalitarianism": "[cp.green]평등주의[/]",
            }
            for ideo_name, count in sorted(ideo_counts.items(), key=lambda x: -x[1]):
                display = ideo_names.get(ideo_name, ideo_name)
                ideo.add_row(f"  {display}", f"{count}")
            groups.append(
                Panel(ideo, title="[cp.cyan]\U0001f9e0 이데올로기[/]", box=ROUNDED, border_style="cp.dim")
            )
        else:
            ideo = Panel(
                Text("(아직 형성 안 됨)", style="cp.dim"),
                title="[cp.cyan]\U0001f9e0 이데올로기[/]", box=ROUNDED, border_style="cp.dim"
            )
            groups.append(ideo)

        # -- Brain Comparison --
        brain_panel = self._render_brain_panel(snap)
        groups.append(brain_panel)

        # -- Market --
        mkt = Table.grid(padding=(0, 2))
        mkt.add_column(style="cp.dim", width=14)
        mkt.add_column(style="cp.text")
        summary = market.market_summary()
        mkt.add_row("매수 주문", f"{summary['open_buy_orders']}")
        mkt.add_row("매도 주문", f"{summary['open_sell_orders']}")
        mkt.add_row("체결", f"{summary['total_trades']}")
        groups.append(
            Panel(mkt, title="[cp.purple]\U0001f4b1 시장[/]", box=ROUNDED, border_style="cp.dim")
        )

        # -- Buildings --
        bld_data = {"total": 0}
        for e in self.engine.world.entities.values():
            if e.alive:
                for b in e.buildings:
                    bld_data[b] = bld_data.get(b, 0) + 1
                    bld_data["total"] += 1
        if bld_data["total"] > 0:
            bld_grid = Table.grid(padding=(0, 2))
            bld_grid.add_column(style="cp.dim", width=14)
            bld_grid.add_column(style="cp.text")
            bld_grid.add_row("건물", f"{bld_data['total']}개")
            for bname, count in sorted(bld_data.items()):
                if bname == "total":
                    continue
                bld_grid.add_row(f"  {bname}", f"{count}")
            groups.append(
                Panel(bld_grid, title="[cp.amber]\U0001f3db 건물[/]", box=ROUNDED, border_style="cp.dim")
            )

        return Panel(
            Group(*groups),
            title=Text.assemble(("\u2699", "cp.magenta"), (" 상태", "cp.magenta")),
            box=ROUNDED,
            border_style="cp.magenta",
            padding=(0, 1),
        )

    # ------------------------------------------
    # Brain Comparison Panel
    # ------------------------------------------
    def _render_brain_panel(self, snap) -> Panel:
        grid = Table.grid(padding=(0, 2))
        grid.add_column(style="cp.dim", width=14)
        grid.add_column(style="cp.text")

        if snap and snap.population > 0:
            total = snap.smart_count + snap.rule_count
            smart_pct = snap.smart_count / total * 100 if total > 0 else 0
            rule_pct = snap.rule_count / total * 100 if total > 0 else 0

            # SmartBrain
            grid.add_row("[cp.cyan]SmartBrain[/]", "")
            grid.add_row("  인원", f"{snap.smart_count}명 ([cp.green]{smart_pct:.1f}%[/])")
            grid.add_row("  평균 부", f"{snap.smart_avg_wealth:.1f}")
            grid.add_row("  평균 에너지", f"{snap.smart_avg_energy:.1f}")
            grid.add_row("  총 킬", f"{snap.smart_total_kills}")
            if snap.smart_count > 0:
                grid.add_row("  1인당 킬", f"{snap.smart_total_kills / snap.smart_count:.2f}")
            grid.add_row("", "")

            # RuleBasedBrain
            grid.add_row("[cp.text]RuleBased[/]", "")
            grid.add_row("  인원", f"{snap.rule_count}명 ([cp.green]{rule_pct:.1f}%[/])")
            grid.add_row("  평균 부", f"{snap.rule_avg_wealth:.1f}")
            grid.add_row("  평균 에너지", f"{snap.rule_avg_energy:.1f}")
            grid.add_row("  총 킬", f"{snap.rule_total_kills}")
            if snap.rule_count > 0:
                grid.add_row("  1인당 킬", f"{snap.rule_total_kills / snap.rule_count:.2f}")

            # 격차 (SmartBrain - RuleBased)
            grid.add_row("", "")
            wealth_gap = snap.smart_avg_wealth - snap.rule_avg_wealth
            gap_style = "cp.green" if wealth_gap >= 0 else "cp.red"
            grid.add_row("  부 격차", f"[{gap_style}]{wealth_gap:+.1f}[/]")
            energy_gap = snap.smart_avg_energy - snap.rule_avg_energy
            gap_style_e = "cp.green" if energy_gap >= 0 else "cp.red"
            grid.add_row("  에너지 격차", f"[{gap_style_e}]{energy_gap:+.1f}[/]")
        else:
            grid.add_row("데이터 없음", "")

        return Panel(
            grid,
            title="[cp.cyan]\U0001f9e0 두뇌 비교[/]",
            box=ROUNDED,
            border_style="cp.dim",
        )

    # ------------------------------------------
    # Events Panel
    # ------------------------------------------
    def _render_events_panel(self) -> Panel:
        """최근 이벤트 로그를 사이버펑크 스타일로."""
        events = self.engine.event_log
        if not events:
            return Panel(
                Text("(이벤트 없음)", style="cp.dim"),
                title="[cp.amber]\U0001f4dd 이벤트 로그[/]",
                box=ROUNDED,
                border_style="cp.amber",
                padding=(0, 1),
            )

        important_types = {
            "reproduce", "death", "starvation", "tech_discovery",
            "combat", "craft", "construct", "loot",
            "faction_formed", "faction_disbanded",
            "knowledge_loot", "equipment_loot", "equipment_broken",
            "event_started", "event_ended", "event_death",
            "building_destroyed",
        }
        recent = [e for e in reversed(events) if e.get("type") in important_types][:6]

        lines: list[Text] = []
        for ev in recent:
            tick = ev.get("tick", "?")
            etype = ev.get("type", "?")
            name = ev.get("entity_name", "?")
            data = ev.get("data", {})

            if etype == "reproduce":
                child = data.get("child", "?")
                partner = data.get("partner")
                if partner:
                    t = Text.assemble(
                        (f"[{tick}] ", "cp.dim"),
                        (f"{SYM['HR']} ", "cp.pink"),
                        (f"{name}", "cp.text"),
                        (f" x {partner} ", "cp.dim"),
                        (f"{SYM['AR']} {child}", "cp.green"),
                    )
                else:
                    t = Text.assemble(
                        (f"[{tick}] ", "cp.dim"),
                        (f"{SYM['HR']} ", "cp.pink"),
                        (f"{name}", "cp.text"),
                        (f" {SYM['AR']} {child}", "cp.green"),
                        (" (단성생식)", "cp.dim"),
                    )
            elif etype == "starvation":
                t = Text.assemble(
                    (f"[{tick}] ", "cp.dim"),
                    (f"{SYM['SK']} ", "cp.red"),
                    (f"{name}", "cp.text"),
                    (" -- 굶어 죽음", "cp.red"),
                )
            elif etype == "tech_discovery":
                tech = data.get("tech", "?")
                t = Text.assemble(
                    (f"[{tick}] ", "cp.dim"),
                    (f"{SYM['ST']} ", "cp.cyan"),
                    (f"{tech}", "cp.cyan"),
                    (" 발견!", "cp.green"),
                )
            elif etype == "combat":
                target = data.get("target", "?")
                dmg = data.get("damage_dealt", "?")
                taken = data.get("damage_taken", 0)
                target_alive = data.get("target_alive", True)
                status = "" if target_alive else " 처치"
                t = Text.assemble(
                    (f"[{tick}] ", "cp.dim"),
                    ("@ ", "cp.red"),
                    (f"{name}", "cp.text"),
                    (f" -> {target}", "cp.amber"),
                    (f" ({dmg:.0f}/{taken:.0f}{status})", "cp.red"),
                )
            elif etype == "loot":
                loot = data.get("loot", {})
                loot_str = ", ".join(f"{k}:{v}" for k, v in loot.items())
                t = Text.assemble(
                    (f"[{tick}] ", "cp.dim"),
                    (f"   약탈: {loot_str}", "cp.amber"),
                )
            elif etype == "craft":
                item = data.get("item", "?")
                t = Text.assemble(
                    (f"[{tick}] ", "cp.dim"),
                    (f"{SYM['HM']} ", "cp.blue"),
                    (f"{name}", "cp.text"),
                    (f" {SYM['AR']} {item}", "cp.cyan"),
                )
            elif etype == "faction_formed":
                f_name = data.get("faction", "?")
                leader = data.get("leader", "?")
                n = data.get("members", 0)
                t = Text.assemble(
                    (f"[{tick}] ", "cp.dim"),
                    ("\u26a1 ", "cp.red"),
                    (f"{f_name}", "cp.red"),
                    (f" 결성 (인원 {n}, 지도자: {leader})", "cp.text"),
                )
            elif etype == "faction_disbanded":
                f_name = data.get("faction", "?")
                reason = data.get("reason", "?")
                t = Text.assemble(
                    (f"[{tick}] ", "cp.dim"),
                    ("\u2620 ", "cp.red"),
                    (f"{f_name}", "cp.red"),
                    (f" 해체 ({reason})", "cp.dim"),
                )
            elif etype == "knowledge_loot":
                tech = data.get("tech", "?")
                source = data.get("from", "?")
                t = Text.assemble(
                    (f"[{tick}] ", "cp.dim"),
                    ("\U0001f4da ", "cp.cyan"),
                    (f"{name}", "cp.text"),
                    (f" {tech} 약탈 (from {source})", "cp.cyan"),
                )
            elif etype == "equipment_loot":
                item = data.get("item", "?")
                source = data.get("from", "?")
                t = Text.assemble(
                    (f"[{tick}] ", "cp.dim"),
                    ("\u2694 ", "cp.amber"),
                    (f"{name}", "cp.text"),
                    (f" {item} 획득 (from {source})", "cp.amber"),
                )
            elif etype == "equipment_broken":
                item = data.get("item", "?")
                t = Text.assemble(
                    (f"[{tick}] ", "cp.dim"),
                    ("\U0001f4a5 ", "cp.red"),
                    (f"{name}", "cp.text"),
                    (f" {item} 파괴!", "cp.red"),
                )
            elif etype == "construct":
                bld_name = data.get("building", "?")
                t = Text.assemble(
                    (f"[{tick}] ", "cp.dim"),
                    ("\U0001f3d7 ", "cp.amber"),
                    (f"{name}", "cp.text"),
                    (f" \u2192 {bld_name} 건설!", "cp.amber"),
                )
            elif etype == "event_started":
                ev_name = data.get("event", "?")
                t = Text.assemble(
                    (f"[{tick}] ", "cp.dim"),
                    ("\U0001f4a5 ", "cp.red"),
                    (f"\u26a0 {ev_name} 발생!", "cp.red"),
                )
            elif etype == "event_ended":
                ev_name = data.get("event", "?")
                t = Text.assemble(
                    (f"[{tick}] ", "cp.dim"),
                    ("\u2705 ", "cp.green"),
                    (f"{ev_name} 종료", "cp.green"),
                )
            elif etype == "event_death":
                cause = data.get("cause", "?")
                t = Text.assemble(
                    (f"[{tick}] ", "cp.dim"),
                    ("\u2620 ", "cp.red"),
                    (f"{name}", "cp.text"),
                    (f" {cause} 사망", "cp.red"),
                )
            elif etype == "building_destroyed":
                bld_name = data.get("building", "?")
                t = Text.assemble(
                    (f"[{tick}] ", "cp.dim"),
                    ("\U0001f4a5 ", "cp.red"),
                    (f"{name}", "cp.text"),
                    (f" {bld_name} \ud83d\udca5", "cp.red"),
                )
            else:
                t = Text(f"[{tick}] {etype}: {name} {data}", style="cp.dim")

            lines.append(t)

        events_text = Text("\n").join(lines) if lines else Text("(중요 이벤트 없음)", style="cp.dim")

        return Panel(
            events_text,
            title=Text.assemble(("\U0001f4dd", "cp.amber"), (" EVENT LOG", "cp.amber")),
            box=ROUNDED,
            border_style="cp.amber",
            padding=(0, 1),
        )

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
                    ("\u26a1 ", "cp.cyan"),
                    ("시뮬레이션 종료", "cp.magenta"),
                    (" \u26a1", "cp.cyan"),
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
        grid.add_row("[cp.cyan]\u2500" * 35 + "[/]", "")
        grid.add_row("[cp.cyan]인구 통계[/]", "")
        grid.add_row("[cp.cyan]\u2500" * 35 + "[/]", "")
        grid.add_row("총 틱", f"{snap.tick}")
        grid.add_row("최종 인구", f"{snap.population}")
        grid.add_row("총 출생", f"[cp.green]{snap.births}[/]")
        grid.add_row("총 사망", f"[cp.red]{snap.deaths}[/]")
        grid.add_row("전투 사망", f"[cp.red]{snap.kill_count}[/]")

        grid.add_section()
        grid.add_row("[cp.amber]\u2500" * 35 + "[/]", "")
        grid.add_row("[cp.amber]경제 지표[/]", "")
        grid.add_row("[cp.amber]\u2500" * 35 + "[/]", "")
        grid.add_row("지니계수", f"{snap.gini_coefficient:.4f}")
        grid.add_row("분업지수", f"{snap.specialization_diversity:.4f}")
        grid.add_row("평균 부", f"{snap.avg_wealth:.2f}")
        grid.add_row("총 거래량", f"{snap.trade_volume:.2f}")
        grid.add_row("총 세금", f"{snap.total_taxes:.2f}")

        grid.add_section()
        grid.add_row("[cp.green]\u2500" * 35 + "[/]", "")
        grid.add_row("[cp.green]최종 가격[/]", "")
        grid.add_row("[cp.green]\u2500" * 35 + "[/]", "")
        for rtype, price in snap.prices.items():
            grid.add_row(f"  {rtype}", f"{price:.2f}")

        # Tech
        tech_tree = self.engine.tech_tree
        grid.add_section()
        grid.add_row("[cp.cyan]\u2500" * 35 + "[/]", "")
        grid.add_row("[cp.cyan]기술[/]", "")
        grid.add_row("[cp.cyan]\u2500" * 35 + "[/]", "")
        grid.add_row(
            "발견",
            f"[cp.cyan]{tech_tree.discover_count()}[/][cp.dim]/[/][cp.cyan]{tech_tree.total_count()}[/]",
        )
        for tech in tech_tree.get_discovered():
            grid.add_row(f"  {SYM['ST']}", f"[cp.green]{tech.name}[/]")

        # Brain Comparison
        grid.add_section()
        grid.add_row("[cp.cyan]\u2500" * 35 + "[/]", "")
        grid.add_row("[cp.cyan]두뇌 비교 (실험)[/]", "")
        grid.add_row("[cp.cyan]\u2500" * 35 + "[/]", "")
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
        grid.add_row("[cp.purple]\u2500" * 35 + "[/]", "")
        grid.add_row("[cp.purple]직업 분포[/]", "")
        grid.add_row("[cp.purple]\u2500" * 35 + "[/]", "")
        for spec, count in sorted(spec_counts.items()):
            bar = "\u2588" * count
            st = SPEC_STYLES.get(spec, "cp.text")
            grid.add_row(f"  [{st}]{spec}[/]", f"{count} {bar}")

        console.print(Panel(grid, box=ROUNDED, border_style="cp.cyan"))
        console.print()
