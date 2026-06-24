"""기술 트리 시각화 — ASCII 형태로 기술 트리 구조 표시."""

from __future__ import annotations

from typing import TYPE_CHECKING

from rich.panel import Panel
from rich.table import Table
from rich.text import Text

if TYPE_CHECKING:
    from ..knowledge import TechnologyTree
    from ..entity import Entity


TIER_LABELS = {0: "Tier 1", 1: "Tier 2", 2: "Tier 3", 3: "Tier 4"}
TIER_COLORS = {0: "cp.green", 1: "cp.cyan", 2: "cp.amber", 3: "cp.magenta"}


def _get_tier(tech_name: str, tech_tree: TechnologyTree) -> int:
    tech = tech_tree.get_by_name(tech_name)
    if tech is None:
        return 0
    return len(tech.prerequisites)


def render_tech_tree_panel(
    tech_tree: TechnologyTree,
    known_techs: set[str] | None = None,
) -> Panel:
    known = known_techs or set()

    tiers: dict[int, list[str]] = {}
    for tech in tech_tree.all_techs():
        tier = _get_tier(tech.name, tech_tree)
        tiers.setdefault(tier, []).append(tech.name)

    table = Table.grid(padding=(0, 1))
    table.add_column(style="cp.dim", width=8)
    table.add_column(width=18)
    table.add_column(style="cp.dim", width=6)
    table.add_column(style="cp.text")

    for tier_num in sorted(tiers.keys()):
        tier_color = TIER_COLORS.get(tier_num, "cp.text")
        tier_label = TIER_LABELS.get(tier_num, f"T{tier_num}")
        table.add_row(
            f"[{tier_color}]── {tier_label} ──[/]", "", "", ""
        )

        for tech_name in sorted(tiers[tier_num]):
            tech = tech_tree.get_by_name(tech_name)
            if tech is None:
                continue

            is_discovered = tech_name in known
            status_icon = "[cp.green]✓[/]" if is_discovered else "[cp.dim]○[/]"
            name_color = "cp.green" if is_discovered else "cp.text"
            prereqs = ", ".join(tech.prerequisites) if tech.prerequisites else "-"
            cost = f"{tech.research_cost}pt"

            table.add_row(
                f"  {status_icon}",
                f"[{name_color}]{tech_name}[/]",
                f"[cp.dim]{cost}[/]",
                f"[cp.dim]{prereqs}[/]",
            )

        table.add_row("", "", "", "")

    discovered = tech_tree.discover_count()
    total = tech_tree.total_count()

    return Panel(
        table,
        title=f"[cp.cyan]🔬 기술 트리 ({discovered}/{total})[/]",
        border_style="cp.cyan",
        padding=(0, 1),
    )
