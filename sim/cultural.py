"""문화적 진화 — 언어, 관습, 지식 전수."""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Callable, Optional

if TYPE_CHECKING:
    from .world import World
    from .entity import Entity


@dataclass
class Culture:
    """문화 — 언어, 관습, 전통을 포함."""
    language: str = "basic"
    customs: set[str] = field(default_factory=set)
    traditions: list[str] = field(default_factory=list)
    
    def merge(self, other: "Culture", strength: float = 0.3) -> "Culture":
        """다른 문화와 합병."""
        new_language = self.language if random.random() < 0.5 else other.language
        new_customs = self.customs.copy()
        
        for custom in other.customs:
            if random.random() < strength:
                new_customs.add(custom)
        
        new_traditions = self.traditions.copy()
        for tradition in other.traditions:
            if random.random() < strength and tradition not in new_traditions:
                new_traditions.append(tradition)
        
        return Culture(
            language=new_language,
            customs=new_customs,
            traditions=new_traditions,
        )


CULTURE_LANGUAGES = ["basic", "trade", "martial", "scholarly", "spiritual"]
CULTURE_CUSTOMS = [
    "hospitality", "trade_friendly", "martial_honor",
    "scholarly_pursuit", "spiritual_practice", "communal_living",
    "seasonal_festival", "craft_tradition", "exploration_love",
]


def determine_culture(entity: Entity, rng: random.Random) -> Culture:
    """개체의 유전자 형질에 따라 문화 결정."""
    genome = entity.genome
    
    if genome.sociability > 0.7:
        language = "trade"
    elif genome.curiosity > 0.7:
        language = "scholarly"
    elif genome.aggression > 0.7:
        language = "martial"
    elif genome.industry > 0.7:
        language = "spiritual"
    else:
        language = "basic"
    
    customs = set()
    if genome.sociability > 0.5:
        customs.add("hospitality")
    if genome.industry > 0.5:
        customs.add("trade_friendly")
    if genome.aggression > 0.5:
        customs.add("martial_honor")
    if genome.curiosity > 0.5:
        customs.add("scholarly_pursuit")
    if genome.endurance > 0.5:
        customs.add("communal_living")
    
    return Culture(language=language, customs=customs)


def cultural_transfer(
    world: World,
    rng: random.Random,
    log_event: Callable[[dict], None],
) -> None:
    """인접 개체 간 문화적 전파 (지식 + 언어 + 관습)."""
    for entity in list(world.entities.values()):
        if not entity.alive or entity.genome.sociability < 0.2:
            continue
        
        if not hasattr(entity, "culture"):
            entity.culture = determine_culture(entity, rng)
        
        for eid, other in world.entities_near(entity.x, entity.y, 1):
            if other is entity or not other.alive:
                continue
            
            if not hasattr(other, "culture"):
                other.culture = determine_culture(other, rng)
            
            # 지식 전수
            transferred = entity.knowledge.share(
                other.knowledge, entity.genome.sociability,
                rng=rng,
            )
            for tech in transferred:
                log_event({
                    "tick": world.tick,
                    "type": "knowledge_transfer",
                    "entity_id": entity.eid,
                    "entity_name": entity.name,
                    "data": {"from": entity.name, "to": other.name,
                             "tech": tech},
                })
            
            # 언어 전파
            if entity.culture.language != other.culture.language:
                if rng.random() < entity.genome.sociability * 0.3:
                    old_lang = other.culture.language
                    other.culture.language = entity.culture.language
                    log_event({
                        "tick": world.tick,
                        "type": "language_transfer",
                        "entity_id": other.eid,
                        "entity_name": other.name,
                        "data": {"from": entity.name, "to": other.name,
                                 "old_language": old_lang,
                                 "new_language": entity.culture.language},
                    })
            
            # 관습 전파
            for custom in entity.culture.customs:
                if custom not in other.culture.customs:
                    if rng.random() < entity.genome.sociability * 0.2:
                        other.culture.customs.add(custom)
                        log_event({
                            "tick": world.tick,
                            "type": "custom_transfer",
                            "entity_id": other.eid,
                            "entity_name": other.name,
                            "data": {"from": entity.name, "to": other.name,
                                     "custom": custom},
                        })
