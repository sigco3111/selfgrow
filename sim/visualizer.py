"""터미널 기반 실시간 시각화 -- ASCII 월드 맵 + 상태 패널."""

from __future__ import annotations

from typing import TYPE_CHECKING

from . import config
from .metrics import MetricsCollector

if TYPE_CHECKING:
    from .engine import SimulationEngine
    from .entity import Entity


# ── cp949 안전 출력 ──
def _p(text: str) -> None:
    """cp949로 인코딩 불가능한 문자를 대체하여 출력."""
    try:
        print(text)
    except UnicodeEncodeError:
        safe = text.encode("cp949", errors="replace").decode("cp949")
        print(safe)


SYM = {
    "HD": "#",      # 밀집 (3+ entities)
    "DB": "%",      # 두명 (2 entities)
    "SG": "o",      # 한명 (1 entity)
    "HR": "*",      # 하트
    "SK": "x",      # 해골
    "ST": "+",      # 별
    "SW": "@",      # 검
    "HM": "^",      # 망치
    "HT": "H",      # 본거지 (home tile)
    "AR": "->",     # 화살표
}


class TerminalVisualizer:
    """실시간 터미널 시각화 (ANSI 이스케이프 코드 기반)."""

    def __init__(self, engine: SimulationEngine):
        self.engine = engine
        self.last_tick = -1

    def render(self) -> None:
        """한 프레임 렌더링."""
        _p("\033[2J\033[H")

        lines: list[str] = []

        state = self.engine.state()
        title = (f"[ Sim ] Tick {state.tick}  "
                 f"Pop: {state.alive_count}/{state.population}")
        lines.append(f"\033[1;36m{'=' * len(title)}\033[0m")
        lines.append(f"\033[1;33m{title}\033[0m")
        lines.append(f"\033[1;36m{'=' * len(title)}\033[0m")
        lines.append("")

        map_lines = self._render_map()
        lines.extend(map_lines)
        lines.append("")

        panel = self._render_panel()
        lines.extend(panel)
        lines.append("")

        events = self._render_events()
        if events:
            lines.extend(events)

        _p("\n".join(lines))
        self.last_tick = state.tick

    def _render_map(self) -> list[str]:
        """월드 맵을 ASCII로 렌더링 — 영토 표시 포함."""
        world = self.engine.world
        map_lines: list[str] = []

        entity_positions: dict[tuple[int, int], list[Entity]] = {}
        for entity in world.entities.values():
            if entity.alive:
                entity_positions.setdefault((entity.x, entity.y), []).append(entity)

        for y in range(world.height):
            row_chars: list[str] = []
            for x in range(world.width):
                tile = world.tile_at(x, y)
                if not tile:
                    row_chars.append(" ")
                    continue

                is_claimed = (x, y) in world.tile_claims
                entities_at = entity_positions.get((x, y), [])

                if entities_at:
                    count = len(entities_at)
                    first = entities_at[0]
                    on_home = (hasattr(first, "home_x") and first.home_x == x
                               and first.home_y == y)
                    if count >= 3:
                        ch = SYM["HD"]
                    elif count == 2:
                        ch = SYM["DB"]
                    elif on_home:
                        ch = SYM["HT"]
                    else:
                        ch = SYM["SG"]
                    spec = first.genome.specialization
                    color = {
                        "farmer": "32",
                        "miner": "33",
                        "merchant": "35",
                        "warrior": "31",
                        "crafter": "34",
                        "explorer": "36",
                        "general": "37",
                    }.get(spec, "37")
                    row_chars.append(f"\033[{color}m{ch}\033[0m")
                elif is_claimed:
                    row_chars.append("\033[2;90m.\033[0m")  # 클레임된 타일은 흐린 점
                else:
                    row_chars.append(f"\033[{tile.color_code()}m{tile.display_char()}\033[0m")
            map_lines.append("".join(row_chars))

        return map_lines

    def _render_panel(self) -> list[str]:
        """정보 패널."""
        lines: list[str] = []
        world = self.engine.world
        market = self.engine.market
        snap = self.engine.metrics.latest()

        lines.append("\033[1;34m== Economy ==\033[0m")
        if snap:
            lines.append(f"  Gini:          {snap.gini_coefficient:.4f}")
            lines.append(f"  Diversity:     {snap.specialization_diversity:.4f}")
            lines.append(f"  Avg Wealth:    {snap.avg_wealth:.1f}")
            lines.append(f"  Trade Volume:  {snap.trade_volume:.1f}")
            lines.append(f"  Taxes:         {snap.total_taxes:.2f}")

        prices = market.market_summary()["prices"]
        price_str = "  ".join(f"{k}:{v:.1f}" for k, v in prices.items())
        lines.append(f"  Prices:        {price_str}")
        lines.append("")

        lines.append("\033[1;34m== Population ==\033[0m")
        if snap:
            lines.append(f"  Pop:           {snap.population}")
            lines.append(f"  Births:        {snap.births}")
            lines.append(f"  Deaths:        {snap.deaths}")
            lines.append(f"  Combat Deaths: {snap.kill_count}")
            lines.append(f"  Avg Energy:    {snap.avg_energy:.1f}")

        claimed_tiles = len(world.tile_claims)
        home_owners = sum(1 for e in world.entities.values()
                          if e.alive and hasattr(e, "home_x") and e.home_x is not None)
        lines.append(f"  Claims:        {claimed_tiles}")
        lines.append(f"  Home Owners:   {home_owners}")

        spec_counts: dict[str, int] = {}
        for e in world.entities.values():
            if e.alive:
                s = e.genome.specialization
                spec_counts[s] = spec_counts.get(s, 0) + 1
        spec_str = "  ".join(f"{k[:3]}:{v}" for k, v in sorted(spec_counts.items()))
        lines.append(f"  Spec:          {spec_str}")
        lines.append("")

        lines.append("\033[1;34m== Tech ==\033[0m")
        tech_tree = self.engine.tech_tree
        discovered = tech_tree.get_discovered()
        lines.append(f"  Discovered: {len(discovered)}/{tech_tree.total_count()}")
        if discovered:
            tech_names = ", ".join(t.name for t in discovered[-5:])
            lines.append(f"  Recent: {tech_names}")
        lines.append("")

        summary = market.market_summary()
        lines.append("\033[1;34m== Market ==\033[0m")
        lines.append(f"  Buy Orders:    {summary['open_buy_orders']}")
        lines.append(f"  Sell Orders:   {summary['open_sell_orders']}")
        lines.append(f"  Trades:        {summary['total_trades']}")

        return lines

    def _render_events(self) -> list[str]:
        """최근 주요 이벤트."""
        events = self.engine.event_log
        if not events:
            return []

        important_types = {"reproduce", "death", "starvation",
                           "tech_discovery", "combat", "craft", "loot"}
        recent = [e for e in reversed(events)
                  if e.get("type") in important_types][:5]

        if not recent:
            return []

        lines = ["\033[1;34m== Events ==\033[0m"]
        for ev in recent:
            tick = ev.get("tick", "?")
            etype = ev.get("type", "?")
            name = ev.get("entity_name", "?")
            data = ev.get("data", {})

            if etype == "reproduce":
                child = data.get("child", "?")
                partner = data.get("partner")
                if partner:
                    lines.append(f"  [{tick}] {SYM['HR']} {name} x {partner} {SYM['AR']} {child}")
                else:
                    lines.append(f"  [{tick}] {SYM['HR']} {name} {SYM['AR']} {child} (asexual)")
            elif etype == "starvation":
                lines.append(f"  [{tick}] {SYM['SK']} {name} -- starved")
            elif etype == "tech_discovery":
                tech = data.get("tech", "?")
                lines.append(f"  [{tick}] {SYM['ST']} {tech} discovered!")
            elif etype == "combat":
                target = data.get("target", "?")
                dmg = data.get("damage_dealt", "?")
                taken = data.get("damage_taken", 0)
                target_alive = data.get("target_alive", True)
                status = "" if target_alive else " KILL"
                entry = f"  [{tick}] @ {name} -> {target}({dmg:.0f}/{taken:.0f}{status})"
                lines.append(entry)
            elif etype == "loot":
                loot = data.get("loot", {})
                loot_str = ", ".join(f"{k}:{v}" for k, v in loot.items())
                lines.append(f"  [{tick}]    loot: {loot_str}")
            elif etype == "craft":
                item = data.get("item", "?")
                lines.append(f"  [{tick}] {SYM['HM']} {name} {SYM['AR']} {item}")
            else:
                lines.append(f"  [{tick}] {etype}: {name} {data}")

        return lines

    def render_final_summary(self, metrics: MetricsCollector) -> None:
        """시뮬레이션 종료 후 최종 통계."""
        _p("\033[2J\033[H")
        snap = metrics.latest()
        if snap is None:
            return

        lines = [
            "\033[1;36m" + "=" * 60 + "\033[0m",
            "\033[1;33m      S I M U L A T I O N   E N D      \033[0m",
            "\033[1;36m" + "=" * 60 + "\033[0m",
            "",
            f"\033[1mTicks:\033[0m        {snap.tick}",
            f"\033[1mFinal Pop:\033[0m    {snap.population}",
            f"\033[1mTotal Births:\033[0m {snap.births}",
            f"\033[1mTotal Deaths:\033[0m {snap.deaths}",
            f"\033[1mCombat Deaths:\033[0m {snap.kill_count}",
            "",
            f"\033[1mGini Coeff:\033[0m   {snap.gini_coefficient:.4f}",
            f"\033[1mDiversity Idx:\033[0m {snap.specialization_diversity:.4f}",
            f"\033[1mAvg Wealth:\033[0m   {snap.avg_wealth:.1f}",
            f"\033[1mTrade Vol:\033[0m    {snap.trade_volume:.1f}",
            f"\033[1mTotal Taxes:\033[0m  {snap.total_taxes:.2f}",
            "",
            "\033[1mFinal Prices:\033[0m",
        ]
        for rtype, price in snap.prices.items():
            lines.append(f"    {rtype}: {price:.2f}")

        tech_tree = self.engine.tech_tree
        lines.append("")
        lines.append(f"\033[1mTech Discovered:\033[0m {tech_tree.discover_count()}/{tech_tree.total_count()}")
        for tech in tech_tree.get_discovered():
            lines.append(f"    {SYM['ST']} {tech.name} -- {tech.description}")

        lines.append("")
        lines.append("\033[1mSpecialization Distribution:\033[0m")
        spec_counts: dict[str, int] = {}
        for e in self.engine.world.entities.values():
            if e.alive:
                spec_counts[e.genome.specialization] = \
                    spec_counts.get(e.genome.specialization, 0) + 1
        for spec, count in sorted(spec_counts.items()):
            bar = "#" * count
            lines.append(f"    {spec}: {count} {bar}")

        lines.append("")
        lines.append("\033[1;36m" + "=" * 60 + "\033[0m")
        _p("\n".join(lines))
