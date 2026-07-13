"""Generate project-local PNG assets for MoonSpace."""

from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import config
from utils import palette


OUT_DIR = ROOT / "assets" / "sprites" / "moonspace"


def surf(size: tuple[int, int], color: tuple[int, int, int, int] = palette.TRANSPARENT) -> pygame.Surface:
    image = pygame.Surface(size, pygame.SRCALPHA)
    image.fill(color)
    return image


def rect(image: pygame.Surface, box: tuple[int, int, int, int], color: tuple[int, int, int] | tuple[int, int, int, int]) -> None:
    pygame.draw.rect(image, color, pygame.Rect(box))


def line(image: pygame.Surface, start: tuple[int, int], end: tuple[int, int], color: tuple[int, int, int], width: int = 1) -> None:
    pygame.draw.line(image, color, start, end, width)


def circle(image: pygame.Surface, color: tuple[int, int, int] | tuple[int, int, int, int], center: tuple[int, int], radius: int) -> None:
    pygame.draw.circle(image, color, center, radius)


def save(image: pygame.Surface, name: str) -> None:
    pygame.image.save(image, OUT_DIR / name)


def draw_player_frame(
    image: pygame.Surface,
    x: int,
    y: int,
    *,
    facing: str,
    step: int = 0,
) -> None:
    trim = palette.PALE_MOON
    robe = palette.PLAYER_ROBE
    shadow = palette.DEEP_BLUE
    hair = (7, 8, 14)
    skin = palette.SKIN_PALE

    rect(image, (x + 5, y + 1, 6, 2), hair)
    rect(image, (x + 4, y + 3, 8, 2), hair)
    rect(image, (x + 5, y + 5, 6, 5), skin)
    if facing == "left":
        rect(image, (x + 5, y + 6, 2, 1), hair)
        rect(image, (x + 10, y + 7, 1, 1), trim)
    elif facing == "right":
        rect(image, (x + 9, y + 6, 2, 1), hair)
        rect(image, (x + 5, y + 7, 1, 1), trim)
    elif facing == "up":
        rect(image, (x + 5, y + 5, 6, 3), hair)
    else:
        rect(image, (x + 6, y + 7, 1, 1), hair)
        rect(image, (x + 9, y + 7, 1, 1), hair)

    rect(image, (x + 4, y + 10, 8, 2), trim)
    rect(image, (x + 3, y + 12, 10, 9), robe)
    rect(image, (x + 5, y + 12, 2, 9), (96, 112, 150))
    rect(image, (x + 10, y + 13, 1, 8), shadow)
    rect(image, (x + 2, y + 13, 2, 6), robe)
    rect(image, (x + 12, y + 13, 2, 6), trim if step else robe)
    rect(image, (x + 5, y + 21, 3, 2 + step), shadow)
    rect(image, (x + 9, y + 21 + step, 3, 2), shadow)


def generate_player() -> None:
    image = surf((16 * 8, 24))
    frames = [
        ("down", 0),
        ("down", 1),
        ("up", 0),
        ("up", 1),
        ("left", 0),
        ("left", 1),
        ("right", 0),
        ("right", 1),
    ]
    for index, (facing, step) in enumerate(frames):
        draw_player_frame(image, index * 16, 0, facing=facing, step=step)
    save(image, "player_envoy.png")


def draw_wugang_frame(image: pygame.Surface, x: int, phase: int) -> None:
    y = 0
    skin = (175, 161, 144)
    robe = palette.WUGANG_ROBE
    dark = palette.WOOD_DARK
    axe = palette.MOON_WHITE
    rect(image, (x + 12, y + 5, 8, 7), skin)
    rect(image, (x + 14, y + 6, 4, 2), palette.SKIN_PALE)
    rect(image, (x + 10, y + 12, 12, 6), robe)
    rect(image, (x + 8, y + 17, 16, 8), robe)
    rect(image, (x + 12, y + 25, 3, 6), dark)
    rect(image, (x + 18, y + 25, 3, 6), dark)
    rect(image, (x + 13, y + 8, 2, 1), palette.ASH_GRAY)
    rect(image, (x + 18, y + 8, 2, 1), palette.ASH_GRAY)
    rect(image, (x + 14, y + 17, 2, 1), palette.ASH_GRAY)
    rect(image, (x + 18, y + 20, 2, 1), palette.ASH_GRAY)

    if phase == 0:
        line(image, (x + 23, y + 3), (x + 16, y + 20), dark, 2)
        rect(image, (x + 21, y + 1, 9, 4), axe)
    elif phase == 1:
        line(image, (x + 24, y + 8), (x + 17, y + 23), dark, 2)
        rect(image, (x + 23, y + 7, 8, 4), axe)
    elif phase == 2:
        line(image, (x + 24, y + 15), (x + 18, y + 29), dark, 2)
        rect(image, (x + 20, y + 27, 10, 4), axe)
    else:
        line(image, (x + 18, y + 7), (x + 15, y + 25), dark, 2)
        rect(image, (x + 14, y + 4, 8, 4), axe)


