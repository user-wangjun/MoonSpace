"""Tests for staged image_gen large-map candidate assets."""

from __future__ import annotations

import os
import shutil
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame
import pytest

from tools.stage_imagegen_v4_large_assets import (
    OUT_DIR,
    PLAYER_FRAME_SIZE,
    SCREEN_SIZE,
    WUGANG_FRAME_SIZE,
    WORLD_SIZE,
    YUTU_FRAME_SIZE,
    main as stage_large_assets,
)


def image_size(path: Path) -> tuple[int, int]:
    image = pygame.image.load(str(path)).convert_alpha()
    return image.get_size()


@pytest.fixture(autouse=True)
def pygame_display():
    pygame.init()
    pygame.display.set_mode((1, 1))
    yield
    pygame.quit()


def test_stage_imagegen_v4_large_assets_outputs_expected_sizes():
    stage_large_assets()
    pygame.init()
    pygame.display.set_mode((1, 1))

    expected = {
        "courtyard_bg_large.png": WORLD_SIZE,
        "main_menu_bg.png": SCREEN_SIZE,
        "opening_cg_room.png": SCREEN_SIZE,
        "opening_cg_moonlight.png": SCREEN_SIZE,
        "opening_cg_blood_moon.png": SCREEN_SIZE,
        "opening_cg_blackout.png": SCREEN_SIZE,
        "player_envoy_large.png": (PLAYER_FRAME_SIZE[0] * 4, PLAYER_FRAME_SIZE[1] * 4),
        "wugang_chop_large.png": (WUGANG_FRAME_SIZE[0] * 4, WUGANG_FRAME_SIZE[1] * 4),
        "yutu_pounding_large.png": (YUTU_FRAME_SIZE[0] * 4, YUTU_FRAME_SIZE[1] * 4),
    }

    for filename, size in expected.items():
        assert image_size(OUT_DIR / filename) == size


def test_stage_imagegen_v4_large_assets_uses_complete_player_sheet():
    shutil.rmtree(OUT_DIR, ignore_errors=True)
    stage_large_assets()
    pygame.init()
    pygame.display.set_mode((1, 1))

    player_sheet = pygame.image.load(str(OUT_DIR / "player_envoy_large.png")).convert_alpha()

    assert player_sheet.get_width() == PLAYER_FRAME_SIZE[0] * 4
    assert player_sheet.get_height() == PLAYER_FRAME_SIZE[1] * 4


def test_stage_imagegen_v4_large_assets_uses_16_frame_npc_sheets():
    stage_large_assets()
    pygame.init()
    pygame.display.set_mode((1, 1))

    wugang_sheet = pygame.image.load(str(OUT_DIR / "wugang_chop_large.png")).convert_alpha()
    yutu_sheet = pygame.image.load(str(OUT_DIR / "yutu_pounding_large.png")).convert_alpha()

    assert wugang_sheet.get_size() == (WUGANG_FRAME_SIZE[0] * 4, WUGANG_FRAME_SIZE[1] * 4)
    assert yutu_sheet.get_size() == (YUTU_FRAME_SIZE[0] * 4, YUTU_FRAME_SIZE[1] * 4)
