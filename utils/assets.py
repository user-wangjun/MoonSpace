"""Pygame image asset loading helpers."""

from __future__ import annotations

import sys
from pathlib import Path

import pygame


_IMAGE_CACHE: dict[tuple[str, bool], pygame.Surface] = {}
_SHEET_CACHE: dict[tuple[str, int, int], list[pygame.Surface]] = {}
_GRID_CACHE: dict[tuple[str, int, int, int, int], list[list[pygame.Surface]]] = {}


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
