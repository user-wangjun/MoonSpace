"""开场 CG 测试。"""

import pygame

import config
from ui.opening_cg import OpeningCG


class FakeInput:
    def __init__(self, pressed=None):
        self.pressed = set(pressed or [])

    def was_pressed(self, action):
        return action in self.pressed


class FakeAudio:
    def __init__(self):
        self.calls = []

    def begin_cg_cycle(self):
        self.calls.append(("begin",))

    def play_cg_cue(self, key, *, token):
        self.calls.append(("play", key, token))

    def stop_cg_sounds(self):
        self.calls.append(("stop",))


def test_opening_cg_finishes_after_duration():
    cg = OpeningCG()
    cg.start()

    finished = cg.update(cg.TOTAL_DURATION, FakeInput())

    assert finished
    assert cg.finished
    assert not cg.active


def test_opening_cg_can_skip_with_interact():
    cg = OpeningCG()
    cg.start()

    finished = cg.update(0.1, FakeInput({"interact"}))

    assert finished
    assert cg.finished


def test_opening_cg_exposes_story_caption_for_each_act():
    cg = OpeningCG()

    cg.time = 1.0
    assert "MoonSpace" in cg.current_caption()

    cg.time = 4.2
    assert "血月" in cg.current_caption()

    cg.time = 10.0
    assert "红光" in cg.current_caption()

    cg.time = 14.2
    assert "月宫" in cg.current_caption()


def test_opening_cg_draw_uses_png_scene_backgrounds():
    cg = OpeningCG()
    surface = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT), pygame.SRCALPHA)
    expected_times = (1.0, 7.0, 10.0, 14.2)

    for time in expected_times:
        surface.fill((0, 0, 0, 0))
        cg.time = time
        cg.draw(surface)
        colors = {
            surface.get_at((x, y))[:3]
            for x in range(config.SCREEN_WIDTH)
            for y in range(config.SCREEN_HEIGHT)
        }
        assert len(colors) > 100


def test_opening_cg_declares_eight_formal_shots_without_changing_total_duration():
    assert len(OpeningCG.SHOT_ASSETS) == 8
    assert OpeningCG.SHOT_ASSETS[0][0] == 0.0
    assert OpeningCG.SHOT_ASSETS[-1][1] == OpeningCG.TOTAL_DURATION


def test_opening_cg_audio_cues_fire_once_and_stop_on_skip():
    audio = FakeAudio()
    cg = OpeningCG(audio)
    cg.start()
    cg.update(10.0, FakeInput())
    cg.update(5.0, FakeInput())

    played = [call[1] for call in audio.calls if call[0] == "play"]
    assert played == ["cg_download_start", "cg_download_complete", "cg_blood_moon", "cg_screen_crack"]
    assert audio.calls[-1] == ("stop",)

    cg.start()
    cg.update(0.1, FakeInput({"interact"}))
    assert audio.calls[-1] == ("stop",)
