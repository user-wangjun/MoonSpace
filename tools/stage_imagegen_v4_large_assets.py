"""Stage confirmed-direction v4 large-map assets without replacing runtime assets."""

from __future__ import annotations

import os
import tempfile
from collections import deque
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_DIR = ROOT / "assets" / "source" / "imagegen" / "candidates"
OUT_DIR = ROOT / "tmp" / "imagegen-v4-large-assets" / "assets" / "sprites" / "moonspace"

SCREEN_SIZE = (480, 270)
WORLD_SIZE = (960, 540)
PLAYER_FRAME_SIZE = (42, 62)
WUGANG_FRAME_SIZE = (76, 92)
YUTU_FRAME_SIZE = (64, 78)

BACKGROUND = CANDIDATE_DIR / "candidate_gameplay_courtyard_clean_bg_horror_v4.png"
CHARACTER_ATLAS = CANDIDATE_DIR / "candidate_characters_npcs_horror_v4.png"
PLAYER_ATLAS = CANDIDATE_DIR / "candidate_player_envoy_16frames_horror_v6.png"
WUGANG_ATLAS = CANDIDATE_DIR / "candidate_wugang_16frames_horror_v7.png"
YUTU_ATLAS = CANDIDATE_DIR / "candidate_yutu_16frames_horror_v7.png"
MAIN_MENU = CANDIDATE_DIR / "candidate_main_menu_scene_horror_v3.png"
OPENING_STORYBOARD = CANDIDATE_DIR / "candidate_opening_cg_storyboard_horror_v3.png"


def ensure_output_directory() -> None:
    """Create the complete temporary asset tree before an image is written."""
    OUT_DIR.mkdir(parents=True, exist_ok=True)


def save_surface(surface: pygame.Surface, destination: Path) -> None:
    """Write an image through a sibling temporary file before replacing it.

    Pygame's Windows PNG writer can fail when asked to overwrite a file after
    the display/mixer has been torn down and initialized again.  Staging is
    deliberately repeatable, so keep the destination out of the writer's
    direct overwrite path and replace it only after the new image is complete.
    """
    ensure_output_directory()
    file_descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{destination.stem}-",
        suffix=destination.suffix,
        dir=OUT_DIR,
    )
    os.close(file_descriptor)
    temporary_path = Path(temporary_name)
    try:
        pygame.image.save(surface, str(temporary_path))
        os.replace(temporary_path, destination)
    finally:
        temporary_path.unlink(missing_ok=True)


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


def transparent_crop(source: pygame.Surface, rect: pygame.Rect) -> pygame.Surface:
    rect = rect.inflate(10, 10).clip(source.get_rect())
    crop = pygame.Surface(rect.size, pygame.SRCALPHA)
    crop.blit(source, (0, 0), rect)
    for y in range(crop.get_height()):
        for x in range(crop.get_width()):
            if is_green_key(crop.get_at((x, y))):
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


def save_sheet(source: pygame.Surface, rects: list[pygame.Rect], frame_size: tuple[int, int], filename: str) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    sheet = pygame.Surface((frame_size[0] * len(rects), frame_size[1]), pygame.SRCALPHA)
    for index, rect in enumerate(rects):
        sheet.blit(fit_sprite(source, rect, frame_size), (index * frame_size[0], 0))
    save_surface(sheet, OUT_DIR / filename)


def save_grid_sheet(
    source: pygame.Surface,
    rows: list[list[pygame.Rect]],
    frame_size: tuple[int, int],
    filename: str,
) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    sheet = pygame.Surface((frame_size[0] * len(rows[0]), frame_size[1] * len(rows)), pygame.SRCALPHA)
    for row_index, row in enumerate(rows):
        for col_index, rect in enumerate(row):
            sheet.blit(fit_sprite(source, rect, frame_size), (col_index * frame_size[0], row_index * frame_size[1]))
    save_surface(sheet, OUT_DIR / filename)


def pad_frames(rects: list[pygame.Rect], expected_count: int) -> list[pygame.Rect]:
    """Pad a generated row that is one frame short by repeating the last frame."""
    if len(rects) == expected_count:
        return rects
    if len(rects) == expected_count - 1:
        return [*rects, rects[-1]]
    return rects


def main_row_frames(path: Path, expected_count: int) -> list[pygame.Rect]:
    atlas = pygame.image.load(str(path)).convert_alpha()
    rects = sorted(component_rects(atlas), key=lambda rect: rect.centerx)
    if len(rects) != expected_count:
        raise RuntimeError(f"{path.name} has {len(rects)} frames, expected {expected_count}")
    return rects


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


def save_scaled(path: Path, size: tuple[int, int], filename: str) -> None:
    ensure_output_directory()
    source = pygame.image.load(str(path)).convert_alpha()
    save_surface(pygame.transform.scale(source, size), OUT_DIR / filename)


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


def stage_backgrounds() -> None:
    ensure_output_directory()
    save_scaled(BACKGROUND, WORLD_SIZE, "courtyard_bg_large.png")
    save_scaled(MAIN_MENU, SCREEN_SIZE, "main_menu_bg.png")

    storyboard = pygame.image.load(str(OPENING_STORYBOARD)).convert_alpha()
    panels = panel_rects(storyboard)
    for key, filename in (
        ("top_left", "opening_cg_room.png"),
        ("top_right", "opening_cg_moonlight.png"),
        ("bottom_left", "opening_cg_blood_moon.png"),
        ("bottom_right", "opening_cg_blackout.png"),
    ):
        crop = pygame.Surface(panels[key].size, pygame.SRCALPHA)
        crop.blit(storyboard, (0, 0), panels[key])
        save_surface(pygame.transform.scale(crop, SCREEN_SIZE), OUT_DIR / filename)


def stage_character_sheets() -> None:
    ensure_output_directory()
    player_atlas = pygame.image.load(str(PLAYER_ATLAS)).convert_alpha()
    player_rows = grid_frames(PLAYER_ATLAS, 4, 4)

    wugang_atlas = pygame.image.load(str(WUGANG_ATLAS)).convert_alpha()
    wugang_rows = grid_frames(WUGANG_ATLAS, 4, 4)

    yutu_atlas = pygame.image.load(str(YUTU_ATLAS)).convert_alpha()
    yutu_rows = grid_frames(YUTU_ATLAS, 4, 4)

    save_grid_sheet(player_atlas, player_rows, PLAYER_FRAME_SIZE, "player_envoy_large.png")
    save_grid_sheet(wugang_atlas, wugang_rows, WUGANG_FRAME_SIZE, "wugang_chop_large.png")
    save_grid_sheet(yutu_atlas, yutu_rows, YUTU_FRAME_SIZE, "yutu_pounding_large.png")


def validate_outputs() -> None:
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
        image = pygame.image.load(str(OUT_DIR / filename)).convert_alpha()
        if image.get_size() != size:
            raise RuntimeError(f"{filename} has size {image.get_size()}, expected {size}")


def main() -> None:
    for path in (BACKGROUND, PLAYER_ATLAS, WUGANG_ATLAS, YUTU_ATLAS, MAIN_MENU, OPENING_STORYBOARD):
        if not path.exists():
            raise FileNotFoundError(path)

    pygame.init()
    pygame.display.set_mode((1, 1))
    ensure_output_directory()
    stage_backgrounds()
    stage_character_sheets()
    validate_outputs()
    pygame.quit()
    print(f"Staged v4 large-map assets into {OUT_DIR}")


if __name__ == "__main__":
    main()
