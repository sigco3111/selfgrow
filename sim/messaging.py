"""SmartBrain 메시징 시스템 — outbox 수집 및 mailbox 배달."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .world import World


def process_brain_messages(world: World) -> None:
    """SmartBrain의 outbox 메시지를 수집해 대상 개체의 mailbox로 배달."""
    messages: list = []
    for entity in world.entities.values():
        if not entity.alive:
            continue
        if hasattr(entity.brain, "outbox"):
            messages.extend(entity.brain.outbox)
            entity.brain.outbox.clear()

    for msg in messages:
        target = world.entities.get(msg.target_id)
        if target and target.alive:
            if not hasattr(target, "mailbox"):
                continue
            target.mailbox.append(msg)
