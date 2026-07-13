"""玉兔 NPC 测试。"""

import pygame

import config
from core.event_bus import DIALOG_ACTIVE_CHANGED, EventBus, YUTU_POUNDING_CHANGED
from entities.yutu import Yutu
from utils import palette


def test_yutu_keeps_pounding_when_player_near_so_eye_contact_rule_remains_active():
    bus = EventBus()
    yutu = Yutu(bus)
    received = []
    bus.subscribe(YUTU_POUNDING_CHANGED, lambda **payload: received.append(payload))
    near_player = pygame.Rect(0, 0, 16, 24)
    near_player.center = yutu.interaction_rect.center

    yutu.update(0.1, near_player)

    assert yutu.player_in_range is True
    assert yutu.is_pounding is True
    assert received == []


def test_yutu_stops_pounding_during_dialog_and_resumes_after_close():
    bus = EventBus()
    yutu = Yutu(bus)
    received = []
    bus.subscribe(YUTU_POUNDING_CHANGED, lambda **payload: received.append(payload))
    bus.emit(DIALOG_ACTIVE_CHANGED, active=True, speaker_id="yutu")
    yutu.update(0.1)
    bus.emit(DIALOG_ACTIVE_CHANGED, active=False, speaker_id="yutu")
    yutu.update(0.1)

    assert yutu.is_pounding is True
    assert received == [{"is_pounding": False}, {"is_pounding": True}]


def test_yutu_interaction_rect_reaches_past_pound_table_on_back_side():
    yutu = Yutu(EventBus())
    reachable_player = pygame.Rect(740, 300, 16, 24)

    assert yutu.can_interact(reachable_player)
    assert reachable_player.centerx >= yutu.rect.right


def test_yutu_draw_uses_body_eye_and_pestle_colors():
    bus = EventBus()
    yutu = Yutu(bus)
    surface = pygame.Surface((config.MAP_WIDTH, config.MAP_HEIGHT))

    yutu.draw(surface)

    sample = yutu.rect.inflate(44, 44).clip(surface.get_rect())
    colors = {
        surface.get_at((x, y))[:4]
        for x in range(sample.left, sample.right)
        for y in range(sample.top, sample.bottom)
        if surface.get_at((x, y)).a > 0
    }
    assert len(colors) > 20


def test_yutu_draw_uses_png_pounding_sprite():
    bus = EventBus()
    yutu = Yutu(bus)
    surface = pygame.Surface((config.MAP_WIDTH, config.MAP_HEIGHT), pygame.SRCALPHA)

    yutu.draw(surface)

    sample = yutu.rect.inflate(56, 56).clip(surface.get_rect())
    colors = {
        surface.get_at((x, y))[:4]
        for x in range(sample.left, sample.right)
        for y in range(sample.top, sample.bottom)
        if surface.get_at((x, y)).a > 0
    }
    assert len(colors) > 20
