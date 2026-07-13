"""显示模式与全屏缩放测试。"""

import pygame

from core.game import Game
from core.input_manager import InputManager


def test_f11_requests_fullscreen_toggle():
    manager = InputManager()

    manager.process_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_F11))

    assert manager.fullscreen_toggle_requested


def test_alt_enter_requests_fullscreen_toggle():
    manager = InputManager()

    manager.process_event(
        pygame.event.Event(
            pygame.KEYDOWN,
            key=pygame.K_RETURN,
            mod=pygame.KMOD_ALT,
        )
    )

    assert manager.fullscreen_toggle_requested
    assert not manager.was_key_pressed(pygame.K_RETURN)


def test_plain_enter_remains_available_to_menu_input():
    manager = InputManager()

    manager.process_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN, mod=0))

    assert not manager.fullscreen_toggle_requested
    assert manager.was_key_pressed(pygame.K_RETURN)


def test_begin_frame_clears_fullscreen_toggle_request():
    manager = InputManager()
    manager.process_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_F11))

    manager.begin_frame()

    assert not manager.fullscreen_toggle_requested


def test_scaled_game_rect_preserves_aspect_ratio_and_centers():
    rect = Game._scaled_game_rect((1920, 1200))

    assert rect == pygame.Rect(0, 60, 1920, 1080)
