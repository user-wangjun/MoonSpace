"""残破玉简拾取界面测试。"""

import pygame

import config
from ui.broken_jade import BrokenJadeView
from utils.assets import load_image


class FakeInput:
    def __init__(self, pressed: str = "") -> None:
        self.pressed = pressed

    def was_pressed(self, action: str) -> bool:
        return action == self.pressed


def test_broken_jade_assets_load_with_runtime_sizes_and_alpha():
    item = load_image(BrokenJadeView.ITEM_PATH)

    assert item.get_flags() & pygame.SRCALPHA
    assert item.get_at((0, 0)).a == 0


def test_broken_jade_view_opens_on_acquire_then_inspects_and_closes():
    view = BrokenJadeView()
    view.acquire()

    assert view.acquired is True
    assert view.active is True

    view.update(FakeInput(config.ACTION_INTERACT))

    assert view.active is True
    assert view.stage == view.STAGE_INSPECT

    view.update(FakeInput(config.ACTION_INTERACT))

    assert view.active is False


def test_broken_jade_view_draws_without_text_or_frame_clipping():
    view = BrokenJadeView()
    view.acquire()
    surface = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT), pygame.SRCALPHA)

    view.draw(surface)

    assert surface.get_bounding_rect().size == surface.get_size()


def test_broken_jade_pickup_includes_reason_for_unreadable_text(monkeypatch):
    import ui.broken_jade as broken_jade_module

    rendered = []
    monkeypatch.setattr(
        broken_jade_module,
        "render_text",
        lambda surface, text, *args: rendered.append(text) or True,
    )
    view = BrokenJadeView()
    view.acquire()
    view.draw(pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT), pygame.SRCALPHA))

    assert BrokenJadeView.PICKUP_EXPLANATION in rendered