def generate_wugang() -> None:
    image = surf((32 * 4, 32))
    for phase in range(4):
        draw_wugang_frame(image, phase * 32, phase)
    save(image, "wugang_chop.png")


def draw_yutu_frame(image: pygame.Surface, x: int, phase: int) -> None:
    y = 0
    white = palette.YUTU_WHITE
    gray = palette.ASH_GRAY
    ear_shift = 1 if phase == 1 else 0
    rect(image, (x + 7, y + 1 - ear_shift, 2, 11), white)
    rect(image, (x + 14, y + 2 + ear_shift, 3, 10), white)
    rect(image, (x + 8, y + 10, 8, 6), white)
    rect(image, (x + 6, y + 16, 12, 5), white)
    rect(image, (x + 7, y + 17, 3, 2), (184, 188, 187))
    rect(image, (x + 5, y + 20, 4, 3), gray)
    rect(image, (x + 16, y + 19, 4, 4), gray)
    rect(image, (x + 10, y + 12, 1, 1), palette.BLOOD_RED)
    rect(image, (x + 15, y + 13, 1, 1), palette.BLOOD_RED)
    if phase < 3:
        rect(image, (x + 12, y + 12 + phase, 2, 9), palette.MOON_WHITE)
        rect(image, (x + 9, y + 21, 8, 2), palette.WOOD_DARK)
    else:
        rect(image, (x + 10, y + 18, 6, 1), palette.MOON_WHITE)


def generate_yutu() -> None:
    image = surf((24 * 4, 24))
    for phase in range(4):
        draw_yutu_frame(image, phase * 24, phase)
    save(image, "yutu_pounding.png")


def generate_laurel_tree() -> None:
    image = surf((64, 80))
    rect(image, (24, 28, 18, 45), palette.WOOD_DARK)
    rect(image, (29, 30, 5, 41), palette.WOOD_BROWN)
    rect(image, (36, 34, 4, 38), palette.LAUREL_DARK)
    rect(image, (15, 70, 36, 3), palette.WOOD_DARK)
    rect(image, (9, 72, 48, 2), palette.LAUREL_DARK)
    rect(image, (12, 9, 34, 24), palette.LAUREL_GREEN)
    rect(image, (18, 18, 10, 8), (44, 82, 58))
    rect(image, (4, 22, 28, 22), palette.LAUREL_DARK)
    rect(image, (26, 14, 30, 28), palette.LAUREL_GREEN)
    rect(image, (18, 2, 24, 15), palette.LAUREL_DARK)
    rect(image, (27, 43, 2, 2), palette.ASH_GRAY)
    rect(image, (36, 43, 2, 2), palette.ASH_GRAY)
    rect(image, (30, 52, 7, 1), palette.ASH_GRAY)
    rect(image, (32, 48, 2, 4), palette.ASH_GRAY)
    save(image, "laurel_tree.png")


def generate_moon_pool() -> None:
    image = surf((64, 40))
    rect(image, (0, 0, 64, 40), palette.DEEP_BLUE)
    rect(image, (3, 3, 58, 34), palette.PALE_MOON)
    rect(image, (4, 4, 56, 5), (29, 57, 84))
    rect(image, (7, 7, 50, 26), palette.POOL_BLUE)
    rect(image, (14, 13, 36, 2), palette.POOL_HIGHLIGHT)
    rect(image, (18, 20, 30, 2), palette.POOL_HIGHLIGHT)
    rect(image, (26, 14, 8, 12), palette.HORROR_CYAN_GRAY)
    rect(image, (30, 27, 2, 3), palette.DARK_BLOOD)
    save(image, "moon_pool.png")


