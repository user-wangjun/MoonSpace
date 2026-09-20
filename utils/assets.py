"""Pygame image asset loading helpers."""

from __future__ import annotations

import sys
from pathlib import Path

import pygame


_IMAGE_CACHE: dict[tuple[str, bool], pygame.Surface] = {}
_SHEET_CACHE: dict[tuple[str, int, int], list[pygame.Surface]] = {}
_GRID_CACHE: dict[tuple[str, int, int, int, int], list[list[pygame.Surface]]] = {}

# Artwork can be authored at higher resolution; world units and animation cells
# remain fixed. These are presentation sizes, never collision dimensions.
RUNTIME_IMAGE_SIZES = {
    "sprites/moonspace/player_envoy_large.png": (168, 248),
    "sprites/moonspace/wugang_chop_large.png": (304, 368),
    "sprites/moonspace/yutu_body_4x4.png": (256, 312),
    "sprites/moonspace/props/yutu_mortar.png": (48, 32),
    "sprites/moonspace/props/registration_desk.png": (180, 96),
    "sprites/moonspace/home_tutorial_bg.png": (960, 540),
    "sprites/moonspace/home_tutorial_bg_open.png": (960, 540),
    "sprites/moonspace/backgrounds/courtyard_expanded_closed.png": (960, 640),
    "sprites/moonspace/backgrounds/courtyard_expanded_open.png": (960, 640),
    "sprites/moonspace/backgrounds/guanghan_hall_curtain.png": (960, 720),
}
CHROMA_KEY_ASSETS = {
    "sprites/moonspace/player_envoy_large.png",
    "sprites/moonspace/wugang_chop_large.png",
    "sprites/moonspace/yutu_body_4x4.png",
    "sprites/moonspace/props/yutu_mortar.png",
    "sprites/moonspace/props/registration_desk.png",
}
CHARACTER_GRID_ASSETS = {
    "sprites/moonspace/player_envoy_large.png",
    "sprites/moonspace/wugang_chop_large.png",
    "sprites/moonspace/yutu_body_4x4.png",
}


def _fit_character_grid(image: pygame.Surface, target_size: tuple[int, int]) -> pygame.Surface:
    """Respect empty authored gutters before reducing the four animation rows."""
    width, height = image.get_size()
    mask = pygame.mask.from_surface(image, 8)
    edges = [0]
    for row in range(1, 4):
        expected = round(height * row / 4)
        radius = max(1, height // 24)
        empty = [
            y for y in range(expected - radius, expected + radius + 1)
            if not any(mask.get_at((x, y)) for x in range(width))
        ]
        edges.append(min(empty, key=lambda y: abs(y - expected)) if empty else expected)
    edges.append(height)
    frame_width, frame_height = target_size[0] // 4, target_size[1] // 4
    fitted = pygame.Surface(target_size, pygame.SRCALPHA)
    for row in range(4):
        for col in range(4):
            left, right = round(width * col / 4), round(width * (col + 1) / 4)
            source = image.subsurface((left, edges[row], right - left, edges[row + 1] - edges[row]))
            frame = pygame.transform.smoothscale(source, (frame_width, frame_height))
            fitted.blit(frame, (col * frame_width, row * frame_height))
    return fitted


def _remove_green_key(image: pygame.Surface) -> pygame.Surface:
    """Decode the authored green-screen sprites without discarding dark shading."""
    pixels = bytearray(pygame.image.tobytes(image, "RGBA"))
    for offset in range(0, len(pixels), 4):
        red, green, blue = pixels[offset:offset + 3]
        if green > 110 and green > max(red, blue) + 55:
            pixels[offset:offset + 4] = b"\x00\x00\x00\x00"
        elif green > max(red, blue) + 20:
            # De-spill the antialiased silhouette edge before it is downsampled.
            pixels[offset + 1] = max(red, blue)
    return pygame.image.frombytes(bytes(pixels), image.get_size(), "RGBA")


def asset_path(relative_path: str) -> Path:
    """Return an absolute path for a project asset."""
    base_dir = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[1]))
    return base_dir / "assets" / relative_path


def load_image(relative_path: str, *, convert_alpha: bool = True) -> pygame.Surface:
    """Load a single image asset."""
    key = (relative_path, convert_alpha)
    if key in _IMAGE_CACHE:
        return _IMAGE_CACHE[key]

    path = asset_path(relative_path)
    if not path.exists():
        raise FileNotFoundError(path)

    image = pygame.image.load(str(path))
    if relative_path in CHROMA_KEY_ASSETS:
        corner = image.get_at((0, 0))
        if corner.g > 180 and corner.g > max(corner.r, corner.b) + 80:
            image = _remove_green_key(image)
    target_size = RUNTIME_IMAGE_SIZES.get(relative_path)
    if target_size is not None and image.get_size() != target_size:
        if relative_path in CHARACTER_GRID_ASSETS:
            image = _fit_character_grid(image, target_size)
        else:
            image = pygame.transform.smoothscale(image, target_size)
    if convert_alpha and pygame.display.get_surface() is not None:
        image = image.convert_alpha()
    elif convert_alpha:
        image = image.copy()
        image.set_colorkey(None)
    else:
        image = image.convert()

    _IMAGE_CACHE[key] = image
    return image


def load_sprite_sheet(relative_path: str, frame_width: int, frame_height: int) -> list[pygame.Surface]:
    """Load a horizontal sprite sheet into equally sized frames."""
    key = (relative_path, frame_width, frame_height)
    if key in _SHEET_CACHE:
        return _SHEET_CACHE[key]

    sheet = load_image(relative_path)
    if sheet.get_width() % frame_width != 0 or sheet.get_height() != frame_height:
        raise ValueError(
            f"{relative_path} has size {sheet.get_size()}, expected a horizontal sheet "
            f"with frame size {(frame_width, frame_height)}"
        )

    frames = []
    for x in range(0, sheet.get_width(), frame_width):
        frame = pygame.Surface((frame_width, frame_height), pygame.SRCALPHA)
        frame.blit(sheet, (0, 0), pygame.Rect(x, 0, frame_width, frame_height))
        frames.append(frame)

    _SHEET_CACHE[key] = frames
    return frames


def load_sprite_grid(
    relative_path: str,
    frame_width: int,
    frame_height: int,
    rows: int,
    cols: int,
) -> list[list[pygame.Surface]]:
    """Load a fixed-size sprite grid into rows of frames."""
    key = (relative_path, frame_width, frame_height, rows, cols)
    if key in _GRID_CACHE:
        return _GRID_CACHE[key]

    sheet = load_image(relative_path)
    expected_size = (frame_width * cols, frame_height * rows)
    if sheet.get_size() != expected_size:
        raise ValueError(f"{relative_path} has size {sheet.get_size()}, expected {expected_size}")

    grid = []
    for row in range(rows):
        grid_row = []
        for col in range(cols):
            frame = pygame.Surface((frame_width, frame_height), pygame.SRCALPHA)
            frame.blit(sheet, (0, 0), pygame.Rect(col * frame_width, row * frame_height, frame_width, frame_height))
            grid_row.append(frame)
        grid.append(grid_row)

    _GRID_CACHE[key] = grid
    return grid


def clear_asset_cache() -> None:
    """Clear cached Pygame image assets."""
    _IMAGE_CACHE.clear()
    _SHEET_CACHE.clear()
    _GRID_CACHE.clear()
