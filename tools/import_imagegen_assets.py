"""Import image_gen atlases into MoonSpace runtime PNG assets."""

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


SOURCE_DIR = ROOT / "assets" / "source" / "imagegen"
OUT_DIR = ROOT / "assets" / "sprites" / "moonspace"
SCENE_ATLAS = SOURCE_DIR / "moonspace_scene_atlas.png"
SPRITE_ATLAS = SOURCE_DIR / "moonspace_sprite_atlas.png"


def save_scaled(source: pygame.Surface, rect: pygame.Rect, size: tuple[int, int], name: str) -> None:
    crop = pygame.Surface(rect.size, pygame.SRCALPHA)
    crop.blit(source, (0, 0), rect)
    scaled = pygame.transform.scale(crop, size)
    pygame.image.save(scaled, OUT_DIR / name)


def scaled_crop(source: pygame.Surface, rect: pygame.Rect, size: tuple[int, int]) -> pygame.Surface:
    crop = pygame.Surface(rect.size, pygame.SRCALPHA)
    crop.blit(source, (0, 0), rect)
    return pygame.transform.scale(crop, size)


def import_scene_atlas() -> None:
    atlas = pygame.image.load(str(SCENE_ATLAS)).convert_alpha()
    width, height = atlas.get_size()
    gutter = max(2, width // 450)
    half_w = width // 2
    half_h = height // 2
    quadrants = {
        "courtyard_bg.png": pygame.Rect(0, 0, half_w - gutter, half_h - gutter),
        "main_menu_bg.png": pygame.Rect(half_w + gutter, 0, width - half_w - gutter, half_h - gutter),
        "opening_cg_room.png": pygame.Rect(0, half_h + gutter, half_w - gutter, height - half_h - gutter),
        "opening_cg_blood_moon.png": pygame.Rect(half_w + gutter, half_h + gutter, width - half_w - gutter, height - half_h - gutter),
    }
    courtyard = scaled_crop(atlas, quadrants["courtyard_bg.png"], (config.SCREEN_WIDTH, config.MAP_HEIGHT))
    pygame.image.save(courtyard, OUT_DIR / "courtyard_bg.png")
    wall = pygame.Surface((config.SCREEN_WIDTH, 80), pygame.SRCALPHA)
    wall.blit(courtyard, (0, 0), pygame.Rect(0, 0, config.SCREEN_WIDTH, 80))
    pygame.image.save(wall, OUT_DIR / "palace_wall_bg.png")
    save_scaled(atlas, quadrants["main_menu_bg.png"], (config.SCREEN_WIDTH, config.SCREEN_HEIGHT), "main_menu_bg.png")
    save_scaled(atlas, quadrants["opening_cg_room.png"], (config.SCREEN_WIDTH, config.SCREEN_HEIGHT), "opening_cg_room.png")
    save_scaled(atlas, quadrants["opening_cg_room.png"], (config.SCREEN_WIDTH, config.SCREEN_HEIGHT), "opening_cg_moonlight.png")
    save_scaled(
        atlas,
        quadrants["opening_cg_blood_moon.png"],
        (config.SCREEN_WIDTH, config.SCREEN_HEIGHT),
        "opening_cg_blood_moon.png",
    )
    save_scaled(
        atlas,
        quadrants["opening_cg_blood_moon.png"],
        (config.SCREEN_WIDTH, config.SCREEN_HEIGHT),
        "opening_cg_blackout.png",
    )


def is_green_key(color: tuple[int, int, int, int]) -> bool:
    r, g, b, _a = color
    return g > 120 and g > r + 40 and g > b + 40


def non_green_mask(surface: pygame.Surface) -> list[list[bool]]:
    width, height = surface.get_size()
    return [
        [not is_green_key(surface.get_at((x, y))) for x in range(width)]
        for y in range(height)
    ]


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
            if count > 60:
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
    rect = rect.inflate(8, 8).clip(source.get_rect())
    crop = make_transparent_crop(source, rect)
    target = pygame.Surface(size, pygame.SRCALPHA)
    scale = min(size[0] / crop.get_width(), size[1] / crop.get_height())
    scaled_size = (max(1, int(crop.get_width() * scale)), max(1, int(crop.get_height() * scale)))
    scaled = pygame.transform.scale(crop, scaled_size)
    target.blit(scaled, ((size[0] - scaled_size[0]) // 2, (size[1] - scaled_size[1]) // 2))
    return target


def save_sheet(source: pygame.Surface, rects: list[pygame.Rect], frame_size: tuple[int, int], name: str) -> None:
    sheet = pygame.Surface((frame_size[0] * len(rects), frame_size[1]), pygame.SRCALPHA)
    for index, rect in enumerate(rects):
        frame = fit_sprite(source, rect, frame_size)
        sheet.blit(frame, (index * frame_size[0], 0))
    pygame.image.save(sheet, OUT_DIR / name)


def save_sprite(source: pygame.Surface, rect: pygame.Rect, size: tuple[int, int], name: str) -> None:
    pygame.image.save(fit_sprite(source, rect, size), OUT_DIR / name)


def group_rows(rects: list[pygame.Rect]) -> list[list[pygame.Rect]]:
    sorted_rects = sorted(rects, key=lambda rect: rect.centery)
    rows: list[list[pygame.Rect]] = []
    for rect in sorted_rects:
        for row in rows:
            if abs(row[0].centery - rect.centery) < 75:
                row.append(rect)
                break
        else:
            rows.append([rect])
    return [sorted(row, key=lambda rect: rect.centerx) for row in rows]


def import_sprite_atlas() -> None:
    atlas = pygame.image.load(str(SPRITE_ATLAS)).convert_alpha()
    rows = group_rows(connected_components(atlas))
    if len(rows) < 4:
        raise RuntimeError(f"Expected at least 4 sprite rows, found {len(rows)}")

    player = rows[0][:8]
    wugang = sorted(sorted(rows[1], key=lambda rect: rect.width * rect.height, reverse=True)[:4], key=lambda rect: rect.centerx)
    yutu_row = rows[3] if len(rows) > 4 else rows[2]
    yutu = (yutu_row[:3] + yutu_row[-1:])[:4]
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
    pygame.init()
    pygame.display.set_mode((1, 1))
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    import_scene_atlas()
    import_sprite_atlas()
    pygame.quit()
    print(f"Imported image_gen assets into {OUT_DIR}")


if __name__ == "__main__":
    main()