def generate_small_objects() -> None:
    table = surf((24, 24))
    rect(table, (5, 10, 14, 9), palette.WOOD_BROWN)
    rect(table, (5, 10, 14, 3), (126, 88, 55))
    rect(table, (8, 5, 8, 7), palette.ASH_GRAY)
    rect(table, (10, 7, 5, 3), palette.BLACK)
    rect(table, (12, 1, 2, 12), palette.MOON_WHITE)
    rect(table, (6, 19, 3, 4), palette.WOOD_DARK)
    rect(table, (16, 19, 3, 4), palette.WOOD_DARK)
    save(table, "pound_table.png")

    sign = surf((24, 32))
    rect(sign, (2, 4, 20, 5), palette.WOOD_DARK)
    rect(sign, (4, 8, 16, 16), palette.WOOD_BROWN)
    rect(sign, (4, 8, 16, 3), (129, 87, 52))
    rect(sign, (6, 11, 11, 1), palette.MOON_WHITE)
    rect(sign, (6, 16, 9, 1), palette.MOON_WHITE)
    rect(sign, (6, 21, 12, 1), palette.MOON_WHITE)
    rect(sign, (18, 17, 1, 6), palette.DARK_BLOOD)
    rect(sign, (5, 24, 3, 8), palette.WOOD_DARK)
    rect(sign, (16, 24, 3, 8), palette.WOOD_DARK)
    save(sign, "sign_board.png")


def generate_palace_wall() -> None:
    image = surf((config.SCREEN_WIDTH, 80), palette.TRANSPARENT)
    rect(image, (0, 0, config.SCREEN_WIDTH, 14), palette.DEEP_BLUE)
    rect(image, (0, 14, config.SCREEN_WIDTH, 48), palette.PALACE_STONE)
    rect(image, (0, 14, config.SCREEN_WIDTH, 5), (63, 70, 96))
    rect(image, (0, 62, config.SCREEN_WIDTH, 18), palette.GROUND_MID)
    for x in range(0, config.SCREEN_WIDTH, 48):
        rect(image, (x + 4, 16, 36, 6), palette.DEEP_BLUE)
        rect(image, (x + 12, 25, 8, 8), palette.ASH_GRAY)
        rect(image, (x + 20, 8, 12, 2), palette.DARK_BLOOD)
    rect(image, (220, 26, 56, 34), palette.BLACK)
    rect(image, (239, 12, 8, 48), palette.PALE_MOON)
    rect(image, (236, 32, 2, 2), palette.PALE_MOON)
    rect(image, (258, 32, 2, 2), palette.PALE_MOON)
    save(image, "palace_wall_bg.png")


def generate_courtyard_bg() -> None:
    image = surf((config.SCREEN_WIDTH, config.MAP_HEIGHT), palette.GROUND_DARK)
    for y in range(0, config.MAP_HEIGHT, config.TILE_SIZE):
        for x in range(0, config.SCREEN_WIDTH, config.TILE_SIZE):
            value = (x * 17 + y * 31) % 9
            color = palette.GROUND_DARK
            if value in (0, 3):
                color = (31, 42, 64)
            elif value in (1, 5):
                color = palette.GROUND_MID
            elif value == 7:
                color = palette.GROUND_LIGHT
            rect(image, (x, y, config.TILE_SIZE, config.TILE_SIZE), color)
            rect(image, (x, y + 15, config.TILE_SIZE, 1), (22, 27, 43))
            rect(image, (x + 15, y, 1, config.TILE_SIZE), (24, 29, 45))
            if y >= 32 and value % 3 == 0:
                rect(image, (x + 3 + value, y + 4, 2, 1), palette.ASH_GRAY)
            if y >= 32 and value == 5:
                rect(image, (x + 11, y + 11, 2, 1), palette.LAUREL_DARK)

    wall = pygame.image.load(str(OUT_DIR / "palace_wall_bg.png"))
    image.blit(wall, (0, 0))
    rect(image, (0, 78, config.SCREEN_WIDTH, 4), (20, 25, 40))
    rect(image, (212, 126, 88, 50), (24, 32, 50))
    rect(image, (218, 132, 76, 38), (38, 55, 78))
    rect(image, (225, 141, 60, 2), palette.POOL_HIGHLIGHT)
    rect(image, (230, 154, 50, 2), palette.POOL_HIGHLIGHT)
    save(image, "courtyard_bg.png")


