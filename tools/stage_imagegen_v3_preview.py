"""Stage v3 image_gen candidate assets without replacing runtime assets."""

from __future__ import annotations

import os
import sys
from collections import deque
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import config


CANDIDATE_DIR = ROOT / "assets" / "source" / "imagegen" / "candidates"
OUT_DIR = ROOT / "tmp" / "imagegen-v3-preview" / "assets" / "sprites" / "moonspace"

GAMEPLAY_MAP = CANDIDATE_DIR / "candidate_gameplay_courtyard_clean_bg_horror_v4.png"
SPRITE_ATLAS = CANDIDATE_DIR / "candidate_characters_npcs_horror_v3.png"
MAIN_MENU = CANDIDATE_DIR / "candidate_main_menu_scene_horror_v3.png"
OPENING_STORYBOARD = CANDIDATE_DIR / "candidate_opening_cg_storyboard_horror_v3.png"


def save_scaled(source: pygame.Surface, rect: pygame.Rect, size: tuple[int, int], name: str) -> None:
    crop = pygame.Surface(rect.size, pygame.SRCALPHA)
    crop.blit(source, (0, 0), rect)
    scaled = pygame.transform.scale(crop, size)
    pygame.image.save(scaled, OUT_DIR / name)


def save_full_scaled(path: Path, size: tuple[int, int], name: str) -> None:
    source = pygame.image.load(str(path)).convert_alpha()
    scaled = pygame.transform.scale(source, size)
    pygame.image.save(scaled, OUT_DIR / name)


