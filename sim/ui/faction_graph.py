"""파벌 관계도 — 파벌 간 관계를 ASCII 그래프로 표시."""

from __future__ import annotations

from typing import TYPE_CHECKING

from rich.panel import Panel
from rich.table import Table
from rich.text import Text

if TYPE_CHECKING:
    from ..faction import Faction


def render_faction_graph(faction_reg: dict[int, Faction]) -> Panel:
    if not faction_reg:
        return Panel(
            Text("(파벌 없음)", style="cp.dim"),
            title="[cp.red]🔗 파벌 관계도[/]",
            border_style="cp.dim",
        )

    table = Table.grid(padding=(0, 1))
    table.add_column(style="cp.text", width=14)
    table.add_column(width=30)
    table.add_column(style="cp.dim", width=10)

    for fid, faction in sorted(faction_reg.items()):
        color = faction.color
        relations: list[str] = []

        for target_id, treaty in faction.diplomacy.items():
            target = faction_reg.get(target_id)
            if target:
                relations.append(f"[{target.color}]{target.name}[/] ({treaty})")

        for enemy_id in faction.wars:
            enemy = faction_reg.get(enemy_id)
            if enemy:
                relations.append(f"[cp.red]⚔ {enemy.name}[/] (전쟁)")

        if not relations:
            relations_str = "[cp.dim]관계 없음[/]"
        else:
            relations_str = ", ".join(relations)

        table.add_row(
            f"[{color}]■ {faction.name}[/]",
            relations_str,
            f"n={faction.member_count}",
        )

        table.add_row(
            "",
            f"[cp.dim]결속 {faction.cohesion:.2f} 킬 {faction.total_kills}[/]",
            "",
        )
        table.add_row("", "", "")

    return Panel(
        table,
        title="[cp.red]🔗 파벌 관계도[/]",
        border_style="cp.red",
        padding=(0, 1),
    )
