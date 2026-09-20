"""吴刚 NPC 测试。"""

import pygame
import pytest

import config
from core.event_bus import EventBus, TREE_BLEEDING
from entities.wugang import Wugang


def test_wugang_feet_remain_planted_across_all_chop_poses():
    wugang = Wugang(EventBus(), 100, 120)
    bottoms = []
    for frame in range(16):
        wugang.current_frame = frame
        surface = pygame.Surface((240, 240), pygame.SRCALPHA)
        wugang.draw(surface)
        bottoms.append(surface.get_bounding_rect(min_alpha=8).bottom)
    assert set(bottoms) == {144}
from utils import palette
from world.laurel_tree import LaurelTree


def test_wugang_emits_tree_bleeding_on_fifth_chop():
    bus = EventBus()
    wugang = Wugang(bus)
    received = []
    bus.subscribe(TREE_BLEEDING, lambda **payload: received.append(payload))

    wugang.update(10.0)

    assert wugang.chop_count == 5
    assert received == [{"source": "wugang"}]


def test_wugang_chop_frame_advances_before_full_chop():
    bus = EventBus()
    wugang = Wugang(bus)

    wugang.update(0.6)

    assert wugang.chop_count == 0
    assert wugang.current_frame > 0


def test_wugang_draw_uses_body_skin_and_axe_colors():
    bus = EventBus()
    wugang = Wugang(bus)
    surface = pygame.Surface((config.MAP_WIDTH, config.MAP_HEIGHT))

    wugang.draw(surface)

    sample = wugang.rect.inflate(44, 44).clip(surface.get_rect())
    colors = {
        surface.get_at((x, y))[:4]
        for x in range(sample.left, sample.right)
        for y in range(sample.top, sample.bottom)
        if surface.get_at((x, y)).a > 0
    }
    assert len(colors) > 20


def test_wugang_draw_uses_png_chop_sprite():
    bus = EventBus()
    wugang = Wugang(bus)
    surface = pygame.Surface((config.MAP_WIDTH, config.MAP_HEIGHT), pygame.SRCALPHA)

    wugang.draw(surface)

    sample = wugang.rect.inflate(56, 56).clip(surface.get_rect())
    colors = {
        surface.get_at((x, y))[:4]
        for x in range(sample.left, sample.right)
        for y in range(sample.top, sample.bottom)
        if surface.get_at((x, y)).a > 0
    }
    assert len(colors) > 20


def test_wugang_default_position_stands_by_laurel_tree():
    bus = EventBus()
    tree = LaurelTree()
    wugang = Wugang(bus)

    assert wugang.rect.left >= tree.rect.right
    assert wugang.rect.left - tree.rect.right <= 36
    assert wugang.rect.colliderect(tree.rect.inflate(42, 42))


@pytest.mark.parametrize("frame_index", range(16))
def test_wugang_chop_cycle_uses_held_axe_poses(monkeypatch, frame_index):
    bus = EventBus()
    wugang = Wugang(bus)
    wugang.current_frame = frame_index
    surface = pygame.Surface((config.MAP_WIDTH, config.MAP_HEIGHT), pygame.SRCALPHA)
    frame_width = 76
    frame_height = 92
    grid = []
    # The neutral/recovery cells omit the prop; hold the nearest complete pose.
    drawn_index = (1, 1, 3, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 13, 13)[frame_index]
    expected = (
        (drawn_index * 13 + 17) % 255,
        (drawn_index * 29 + 31) % 255,
        (drawn_index * 47 + 43) % 255,
    )

    for row in range(4):
        grid_row = []
        for col in range(4):
            frame = pygame.Surface((frame_width, frame_height), pygame.SRCALPHA)
            frame.fill((0, 0, 0, 0))
            cell_index = row * 4 + col
            color = (
                (cell_index * 13 + 17) % 255,
                (cell_index * 29 + 31) % 255,
                (cell_index * 47 + 43) % 255,
            )
            frame.fill((*color, 255))
            grid_row.append(frame)
        grid.append(grid_row)

    monkeypatch.setattr("entities.wugang.load_sprite_grid", lambda *args: grid)

    wugang.draw(surface)

    sprite_left = wugang.rect.centerx - frame_width // 2
    sprite_top = wugang.rect.bottom - frame_height
    assert surface.get_at((sprite_left + 2, sprite_top + 2))[:3] == expected
    assert surface.get_at((sprite_left + frame_width - 3, sprite_top + 2))[:3] == expected


def test_wugang_full_chop_cycle_reaches_frame_15_then_wraps():
    wugang = Wugang(EventBus())

    wugang.update(1.875)
    assert wugang.current_frame == 15
    assert wugang.chop_count == 0

    wugang.update(0.125)
    assert wugang.current_frame == 0
    assert wugang.chop_count == 1


def test_wugang_rest_pauses_chopping_and_then_resumes():
    bus = EventBus()
    wugang = Wugang(bus)
    received = []
    bus.subscribe(TREE_BLEEDING, lambda **payload: received.append(payload))

    wugang.rest(10.0)
    wugang.update(9.5)

    assert wugang.is_resting is True
    assert wugang.chop_count == 0
    assert wugang.current_frame == 0
    assert received == []

    wugang.update(0.6)
    assert wugang.is_resting is False
    assert wugang.anim_state == "chop"

    wugang.update(wugang.CHOP_INTERVAL)

    assert wugang.chop_count == 1
    assert received == []
