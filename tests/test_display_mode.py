"""显示模式与全屏缩放测试。"""

import os
from pathlib import Path
import subprocess
import sys
import textwrap

import pygame
import pytest

from core.game import Game
from core.input_manager import InputManager


@pytest.fixture
def check_display():
    # Keep native display formats and cached surfaces out of the main test
    # process, whose other tests use SDL's dummy display driver.
    def run(assertions):
        setup = """
import pygame
from core.game import Game
pygame.display.init()
game = Game.__new__(Game)
game.windowed_size = (960, 540)
game.fullscreen = False
game.display_surface = game._set_display_mode(False)
"""
        env = dict(os.environ, SDL_VIDEODRIVER="windows" if sys.platform == "win32" else "dummy")
        result = subprocess.run(
            [sys.executable, "-c", setup + textwrap.dedent(assertions)],
            cwd=Path(__file__).resolve().parents[1],
            env=env, capture_output=True, text=True, timeout=30,
        )
        assert result.returncode == 0, result.stdout + result.stderr
    return run


def test_window_can_be_resized_and_maximized(check_display):
    check_display("assert game.display_surface.get_flags() & pygame.RESIZABLE")


def test_fullscreen_roundtrip_restores_resized_window(check_display):
    check_display("""
    game.display_surface = pygame.display.set_mode((1200, 700), pygame.RESIZABLE)

    game._toggle_fullscreen()

    assert game.fullscreen
    assert game.display_surface.get_flags() & pygame.FULLSCREEN

    game._toggle_fullscreen()

    assert not game.fullscreen
    assert game.windowed_size == (1200, 700)
    # The dummy driver keeps the desktop size after leaving fullscreen.
    if pygame.display.get_driver() != "dummy":
        assert game.display_surface.get_size() == (1200, 700)
    assert game.display_surface.get_flags() & pygame.RESIZABLE
    """)


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


def test_mouse_drag_events_keep_position_motion_and_button_state():
    manager = InputManager()
    manager.process_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(20, 30)))
    manager.process_event(
        pygame.event.Event(pygame.MOUSEMOTION, pos=(28, 25), rel=(8, -5), buttons=(1, 0, 0))
    )

    assert manager.was_mouse_pressed(1)
    assert manager.mouse_button_down(1)
    assert manager.mouse_position == (28, 25)
    assert manager.mouse_motion == pygame.Vector2(8, -5)

    manager.begin_frame()
    assert not manager.was_mouse_pressed(1)
    assert manager.mouse_button_down(1)
    assert manager.mouse_motion == pygame.Vector2()

    manager.process_event(pygame.event.Event(pygame.MOUSEBUTTONUP, button=1, pos=(28, 25)))
    assert manager.was_mouse_released(1)
    assert not manager.mouse_button_down(1)


def test_scaled_game_rect_preserves_aspect_ratio_and_centers():
    rect = Game._scaled_game_rect((1920, 1200))

    assert rect == pygame.Rect(0, 60, 1920, 1080)
