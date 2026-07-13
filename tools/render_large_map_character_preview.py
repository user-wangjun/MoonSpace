"""Render large-map character clarity previews without replacing game assets."""

from __future__ import annotations

import os
from collections import deque
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_DIR = ROOT / "assets" / "source" / "imagegen" / "candidates"
OUT_DIR = ROOT / "tmp" / "imagegen-large-map-preview"

SCREEN_SIZE = (480, 270)
WORLD_SIZE = (960, 540)

BACKGROUND = CANDIDATE_DIR / "candidate_gameplay_courtyard_clean_bg_horror_v4.png"
PLAYER_ATLAS = CANDIDATE_DIR / "candidate_player_envoy_16frames_horror_v6.png"
WUGANG_ATLAS = CANDIDATE_DIR / "candidate_wugang_16frames_horror_v7.png"
YUTU_ATLAS = CANDIDATE_DIR / "candidate_yutu_16frames_horror_v7.png"


def is_green_key(color: tuple[int, int, int, int]) -> bool:
    r, g, b, _a = color
    return g > 130 and g > r + 35 and g > b + 35


def component_rects(surface: pygame.Surface) -> list[pygame.Rect]:
    width, height = surface.get_size()
    seen = [[False for _x in range(width)] for _y in range(height)]
    rects: list[pygame.Rect] = []
    for y in range(height):
        for x in range(width):
            if seen[y][x] or is_green_key(surface.get_at((x, y))):
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
                    if 0 <= nx < width and 0 <= ny < height and not seen[ny][nx]:
                        seen[ny][nx] = True
                        if not is_green_key(surface.get_at((nx, ny))):
                            queue.append((nx, ny))
            if count > 120:
                rects.append(pygame.Rect(min_x, min_y, max_x - min_x + 1, max_y - min_y + 1))
    return rects


def grouped_rows(rects: list[pygame.Rect]) -> list[list[pygame.Rect]]:
    rows: list[list[pygame.Rect]] = []
    for rect in sorted(rects, key=lambda item: item.centery):
        for row in rows:
            if abs(row[0].centery - rect.centery) < 115:
                row.append(rect)
                break
        else:
            rows.append([rect])
    return [sorted(row, key=lambda item: item.centerx) for row in rows]


def grid_frames(path: Path, expected_rows: int, expected_cols: int) -> list[list[pygame.Rect]]:
    atlas = pygame.image.load(str(path)).convert_alpha()
    rows = grouped_rows(component_rects(atlas))
    if len(rows) == expected_rows and all(len(row) == expected_cols for row in rows):
        return rows

    cell_width = atlas.get_width() // expected_cols
    cell_height = atlas.get_height() // expected_rows
    return [
        [
            pygame.Rect(col * cell_width, row * cell_height, cell_width, cell_height)
            for col in range(expected_cols)
        ]
        for row in range(expected_rows)
    ]


def transparent_crop(source: pygame.Surface, rect: pygame.Rect) -> pygame.Surface:
    rect = rect.inflate(10, 10).clip(source.get_rect())
    crop = pygame.Surface(rect.size, pygame.SRCALPHA)
    crop.blit(source, (0, 0), rect)
    for y in range(crop.get_height()):
        for x in range(crop.get_width()):
            color = crop.get_at((x, y))
            if is_green_key(color):
                crop.set_at((x, y), (0, 0, 0, 0))
    return crop