def generate_main_menu_bg() -> None:
    image = surf((config.SCREEN_WIDTH, config.SCREEN_HEIGHT), palette.NIGHT_BLACK)
    for y in range(0, config.SCREEN_HEIGHT, 16):
        rect(image, (0, y, config.SCREEN_WIDTH, 1), (22, 27, 43))
    rect(image, (0, 48, config.SCREEN_WIDTH, 8), (49, 56, 84))
    circle(image, palette.DARK_BLOOD, (240, 58), 34)
    circle(image, palette.BLOOD_RED, (240, 58), 27)
    rect(image, (0, 176, config.SCREEN_WIDTH, 94), palette.GROUND_DARK)
    rect(image, (80, 140, 320, 50), palette.PALACE_STONE)
    rect(image, (106, 126, 268, 18), palette.DEEP_BLUE)
    rect(image, (220, 146, 40, 44), palette.BLACK)
    rect(image, (238, 137, 5, 44), palette.PALE_MOON)
    for x in range(32, config.SCREEN_WIDTH, 64):
        rect(image, (x, 156, 20, 34), palette.DEEP_BLUE)
        rect(image, (x + 5, 146, 10, 10), palette.PALACE_STONE)
    save(image, "main_menu_bg.png")


def generate_opening_cg() -> None:
    room = surf((config.SCREEN_WIDTH, config.SCREEN_HEIGHT), palette.NIGHT_BLACK)
    rect(room, (18, 18, 120, 8), (38, 43, 61))
    rect(room, (0, 176, config.SCREEN_WIDTH, 94), palette.GROUND_DARK)
    rect(room, (46, 28, 104, 76), (8, 8, 14))
    rect(room, (46, 28, 104, 76), palette.MOON_WHITE)
    rect(room, (170, 154, 140, 14), palette.WOOD_BROWN)
    rect(room, (196, 91, 90, 56), palette.BLACK)
    rect(room, (204, 99, 74, 36), palette.DEEP_BLUE)
    save(room, "opening_cg_room.png")

    moon = surf((config.SCREEN_WIDTH, config.SCREEN_HEIGHT), (8, 8, 14, 255))
    rect(moon, (0, 0, config.SCREEN_WIDTH, 16), (118, 18, 34))
    rect(moon, (36, 24, 408, 206), palette.PALE_MOON)
    rect(moon, (42, 30, 396, 194), (8, 8, 14))
    circle(moon, palette.DARK_BLOOD, (240, 112), 58)
    circle(moon, palette.BLOOD_RED, (240, 112), 47)
    rect(moon, (236, 24, 6, 206), palette.DEEP_BLUE)
    rect(moon, (36, 126, 408, 6), palette.DEEP_BLUE)
    save(moon, "opening_cg_blood_moon.png")

    pullback = room.copy()
    overlay = surf((config.SCREEN_WIDTH, config.SCREEN_HEIGHT), (192, 57, 43, 42))
    pullback.blit(overlay, (0, 0))
    rect(pullback, (0, 0, config.SCREEN_WIDTH, 18), (84, 31, 45))
    rect(pullback, (42, 24, 104, 76), palette.PALE_MOON)
    circle(pullback, palette.BLOOD_RED, (112, 52), 18)
    rect(pullback, (230, 126, 26, 64), palette.PLAYER_ROBE)
    save(pullback, "opening_cg_moonlight.png")

    blackout = surf((config.SCREEN_WIDTH, config.SCREEN_HEIGHT), palette.BLACK)
    rect(blackout, (0, 0, config.SCREEN_WIDTH, 12), (82, 6, 16))
    rect(blackout, (232, 130, 16, 2), palette.BLOOD_RED)
    save(blackout, "opening_cg_blackout.png")


def main() -> None:
    pygame.init()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    generate_player()
    generate_wugang()
    generate_yutu()
    generate_laurel_tree()
    generate_moon_pool()
    generate_small_objects()
    generate_palace_wall()
    generate_courtyard_bg()
    generate_main_menu_bg()
    generate_opening_cg()
    pygame.quit()
    print(f"Generated MoonSpace PNG assets in {OUT_DIR}")


if __name__ == "__main__":
    main()
