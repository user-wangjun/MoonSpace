"""Render MoonSpace screens with staged v3 image_gen preview assets."""

from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pygame

import config
from core.game import Game
from ui.main_menu import MainMenu
from ui.opening_cg import OpeningCG
from utils.assets import clear_asset_cache

from stage_imagegen_v3_preview import OUT_DIR as STAGED_ASSET_DIR
from stage_imagegen_v3_preview import main as stage_preview_assets


OUT_DIR = ROOT / "tmp" / "imagegen-v3-preview" / "screenshots"
PREVIEW_ROOT = STAGED_ASSET_DIR.parents[2]


def save_main_menu() -> None:
    clear_asset_cache()
    surface = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT), pygame.SRCALPHA)
    MainMenu().draw(surface)
    pygame.image.save(surface, OUT_DIR / "main_menu_render.png")


def save_opening_cg() -> None:
    clear_asset_cache()
    surface = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT), pygame.SRCALPHA)
    cg = OpeningCG()
    frames = (
        (1.0, "opening_01_room_render.png"),
        (4.2, "opening_02_window_render.png"),
        (7.0, "opening_03_blood_moon_render.png"),
        (10.0, "opening_04_moonlight_render.png"),
        (14.2, "opening_05_blackout_render.png"),
    )
    for time_value, filename in frames:
        surface.fill((0, 0, 0, 0))
        cg.time = time_value
        cg.draw(surface)
        pygame.image.save(surface, OUT_DIR / filename)


def save_gameplay() -> None:
    clear_asset_cache()
    game = Game()
    game.mode = game.MODE_PLAYING
    game._draw_playing()
    pygame.image.save(game.game_surface, OUT_DIR / "gameplay_render.png")


def main() -> None:
    stage_preview_assets()
    setattr(sys, "_MEIPASS", str(PREVIEW_ROOT))
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    pygame.init()
    pygame.display.set_mode((config.WINDOW_WIDTH, config.WINDOW_HEIGHT))
    save_main_menu()
    save_opening_cg()
    save_gameplay()
    pygame.quit()
    print(f"Rendered v3 preview screenshots into {OUT_DIR}")


if __name__ == "__main__":
    main()