def fit_sprite(source: pygame.Surface, rect: pygame.Rect, target_size: tuple[int, int]) -> pygame.Surface:
    crop = transparent_crop(source, rect)
    scale = min(target_size[0] / crop.get_width(), target_size[1] / crop.get_height())
    scaled_size = (max(1, int(crop.get_width() * scale)), max(1, int(crop.get_height() * scale)))
    scaled = pygame.transform.scale(crop, scaled_size)
    target = pygame.Surface(target_size, pygame.SRCALPHA)
    target.blit(scaled, ((target_size[0] - scaled_size[0]) // 2, target_size[1] - scaled_size[1]))
    return target


def extract_preview_sprites(
    *,
    player_size: tuple[int, int] = (42, 62),
    wugang_size: tuple[int, int] = (76, 92),
    yutu_size: tuple[int, int] = (64, 78),
) -> dict[str, pygame.Surface]:
    player_atlas = pygame.image.load(str(PLAYER_ATLAS)).convert_alpha()
    player_frames = grid_frames(PLAYER_ATLAS, 4, 4)

    wugang_atlas = pygame.image.load(str(WUGANG_ATLAS)).convert_alpha()
    wugang_frames = grid_frames(WUGANG_ATLAS, 4, 4)

    yutu_atlas = pygame.image.load(str(YUTU_ATLAS)).convert_alpha()
    yutu_frames = grid_frames(YUTU_ATLAS, 4, 4)
    return {
        "player": fit_sprite(player_atlas, player_frames[0][0], player_size),
        "wugang": fit_sprite(wugang_atlas, wugang_frames[0][0], wugang_size),
        "yutu": fit_sprite(yutu_atlas, yutu_frames[0][0], yutu_size),
    }


def make_world() -> pygame.Surface:
    background = pygame.image.load(str(BACKGROUND)).convert_alpha()
    world = pygame.transform.scale(background, WORLD_SIZE)
    vignette = pygame.Surface(WORLD_SIZE, pygame.SRCALPHA)
    pygame.draw.rect(vignette, (0, 0, 0, 70), pygame.Rect(0, 0, WORLD_SIZE[0], WORLD_SIZE[1]), 24)
    world.blit(vignette, (0, 0))
    return world


def draw_sprite_bottom(surface: pygame.Surface, sprite: pygame.Surface, bottom_center: tuple[int, int]) -> None:
    x = bottom_center[0] - sprite.get_width() // 2
    y = bottom_center[1] - sprite.get_height()
    surface.blit(sprite, (x, y))


def draw_collision_preview(surface: pygame.Surface) -> None:
    """Draw collision boxes for internal scale checks only."""
    for center, size in (((480, 360), (16, 24)), ((260, 300), (16, 24)), ((710, 320), (16, 16))):
        rect = pygame.Rect(0, 0, *size)
        rect.midbottom = center
        pygame.draw.rect(surface, (120, 220, 190, 130), rect, 1)


def compose_world(*, show_collision_boxes: bool = False) -> pygame.Surface:
    world = make_world()
    sprites = extract_preview_sprites()

    draw_sprite_bottom(world, sprites["player"], (480, 360))
    draw_sprite_bottom(world, sprites["wugang"], (260, 300))
    draw_sprite_bottom(world, sprites["yutu"], (710, 320))

    if show_collision_boxes:
        draw_collision_preview(world)

    return world


def save_camera_view(world: pygame.Surface, camera: tuple[int, int], filename: str) -> None:
    view = pygame.Surface(SCREEN_SIZE, pygame.SRCALPHA)
    view.blit(world, (0, 0), pygame.Rect(camera, SCREEN_SIZE))
    pygame.image.save(view, OUT_DIR / filename)


def main() -> None:
    for path in (BACKGROUND, PLAYER_ATLAS, WUGANG_ATLAS, YUTU_ATLAS):
        if not path.exists():
            raise FileNotFoundError(path)

    pygame.init()
    pygame.display.set_mode((1, 1))
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    world = compose_world()
    pygame.image.save(world, OUT_DIR / "large_world_overview_clean.png")
    save_camera_view(world, (0, 135), "camera_left_wugang_clean.png")
    save_camera_view(world, (240, 225), "camera_center_player_clean.png")
    save_camera_view(world, (480, 160), "camera_right_yutu_clean.png")

    debug_world = compose_world(show_collision_boxes=True)
    pygame.image.save(debug_world, OUT_DIR / "large_world_overview_debug.png")

    pygame.quit()
    print(f"Rendered large-map character previews into {OUT_DIR}")


if __name__ == "__main__":
    main()
