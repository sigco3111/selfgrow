"""외교 관계 관리 — 파벌 간 조약, 동맹, 전쟁."""

from __future__ import annotations

from typing import TYPE_CHECKING

from . import config

if TYPE_CHECKING:
    from .entity import Entity
    from .faction import Faction


DIPLOMACY_TYPES = ("ALLIANCE", "TRADE_PACT", "NON_AGGRESSION", "VASSAL")


class DiplomacyManager:
    def __init__(self):
        pass

    def set_relation(self, faction: Faction, target_id: int, treaty: str) -> None:
        if treaty in DIPLOMACY_TYPES:
            faction.diplomacy[target_id] = treaty

    def get_relation(self, faction: Faction, target_id: int) -> str | None:
        return faction.diplomacy.get(target_id)

    def remove_relation(self, faction: Faction, target_id: int) -> None:
        faction.diplomacy.pop(target_id, None)

    def has_treaty_with(self, faction: Faction, target_id: int, treaty: str) -> bool:
        return faction.diplomacy.get(target_id) == treaty

    def is_neutral(self, faction: Faction, target_id: int) -> bool:
        return (not faction.is_at_war_with(target_id)
                and not self.has_treaty_with(faction, target_id, "ALLIANCE")
                and not self.has_treaty_with(faction, target_id, "VASSAL")
                and not self.has_treaty_with(faction, target_id, "NON_AGGRESSION"))

    def propose_treaty(self, faction: Faction, target_faction: Faction, treaty: str) -> bool:
        if not config.DIPLOMACY_ENABLED:
            return False
        if treaty not in DIPLOMACY_TYPES:
            return False
        if faction.is_at_war_with(target_faction.faction_id):
            return False

        if treaty == "ALLIANCE":
            self.set_relation(faction, target_faction.faction_id, "ALLIANCE")
            self.set_relation(target_faction, faction.faction_id, "ALLIANCE")
        elif treaty == "TRADE_PACT":
            self.set_relation(faction, target_faction.faction_id, "TRADE_PACT")
            self.set_relation(target_faction, faction.faction_id, "TRADE_PACT")
        elif treaty == "NON_AGGRESSION":
            self.set_relation(faction, target_faction.faction_id, "NON_AGGRESSION")
            self.set_relation(target_faction, faction.faction_id, "NON_AGGRESSION")
        elif treaty == "VASSAL":
            self.set_relation(faction, target_faction.faction_id, "VASSAL")
            self.set_relation(target_faction, faction.faction_id, "ALLIANCE")
        return True

    def break_treaty(self, faction: Faction, target_faction: Faction) -> None:
        treaty = self.get_relation(faction, target_faction.faction_id)
        if treaty is None:
            return
        if treaty == "VASSAL":
            self.set_relation(faction, target_faction.faction_id, "WAR")
            self.set_relation(target_faction, faction.faction_id, "WAR")
        else:
            self.remove_relation(faction, target_faction.faction_id)
            self.remove_relation(target_faction, faction.faction_id)
        faction._cohesion = max(0.0, faction.cohesion - config.ALLIANCE_BREAK_COHESION)

    def tick_diplomacy(self, faction: Faction, faction_registry: dict[int, Faction],
                       entities: dict[int, Entity]) -> list[str]:
        events: list[str] = []
        if not config.DIPLOMACY_ENABLED:
            return events
        for target_id, treaty in list(faction.diplomacy.items()):
            target_faction = faction_registry.get(target_id)
            if target_faction is None:
                self.remove_relation(faction, target_id)
                continue
            if treaty == "ALLIANCE":
                self._process_alliance_tick(faction, target_faction, entities, events)
            elif treaty == "TRADE_PACT":
                self._process_trade_pact_tick(faction, target_faction, entities, events)
            elif treaty == "NON_AGGRESSION":
                self._process_non_aggression_tick(faction, target_faction, entities, events)
            elif treaty == "VASSAL":
                self._process_vassal_tick(faction, target_faction, entities, events)
        return events

    def _process_alliance_tick(self, faction: Faction, target: Faction,
                               entities: dict[int, Entity], events: list[str]) -> None:
        if faction.is_at_war_with(target.faction_id) or target.is_at_war_with(faction.faction_id):
            self.break_treaty(faction, target)
            events.append(f"Alliance broken between {faction.name} and {target.name}")

    def _process_trade_pact_tick(self, faction: Faction, target: Faction,
                                 entities: dict[int, Entity], events: list[str]) -> None:
        pass

    def _process_non_aggression_tick(self, faction: Faction, target: Faction,
                                     entities: dict[int, Entity], events: list[str]) -> None:
        if faction.is_at_war_with(target.faction_id):
            self.remove_relation(faction, target.faction_id)
            self.remove_relation(target, faction.faction_id)
            events.append(f"Non-aggression pact broken between {faction.name} and {target.name}")

    def _process_vassal_tick(self, faction: Faction, target: Faction,
                             entities: dict[int, Entity], events: list[str]) -> None:
        tribute_events = self._collect_vassal_tribute(faction, target, entities)
        events.extend(tribute_events)

    def _collect_vassal_tribute(self, faction: Faction, overlord: Faction,
                                entities: dict[int, Entity]) -> list[str]:
        events: list[str] = []
        for member_id in list(faction.members):
            ent = entities.get(member_id)
            if ent is None or not ent.alive:
                continue
            tribute_wood = int(ent.inventory.get("wood", 0) * config.VASSAL_TRIBUTE_RATIO)
            tribute_stone = int(ent.inventory.get("stone", 0) * config.VASSAL_TRIBUTE_RATIO)
            tribute_food = int(ent.inventory.get("food", 0) * config.VASSAL_TRIBUTE_RATIO)
            if tribute_wood > 0 or tribute_stone > 0 or tribute_food > 0:
                ent.inventory["wood"] = ent.inventory.get("wood", 0) - tribute_wood
                ent.inventory["stone"] = ent.inventory.get("stone", 0) - tribute_stone
                ent.inventory["food"] = ent.inventory.get("food", 0) - tribute_food
                for overlord_member_id in overlord.members:
                    overlord_ent = entities.get(overlord_member_id)
                    if overlord_ent and overlord_ent.alive:
                        overlord_ent.inventory["wood"] = overlord_ent.inventory.get("wood", 0) + tribute_wood
                        overlord_ent.inventory["stone"] = overlord_ent.inventory.get("stone", 0) + tribute_stone
                        overlord_ent.inventory["food"] = overlord_ent.inventory.get("food", 0) + tribute_food
                        break
                if tribute_wood > 0 or tribute_stone > 0 or tribute_food > 0:
                    events.append(f"{faction.name} pays tribute to {overlord.name}")
        return events


diplomacy_manager = DiplomacyManager()
