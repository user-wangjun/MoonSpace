"""玉兔 NPC 测试。"""

import pygame

import config
from core.event_bus import DIALOG_ACTIVE_CHANGED, EventBus, YUTU_POUNDING_CHANGED
from entities.yutu import Yutu
from utils import palette
from utils.assets import load_image


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


def test_yutu_complete_animation_keeps_original_cell_dimensions():
    assert Yutu.BODY_SPRITE_PATH != Yutu.LEGACY_LARGE_SPRITE_PATH
    assert load_image(Yutu.BODY_SPRITE_PATH).get_size() == (256, 312)
    assert load_image(Yutu.PESTLE_OVERLAY_PATH).get_size() == (256, 312)


def test_yutu_does_not_overlay_obsolete_detached_hands(monkeypatch):
    import entities.yutu as module
    original = module.load_sprite_grid
    def load_grid(path, *args):
        if path == Yutu.PESTLE_OVERLAY_PATH:
            obsolete = pygame.Surface((64, 78), pygame.SRCALPHA)
            obsolete.fill((255, 0, 255))
            return [[obsolete] * 4 for _ in range(4)]
        return original(path, *args)
    monkeypatch.setattr(module, "load_sprite_grid", load_grid)
    yutu = Yutu(EventBus(), 100, 120)
    surface = pygame.Surface((240, 240), pygame.SRCALPHA)
    yutu.draw(surface)
    assert not any(surface.get_at((x, y))[:3] == (255, 0, 255) for x in range(90, 180) for y in range(50, 145))


def test_yutu_animation_feet_do_not_float_between_frames():
    yutu = Yutu(EventBus(), 100, 120)
    for frame in range(16):
        yutu.current_frame = frame
        surface = pygame.Surface((240, 240), pygame.SRCALPHA)
        yutu.draw(surface)
        assert surface.get_bounding_rect(min_alpha=8).bottom == 136


def test_yutu_visual_anchor_includes_layer_alignment_offset():
    yutu = Yutu(EventBus(), 700, 300)

    assert yutu.get_visual_rect().centerx == yutu.rect.centerx + Yutu.DRAW_OFFSET_X


def test_yutu_collision_follows_visible_feet_not_old_sprite_origin():
    yutu = Yutu(EventBus())
    footprint = yutu.get_collision_rect()
    assert footprint.midbottom == yutu.get_visual_rect().midbottom
    assert footprint.height <= 12
    assert not footprint.collidepoint(yutu.rect.midleft)
