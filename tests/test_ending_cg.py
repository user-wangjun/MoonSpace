"""结局 CG 测试。"""

import pygame

from ui.ending_cg import EndingCG


class FakeInput:
    def __init__(self, pressed: set[str] | None = None) -> None:
        self.pressed = pressed or set()

    def was_pressed(self, action: str) -> bool:
        return action in self.pressed


def test_ending_cg_finishes_after_duration():
    cg = EndingCG()
    cg.start("he_return_earth")

    finished = cg.update(cg.TOTAL_DURATION, FakeInput())

    assert finished is True
    assert cg.finished is True
    assert cg.active is False


def test_ending_cg_can_skip_with_interact():
    cg = EndingCG()
    cg.start("he_return_earth")

    finished = cg.update(0.1, FakeInput({"interact"}))

    assert finished is True
    assert cg.finished is True
    assert cg.active is False


def test_ending_cg_draws_he_scene():
    cg = EndingCG()
    cg.start("he_return_earth")
    cg.time = 5.0
    surface = pygame.Surface((480, 270), pygame.SRCALPHA)

    cg.draw(surface)

    assert surface.get_bounding_rect().width > 0
    assert "地球" in cg.current_caption()


def test_ending_cg_has_assets_for_mainline_endings():
    expected = {
        "he_return_earth": "cg/he_earth_return.png",
        "be_wugang": "cg/be_wugang_pollution.png",
        "be_yutu": "cg/be_yutu_pollution.png",
        "be_double": "cg/be_double_pollution.png",
        "be_laurel_mixed": "cg/be_double_pollution.png",
        "be_change": "cg/be_wait_trap.png",
    }

    assert EndingCG.ASSET_BY_ENDING == expected


def test_ending_cg_uses_be_specific_caption():
    cg = EndingCG()
    cg.start("be_yutu")
    cg.time = 3.0

    assert "杵声" in cg.current_caption()


def test_ending_cg_declares_three_formal_shots_for_each_fixed_ending():
    fixed_ids = {"he_return_earth", "be_wugang", "be_yutu", "be_double", "be_change"}

    assert fixed_ids.issubset(EndingCG.SHOT_ASSETS_BY_ENDING)
    assert all(len(EndingCG.SHOT_ASSETS_BY_ENDING[ending_id]) == 3 for ending_id in fixed_ids)
    assert EndingCG.SHOT_ASSETS_BY_ENDING["be_laurel_mixed"] == EndingCG.SHOT_ASSETS_BY_ENDING["be_double"]


def test_ending_cg_shot_boundaries_are_stable():
    assert [EndingCG.shot_index_at(t) for t in (0.0, 2.399, 2.4, 5.199, 5.2, 8.0)] == [0, 0, 1, 1, 2, 2]


def test_ending_cg_audio_cues_are_declared_for_each_fixed_ending():
    fixed_ids = {"he_return_earth", "be_wugang", "be_yutu", "be_double", "be_change"}

    assert fixed_ids.issubset(EndingCG.AUDIO_CUES_BY_ENDING)
    assert all(EndingCG.AUDIO_CUES_BY_ENDING[ending_id] for ending_id in fixed_ids)
