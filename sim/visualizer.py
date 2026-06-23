"""사이버펑크 TUI -- Rich 기반 실시간 시뮬레이션 시각화."""

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
from .metrics import MetricsCollector

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
# Cyberpunk Color Theme
# ----------------------------------------------
CYBERPUNK_THEME = Theme(
    {
        "cp.magenta": "bold #ff00ff",
        "cp.cyan": "bold #00ffff",
        "cp.green": "bold #00ff41",
        "cp.amber": "bold #ffb000",
        "cp.red": "bold #ff003c",
        "cp.blue": "bold #0088ff",
        "cp.purple": "bold #aa00ff",
        "cp.dim": "#555555",
        "cp.text": "#c0c0c0",
        "cp.white": "bold #ffffff",
        "cp.pink": "#ff66aa",
    }
)

console = Console(
    theme=CYBERPUNK_THEME,
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
    "forest": "green",
    "mountain": "cp.white",
    "water": "cp.blue",
    "desert": "cp.amber",
    "hill": "yellow",
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
    """사이버펑크 TUI 시각화 -- Rich Layout 기반."""

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
        """네온 타이틀 바."""
        tick_str = f"TICK {state.tick:05d}"
        pop_str = f"POP {state.alive_count}/{state.population}"
        title = Text.assemble(
            (">> ", "cp.cyan"),
            ("SELF-GROWING CIVILIZATION", "cp.magenta"),
            ("  v0.1", "cp.dim"),
        )
        status = Text.assemble(
            (tick_str, "cp.cyan"),
            ("  |  ", "cp.dim"),
            (pop_str, "cp.green"),
        )
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
                    style = SPEC_STYLES.get(first.genome.specialization, "cp.text")
                    map_text.append(ch, style=style)
                elif is_claimed:
                    map_text.append(".", style=Style(dim=True, color="#555555"))
                else:
                    biome = tile.biome.value
                    t_style = TILE_STYLES.get(biome, "cp.dim")
                    t_char = TILE_CHARS.get(biome, "?")
                    map_text.append(t_char, style=t_style)

            map_text.append("\n")

        return Panel(
            map_text,
            title=Text.assemble(("[M]", "cp.cyan"), (" WORLD MAP", "cp.cyan")),
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
            econ.add_row("Gini Coeff", f"{snap.gini_coefficient:.4f}")
            econ.add_row("Diversity", f"{snap.specialization_diversity:.4f}")
            econ.add_row("Avg Wealth", f"{snap.avg_wealth:.1f}")
            econ.add_row("Trade Vol.", f"{snap.trade_volume:.1f}")
            econ.add_row("Taxes", f"{snap.total_taxes:.2f}")
        prices = market.market_summary()["prices"]
        price_items = "  ".join(
            f"[cp.green]{k}[/]:{v:.1f}" for k, v in prices.items()
        )
        econ.add_row("Prices", price_items)
        groups.append(
            Panel(econ, title="[cp.amber][+] Economy[/]", box=ROUNDED, border_style="cp.dim")
        )

        # -- Population --
        pop = Table.grid(padding=(0, 2))
        pop.add_column(style="cp.dim", width=14)
        pop.add_column(style="cp.text")
        if snap:
            pop.add_row("Population", f"{snap.population}")
            pop.add_row("Births", f"[cp.green]{snap.births}[/]")
            pop.add_row("Deaths", f"[cp.red]{snap.deaths}[/]")
            pop.add_row("Combat Kills", f"[cp.red]{snap.kill_count}[/]")
            pop.add_row("Avg Energy", f"{snap.avg_energy:.1f}")
        claimed_tiles = len(world.tile_claims)
        home_owners = sum(
            1
            for e in world.entities.values()
            if e.alive and hasattr(e, "home_x") and e.home_x is not None
        )
        pop.add_row("Claims", f"{claimed_tiles}")
        pop.add_row("Homeowners", f"{home_owners}")

        spec_counts: dict[str, int] = {}
        for e in world.entities.values():
            if e.alive:
                s = e.genome.specialization
                spec_counts[s] = spec_counts.get(s, 0) + 1
        spec_items = "  ".join(
            f"[{SPEC_STYLES.get(k, 'cp.text')}]{k[:3]}[/]:{v}"
            for k, v in sorted(spec_counts.items())
        )
        pop.add_row("Spec", spec_items)
        groups.append(
            Panel(pop, title="[cp.cyan][~] Population[/]", box=ROUNDED, border_style="cp.dim")
        )

        # -- Tech --
        tech = Table.grid(padding=(0, 2))
        tech.add_column(style="cp.dim", width=14)
        tech.add_column(style="cp.text")
        tech_tree = self.engine.tech_tree
        discovered = tech_tree.get_discovered()
        tech.add_row(
            "Progress",
            f"[cp.cyan]{len(discovered)}[/][cp.dim]/[/][cp.cyan]{tech_tree.total_count()}[/]",
        )
        if discovered:
            tech_names = ", ".join(
                f"[cp.green]{t.name}[/]" for t in discovered[-5:]
            )
            tech.add_row("Recent", tech_names)
        groups.append(
            Panel(tech, title="[cp.cyan]\U0001f4a1 Tech Tree[/]", box=ROUNDED, border_style="cp.dim")
        )

        # -- Market --
        mkt = Table.grid(padding=(0, 2))
        mkt.add_column(style="cp.dim", width=14)
        mkt.add_column(style="cp.text")
        summary = market.market_summary()
        mkt.add_row("Buy Orders", f"{summary['open_buy_orders']}")
        mkt.add_row("Sell Orders", f"{summary['open_sell_orders']}")
        mkt.add_row("Trades", f"{summary['total_trades']}")
        groups.append(
            Panel(mkt, title="[cp.purple]\U0001f4b1 Market[/]", box=ROUNDED, border_style="cp.dim")
        )

        return Panel(
            Group(*groups),
            title=Text.assemble(("\u2699", "cp.magenta"), (" STATUS", "cp.magenta")),
            box=ROUNDED,
            border_style="cp.magenta",
            padding=(0, 1),
        )

    # ------------------------------------------
    # Events Panel
    # ------------------------------------------
    def _render_events_panel(self) -> Panel:
        """최근 이벤트 로그를 사이버펑크 스타일로."""
        events = self.engine.event_log
        if not events:
            return Panel(
                Text("(no events yet)", style="cp.dim"),
                title="[cp.amber]\U0001f4dd Event Log[/]",
                box=ROUNDED,
                border_style="cp.amber",
                padding=(0, 1),
            )

        important_types = {
            "reproduce",
            "death",
            "starvation",
            "tech_discovery",
            "combat",
            "craft",
            "loot",
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
                        (" (asexual)", "cp.dim"),
                    )
            elif etype == "starvation":
                t = Text.assemble(
                    (f"[{tick}] ", "cp.dim"),
                    (f"{SYM['SK']} ", "cp.red"),
                    (f"{name}", "cp.text"),
                    (" -- starved", "cp.red"),
                )
            elif etype == "tech_discovery":
                tech = data.get("tech", "?")
                t = Text.assemble(
                    (f"[{tick}] ", "cp.dim"),
                    (f"{SYM['ST']} ", "cp.cyan"),
                    (f"{tech}", "cp.cyan"),
                    (" discovered!", "cp.green"),
                )
            elif etype == "combat":
                target = data.get("target", "?")
                dmg = data.get("damage_dealt", "?")
                taken = data.get("damage_taken", 0)
                target_alive = data.get("target_alive", True)
                status = "" if target_alive else " KILL"
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
                    (f"   loot: {loot_str}", "cp.amber"),
                )
            elif etype == "craft":
                item = data.get("item", "?")
                t = Text.assemble(
                    (f"[{tick}] ", "cp.dim"),
                    (f"{SYM['HM']} ", "cp.blue"),
                    (f"{name}", "cp.text"),
                    (f" {SYM['AR']} {item}", "cp.cyan"),
                )
            else:
                t = Text(f"[{tick}] {etype}: {name} {data}", style="cp.dim")

            lines.append(t)

        events_text = Text("\n").join(lines) if lines else Text("(no important events)", style="cp.dim")

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
                    ("SIMULATION TERMINATED", "cp.magenta"),
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
        grid.add_row("[cp.cyan]POPULATION STATISTICS[/]", "")
        grid.add_row("[cp.cyan]\u2500" * 35 + "[/]", "")
        grid.add_row("Total Ticks", f"{snap.tick}")
        grid.add_row("Final Population", f"{snap.population}")
        grid.add_row("Total Births", f"[cp.green]{snap.births}[/]")
        grid.add_row("Total Deaths", f"[cp.red]{snap.deaths}[/]")
        grid.add_row("Combat Deaths", f"[cp.red]{snap.kill_count}[/]")

        grid.add_section()
        grid.add_row("[cp.amber]\u2500" * 35 + "[/]", "")
        grid.add_row("[cp.amber]ECONOMIC INDICATORS[/]", "")
        grid.add_row("[cp.amber]\u2500" * 35 + "[/]", "")
        grid.add_row("Gini Coefficient", f"{snap.gini_coefficient:.4f}")
        grid.add_row("Diversity Index", f"{snap.specialization_diversity:.4f}")
        grid.add_row("Average Wealth", f"{snap.avg_wealth:.2f}")
        grid.add_row("Total Trade Volume", f"{snap.trade_volume:.2f}")
        grid.add_row("Total Taxes Collected", f"{snap.total_taxes:.2f}")

        grid.add_section()
        grid.add_row("[cp.green]\u2500" * 35 + "[/]", "")
        grid.add_row("[cp.green]FINAL PRICES[/]", "")
        grid.add_row("[cp.green]\u2500" * 35 + "[/]", "")
        for rtype, price in snap.prices.items():
            grid.add_row(f"  {rtype}", f"{price:.2f}")

        # Tech
        tech_tree = self.engine.tech_tree
        grid.add_section()
        grid.add_row("[cp.cyan]\u2500" * 35 + "[/]", "")
        grid.add_row("[cp.cyan]TECHNOLOGY[/]", "")
        grid.add_row("[cp.cyan]\u2500" * 35 + "[/]", "")
        grid.add_row(
            "Discovered",
            f"[cp.cyan]{tech_tree.discover_count()}[/][cp.dim]/[/][cp.cyan]{tech_tree.total_count()}[/]",
        )
        for tech in tech_tree.get_discovered():
            grid.add_row(f"  {SYM['ST']}", f"[cp.green]{tech.name}[/]")

        # Specialization
        spec_counts: dict[str, int] = {}
        for e in self.engine.world.entities.values():
            if e.alive:
                spec_counts[e.genome.specialization] = (
                    spec_counts.get(e.genome.specialization, 0) + 1
                )
        grid.add_section()
        grid.add_row("[cp.purple]\u2500" * 35 + "[/]", "")
        grid.add_row("[cp.purple]SPECIALIZATION[/]", "")
        grid.add_row("[cp.purple]\u2500" * 35 + "[/]", "")
        for spec, count in sorted(spec_counts.items()):
            bar = "\u2588" * count
            st = SPEC_STYLES.get(spec, "cp.text")
            grid.add_row(f"  [{st}]{spec}[/]", f"{count} {bar}")

        console.print(Panel(grid, box=ROUNDED, border_style="cp.cyan"))
        console.print()
