"""NPC 基类测试。"""

import pygame

from core.event_bus import DIALOG_ACTIVE_CHANGED, EventBus, SHOW_DIALOG
from entities.npc_base import NPCBase


def test_npc_detects_player_in_interaction_range():
    bus = EventBus()
    npc = NPCBase("npc", 50, 50, 16, 24, ["hello"], bus)

    npc.update(0.1, pygame.Rect(45, 45, 16, 24))

    assert npc.player_in_range


def test_npc_interact_emits_dialog():
    bus = EventBus()
    npc = NPCBase("npc", 50, 50, 16, 24, ["hello"], bus)
    received = []
    bus.subscribe(SHOW_DIALOG, lambda **payload: received.append(payload))
    npc.update(0.1, pygame.Rect(45, 45, 16, 24))

    triggered = npc.interact()

    assert triggered
    assert received == [{"speaker_id": "npc", "lines": ["hello"]}]


def test_npc_does_not_interact_out_of_range():
    bus = EventBus()
    npc = NPCBase("npc", 50, 50, 16, 24, ["hello"], bus)
    npc.update(0.1, pygame.Rect(200, 200, 16, 24))

    assert npc.interact() is False


def test_npc_does_not_interact_when_dialog_active():
    bus = EventBus()
    npc = NPCBase("npc", 50, 50, 16, 24, ["hello"], bus)
    npc.update(0.1, pygame.Rect(45, 45, 16, 24))
    bus.emit(DIALOG_ACTIVE_CHANGED, active=True)

    assert npc.interact() is False