def panel_rects(source: pygame.Surface) -> dict[str, pygame.Rect]:
    width, height = source.get_size()
    gutter = max(4, min(width, height) // 120)
    half_w = width // 2
    half_h = height // 2
    return {
        "top_left": pygame.Rect(0, 0, half_w - gutter, half_h - gutter),
        "top_right": pygame.Rect(half_w + gutter, 0, width - half_w - gutter, half_h - gutter),
        "bottom_left": pygame.Rect(0, half_h + gutter, half_w - gutter, height - half_h - gutter),
        "bottom_right": pygame.Rect(half_w + gutter, half_h + gutter, width - half_w - gutter, height - half_h - gutter),
    }


def stage_scene_backgrounds() -> None:
    save_full_scaled(MAIN_MENU, (config.SCREEN_WIDTH, config.SCREEN_HEIGHT), "main_menu_bg.png")

    gameplay = pygame.image.load(str(GAMEPLAY_MAP)).convert_alpha()
    gameplay_rect = gameplay.get_rect()
    save_scaled(gameplay, gameplay_rect, (config.SCREEN_WIDTH, config.MAP_HEIGHT), "courtyard_bg.png")
    save_scaled(gameplay, pygame.Rect(0, 0, gameplay.get_width(), gameplay.get_height() // 3), (config.SCREEN_WIDTH, 80), "palace_wall_bg.png")

    storyboard = pygame.image.load(str(OPENING_STORYBOARD)).convert_alpha()
    panels = panel_rects(storyboard)
    save_scaled(storyboard, panels["top_left"], (config.SCREEN_WIDTH, config.SCREEN_HEIGHT), "opening_cg_room.png")
    save_scaled(storyboard, panels["top_right"], (config.SCREEN_WIDTH, config.SCREEN_HEIGHT), "opening_cg_moonlight.png")
    save_scaled(storyboard, panels["bottom_left"], (config.SCREEN_WIDTH, config.SCREEN_HEIGHT), "opening_cg_blood_moon.png")
    save_scaled(storyboard, panels["bottom_right"], (config.SCREEN_WIDTH, config.SCREEN_HEIGHT), "opening_cg_blackout.png")


def is_green_key(color: tuple[int, int, int, int]) -> bool:
    r, g, b, _a = color
    return g > 130 and g > r + 35 and g > b + 35


def non_green_mask(surface: pygame.Surface) -> list[list[bool]]:
    width, height = surface.get_size()
    return [[not is_green_key(surface.get_at((x, y))) for x in range(width)] for y in range(height)]


def connected_components(surface: pygame.Surface) -> list[pygame.Rect]:
    width, height = surface.get_size()
    mask = non_green_mask(surface)
    seen = [[False for _x in range(width)] for _y in range(height)]
    rects: list[pygame.Rect] = []

    for y in range(height):
        for x in range(width):
            if seen[y][x] or not mask[y][x]:
                continue
            queue: deque[tuple[int, int]] = deque([(x, y)])
            seen[y][x] = True
            min_x = max_x = x
            min_y = max_y = y
            count = 0
            while queue:
                px, py = queue.popleft()
                count += 1
                min_x = min(min_x, px)
                max_x = max(max_x, px)
                min_y = min(min_y, py)
                max_y = max(max_y, py)
                for nx, ny in ((px - 1, py), (px + 1, py), (px, py - 1), (px, py + 1)):
                    if 0 <= nx < width and 0 <= ny < height and not seen[ny][nx] and mask[ny][nx]:
                        seen[ny][nx] = True
                        queue.append((nx, ny))
            if count > 80:
                rects.append(pygame.Rect(min_x, min_y, max_x - min_x + 1, max_y - min_y + 1))
    return rects


def make_transparent_crop(source: pygame.Surface, rect: pygame.Rect) -> pygame.Surface:
    crop = pygame.Surface(rect.size, pygame.SRCALPHA)
    crop.blit(source, (0, 0), rect)
    for y in range(crop.get_height()):
        for x in range(crop.get_width()):
            color = crop.get_at((x, y))
            if is_green_key(color):
                crop.set_at((x, y), (0, 0, 0, 0))
    return crop


def fit_sprite(source: pygame.Surface, rect: pygame.Rect, size: tuple[int, int]) -> pygame.Surface:
    padded_rect = rect.inflate(8, 8).clip(source.get_rect())
    crop = make_transparent_crop(source, padded_rect)
    target = pygame.Surface(size, pygame.SRCALPHA)
    scale = min(size[0] / crop.get_width(), size[1] / crop.get_height())
    scaled_size = (max(1, int(crop.get_width() * scale)), max(1, int(crop.get_height() * scale)))
    scaled = pygame.transform.scale(crop, scaled_size)
    target.blit(scaled, ((size[0] - scaled_size[0]) // 2, (size[1] - scaled_size[1]) // 2))
    return target


def save_sheet(source: pygame.Surface, rects: list[pygame.Rect], frame_size: tuple[int, int], name: str) -> None:
    sheet = pygame.Surface((frame_size[0] * len(rects), frame_size[1]), pygame.SRCALPHA)
    for index, rect in enumerate(rects):
        sheet.blit(fit_sprite(source, rect, frame_size), (index * frame_size[0], 0))
    pygame.image.save(sheet, OUT_DIR / name)


def save_sprite(source: pygame.Surface, rect: pygame.Rect, size: tuple[int, int], name: str) -> None:
    pygame.image.save(fit_sprite(source, rect, size), OUT_DIR / name)


def group_rows(rects: list[pygame.Rect]) -> list[list[pygame.Rect]]:
    sorted_rects = sorted(rects, key=lambda rect: rect.centery)
    rows: list[list[pygame.Rect]] = []
    for rect in sorted_rects:
        for row in rows:
            if abs(row[0].centery - rect.centery) < 90:
                row.append(rect)
                break
        else:
            rows.append([rect])
    return [sorted(row, key=lambda rect: rect.centerx) for row in rows]


def stage_sprite_assets() -> None:
    atlas = pygame.image.load(str(SPRITE_ATLAS)).convert_alpha()
    rows = group_rows(connected_components(atlas))
    if len(rows) < 4:
        raise RuntimeError(f"Expected at least 4 sprite rows, found {len(rows)}")

    player = rows[0][:8]
    wugang = sorted(sorted(rows[1], key=lambda rect: rect.width * rect.height, reverse=True)[:4], key=lambda rect: rect.centerx)
    yutu = sorted(sorted(rows[2], key=lambda rect: rect.width * rect.height, reverse=True)[:4], key=lambda rect: rect.centerx)
    objects = sorted(rows[-1], key=lambda rect: rect.centerx)
    if len(player) != 8 or len(wugang) != 4 or len(yutu) != 4 or len(objects) < 5:
        raise RuntimeError(
            f"Unexpected sprite layout: player={len(player)} wugang={len(wugang)} "
            f"yutu={len(yutu)} objects={len(objects)}"
        )

    save_sheet(atlas, player, (16, 24), "player_envoy.png")
    save_sheet(atlas, wugang, (32, 32), "wugang_chop.png")
    save_sheet(atlas, yutu, (24, 24), "yutu_pounding.png")
    save_sprite(atlas, objects[0], (64, 80), "laurel_tree.png")
    save_sprite(atlas, objects[1], (64, 40), "moon_pool.png")
    save_sprite(atlas, objects[2], (24, 24), "pound_table.png")
    save_sprite(atlas, objects[3], (24, 32), "sign_board.png")


def main() -> None:
    for path in (GAMEPLAY_MAP, SPRITE_ATLAS, MAIN_MENU, OPENING_STORYBOARD):
        if not path.exists():
            raise FileNotFoundError(path)

    pygame.init()
    pygame.display.set_mode((1, 1))
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    stage_scene_backgrounds()
    stage_sprite_assets()
    pygame.quit()
    print(f"Staged v3 preview assets into {OUT_DIR}")


if __name__ == "__main__":
    main()
