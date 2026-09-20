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

    transition.update(transition.SEARCH_DURATION)

    assert transition.active
    assert transition.progress == pytest.approx(transition.FOUND_PROGRESS)
    assert transition.reveal_started
    assert completed == []

    transition.update(transition.REVEAL_DURATION)
    assert transition.progress == pytest.approx(
        (transition.SEARCH_DURATION + transition.REVEAL_DURATION) / transition.TOTAL_DURATION
    )
    assert transition.active

    transition.update(transition.FINAL_HOLD_DURATION)

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


def test_scene_transition_says_found_you_after_search_phase():
    transition = SceneTransition()
    surface = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT), pygame.SRCALPHA)
    transition.start(lambda: None)

    transition.update(transition.SEARCH_DURATION)
    transition.draw(surface)

    colors = {
        surface.get_at((x, y))[:3]
        for x in range(config.SCREEN_WIDTH)
        for y in range(config.SCREEN_HEIGHT)
        if surface.get_at((x, y)).a > 0
    }

    assert transition.reveal_started
    assert transition.found_message == "找到你了！"
    assert palette.BLOOD_RED in colors


def test_scene_transition_renders_exact_found_message_over_atlas_text(monkeypatch):
    transition = SceneTransition()
    surface = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT), pygame.SRCALPHA)
    rendered_texts = []

    def fake_render_text(_surface, text, _x, _y, _size=14, _color=palette.MOON_WHITE):
        rendered_texts.append(text)
        return True

    monkeypatch.setattr("ui.scene_transition.render_text", fake_render_text)
    transition.start(lambda: None)
    transition.update(transition.SEARCH_DURATION)
    transition.update(transition.REVEAL_DURATION)
    transition.draw(surface)

    assert "找到你了！" in rendered_texts


def test_scene_transition_large_first_update_still_holds_reveal_frame():
    transition = SceneTransition()
    completed = []
    transition.start(lambda: completed.append(True))

    transition.update(transition.TOTAL_DURATION - transition.FINAL_HOLD_DURATION)

    assert transition.active
    assert transition.progress == pytest.approx(
        (transition.SEARCH_DURATION + transition.REVEAL_DURATION) / transition.TOTAL_DURATION
    )
    assert transition.reveal_started
    assert completed == []

    transition.update(transition.FINAL_HOLD_DURATION)

    assert not transition.active
    assert completed == [True]


def test_scene_transition_callback_runs_once_after_completion():
    transition = SceneTransition()
    completed = []
    transition.start(lambda: completed.append(True))

    transition.update(transition.TOTAL_DURATION)
    transition.update(transition.FINAL_HOLD_DURATION)
    transition.update(transition.FINAL_HOLD_DURATION)

    assert completed == [True]


def test_scene_transition_found_callback_runs_once():
    transition = SceneTransition()
    found = []
    completed = []
    transition.start(lambda: completed.append(True), on_found=lambda: found.append(True))

    transition.update(transition.SEARCH_DURATION)
    transition.update(transition.REVEAL_DURATION)
    transition.update(transition.FINAL_HOLD_DURATION)
    transition.update(transition.FINAL_HOLD_DURATION)

    assert found == [True]
    assert completed == [True]


def test_scene_transition_uses_all_monitor_sequence_phases():
    transition = SceneTransition()
    transition.start(lambda: None)

    assert transition._monitor_frame_index() == 0

    transition.progress = 0.97
    assert transition._monitor_frame_index() == transition.SEARCH_FRAME_END

    transition.reveal_started = True
    assert transition._monitor_frame_index() == transition.REVEAL_FRAME_START

    transition._reveal_elapsed = transition.REVEAL_DURATION
    assert transition._monitor_frame_index() == transition.REVEAL_FRAME_END


def test_scene_transition_draws_user_reference_sheet_inside_monitor():
    transition = SceneTransition()
    surface = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT), pygame.SRCALPHA)
    transition.start(lambda: None)

    assert transition._draw_monitor_sequence(surface) is True
    assert surface.get_at(transition.MONITOR_FRAME_RECT.center).a > 0


def test_scene_transition_search_advances_authored_frames_without_screen_jitter():
    transition = SceneTransition()
    transition.start(lambda: None)
    transition.progress = 0.0
    first_frame = transition._monitor_frame_index()
    first_zoom = transition._monitor_zoom()

    transition.progress = 0.25
    transition.search_offset = 3
    assert transition._monitor_frame_index() > first_frame
    assert transition._monitor_zoom() > first_zoom

    frame_with_offset = transition._monitor_frame_index()
    transition.search_offset = -3
    assert transition._monitor_frame_index() == frame_with_offset

    transition.reveal_started = True
    transition._reveal_elapsed = transition.REVEAL_DURATION / 2

    assert transition._monitor_frame_index() > transition.SEARCH_FRAME_END
    assert transition._monitor_zoom() > transition.SEARCH_END_ZOOM


def test_scene_transition_camera_push_is_monotonic_before_final_rush():
    transition = SceneTransition()
    transition.start(lambda: None)

    transition.progress = 0.0
    start_zoom = transition._monitor_zoom()
    transition.progress = 0.5
    middle_zoom = transition._monitor_zoom()
    transition.progress = transition.FOUND_PROGRESS
    end_search_zoom = transition._monitor_zoom()

    transition.reveal_started = True
    transition._reveal_elapsed = 0.0
    reveal_start_zoom = transition._monitor_zoom()
    transition._reveal_elapsed = transition.REVEAL_DURATION
    final_zoom = transition._monitor_zoom()

    assert start_zoom < middle_zoom < end_search_zoom
    assert reveal_start_zoom == pytest.approx(transition.SEARCH_END_ZOOM)
    assert final_zoom == pytest.approx(transition.REVEAL_MAX_ZOOM)


def test_scene_transition_uses_the_longer_user_requested_timeline():
    assert SceneTransition.SEARCH_DURATION == pytest.approx(3.0)
    assert SceneTransition.REVEAL_DURATION == pytest.approx(0.8)
    assert SceneTransition.FINAL_HOLD_DURATION == pytest.approx(1.4)
    assert SceneTransition.TOTAL_DURATION == pytest.approx(5.2)
