"""主菜单测试。"""

import pygame

import config
from ui.main_menu import MainMenu
from utils import palette


def test_main_menu_can_be_created():
    menu = MainMenu()

    assert menu.selected_action is None


def test_main_menu_update_advances_animation_time():
    menu = MainMenu()

    menu.update(0.5, type("FakeInput", (), {
        "was_pressed": lambda self, action: False,
        "was_key_pressed": lambda self, key: False,
    })())

    assert menu.animation_time == 0.5


def test_main_menu_draw_uses_moonspace_palette():
    menu = MainMenu()
    surface = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))

    menu.draw(surface)

    colors = {
        surface.get_at((x, y))[:3]
        for x in range(config.SCREEN_WIDTH)
        for y in range(config.SCREEN_HEIGHT)
    }
    assert palette.BLOOD_RED in colors
    assert palette.PALE_MOON in colors
    assert len(colors) > 200


def test_main_menu_draw_uses_png_scene_background():
    menu = MainMenu()
    surface = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT), pygame.SRCALPHA)

    menu.draw(surface)

    colors = {
        surface.get_at((x, y))[:3]
        for x in range(config.SCREEN_WIDTH)
        for y in range(config.SCREEN_HEIGHT)
    }
    assert len(colors) > 200


def test_main_menu_text_layout_has_padding_and_no_overlap():
    menu = MainMenu()

    layout = menu.layout()
    panel = layout["panel"]
    title = layout["title"]
    item_rects = layout["items"]
    esc = layout["esc"]

    assert panel.left >= 20
    assert panel.right <= config.SCREEN_WIDTH - 20
    assert panel.bottom <= config.SCREEN_HEIGHT - 24
    assert title.left >= panel.left + 18
    assert title.right <= panel.right - 18
    assert title.top >= panel.top + 14
    assert item_rects[-1].bottom <= panel.bottom - 18
    for upper, lower in zip(item_rects, item_rects[1:]):
        assert upper.bottom + 6 <= lower.top
    assert esc.right <= config.SCREEN_WIDTH - 12
    assert esc.bottom <= config.SCREEN_HEIGHT - 12


def test_main_menu_uses_straight_panel_with_safe_text_area():
    menu = MainMenu()

    layout = menu.layout()
    panel = layout["panel"]
    panel_points = layout["panel_points"]
    inner_points = layout["inner_points"]

    assert panel_points == (
        panel.topleft,
        panel.topright,
        panel.bottomright,
        panel.bottomleft,
    )
    assert inner_points == (
        (panel.left + 10, panel.top + 10),
        (panel.right - 10, panel.top + 10),
        (panel.right - 10, panel.bottom - 10),
        (panel.left + 10, panel.bottom - 10),
    )
    for rect in [layout["title"], *layout["items"]]:
        assert rect.left >= panel.left + 34
        assert rect.right <= panel.right - 34


def test_main_menu_panel_keeps_background_visible():
    menu = MainMenu()
    surface = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT), pygame.SRCALPHA)

    menu.draw(surface)
    layout = menu.layout()
    panel = layout["panel"]
    sample = surface.get_at((panel.left + 20, panel.top + 22))[:3]

    assert sample != palette.BLACK
