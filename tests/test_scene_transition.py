"""Scene transition UI tests."""

import pygame
import pytest

import config
from utils import palette
from ui.scene_transition import SceneTransition


def test_scene_transition_loads_then_holds_on_reveal():
    transition = SceneTransition()
    completed = []

    transition.start(lambda: completed.append(True), "月门正在核验来使身份")

    assert transition.active
    assert transition.progress == 0.0
    assert "月门" in transition.caption

    transition.update(transition.LOAD_DURATION * transition.FOUND_PROGRESS)

    assert transition.active
    assert transition.progress == pytest.approx(transition.FOUND_PROGRESS)
    assert transition.reveal_started
    assert completed == []

    transition.update(transition.LOAD_DURATION * (1 - transition.FOUND_PROGRESS))
    assert transition.progress == 1.0
    assert transition.active

    transition.update(transition.REVEAL_HOLD)

    assert not transition.active
    assert completed == [True]


def test_scene_transition_draws_progress_bar_and_reveal_eye():
    transition = SceneTransition()
    surface = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT), pygame.SRCALPHA)
    transition.start(lambda: None)

    transition.update(transition.LOAD_DURATION * transition.FOUND_PROGRESS)
    transition.draw(surface)

    colors = {
        surface.get_at((x, y))[:3]
        for x in range(config.SCREEN_WIDTH)
        for y in range(config.SCREEN_HEIGHT)
        if surface.get_at((x, y)).a > 0
    }

    assert len(colors) > 30
    assert palette.BLOOD_RED in colors


def test_scene_transition_searches_before_found_progress():
    transition = SceneTransition()
    transition.start(lambda: None)

    transition.update(transition.LOAD_DURATION * 0.5)

    assert not transition.reveal_started
    assert transition.search_offset != 0


def test_scene_transition_says_found_you_after_98_percent():
    transition = SceneTransition()
    surface = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT), pygame.SRCALPHA)
    transition.start(lambda: None)

    transition.update(transition.LOAD_DURATION * transition.FOUND_PROGRESS)
    transition.draw(surface)

    colors = {
        surface.get_at((x, y))[:3]
        for x in range(config.SCREEN_WIDTH)
        for y in range(config.SCREEN_HEIGHT)
        if surface.get_at((x, y)).a > 0
    }

    assert transition.reveal_started
    assert transition.found_message == "找到你了"
    assert palette.BLOOD_RED in colors


def test_scene_transition_large_first_update_still_holds_reveal_frame():
    transition = SceneTransition()
    completed = []
    transition.start(lambda: completed.append(True))

    transition.update(transition.LOAD_DURATION + transition.REVEAL_HOLD + 1.0)

    assert transition.active
    assert transition.progress == 1.0
    assert transition.reveal_started
    assert completed == []

    transition.update(transition.REVEAL_HOLD)

    assert not transition.active
    assert completed == [True]


def test_scene_transition_callback_runs_once_after_completion():
    transition = SceneTransition()
    completed = []
    transition.start(lambda: completed.append(True))

    transition.update(transition.LOAD_DURATION)
    transition.update(transition.REVEAL_HOLD)
    transition.update(transition.REVEAL_HOLD)

    assert completed == [True]


def test_scene_transition_found_callback_runs_once():
    transition = SceneTransition()
    found = []
    completed = []
    transition.start(lambda: completed.append(True), on_found=lambda: found.append(True))

    transition.update(transition.LOAD_DURATION * transition.FOUND_PROGRESS)
    transition.update(transition.LOAD_DURATION)
    transition.update(transition.REVEAL_HOLD)
    transition.update(transition.REVEAL_HOLD)

    assert found == [True]
    assert completed == [True]


def test_scene_transition_uses_all_monitor_sequence_phases():
    transition = SceneTransition()
    transition.start(lambda: None)

    assert transition._monitor_frame_index() == 0

    transition.progress = 0.97
    assert transition._monitor_frame_index() == 21

    transition.reveal_started = True
    assert transition._monitor_frame_index() == 22

    transition._reveal_elapsed = transition.REVEAL_HOLD
    assert transition._monitor_frame_index() == 23


def test_scene_transition_draws_user_reference_sheet_inside_monitor():
    transition = SceneTransition()
    surface = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT), pygame.SRCALPHA)
    transition.start(lambda: None)

    assert transition._draw_monitor_sequence(surface) is True
    assert surface.get_at(transition.MONITOR_FRAME_RECT.center).a > 0
