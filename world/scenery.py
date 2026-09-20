"""Ground footprints and foreground silhouettes for the painted scene props."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

import pygame


@dataclass(frozen=True)
class SceneryProp:
    footprint: tuple[int, int, int, int]
    polygons: tuple[tuple[tuple[int, int], ...], ...]


def _lantern(cx: int, top: int, width: int, height: int, footprint: tuple[int, int, int, int]) -> SceneryProp:
    outline = (
        (0, 0), (.12, .12), (.5, .23), (.32, .3), (.28, .67),
        (.16, .76), (.2, .86), (.4, .9), (.4, 1), (-.4, 1),
        (-.4, .9), (-.2, .86), (-.16, .76), (-.28, .67),
        (-.32, .3), (-.5, .23), (-.12, .12),
    )
    return SceneryProp(footprint, (tuple((round(cx + x * width), round(top + y * height)) for x, y in outline),))


HOME_SIGN = SceneryProp((444, 286, 76, 13), (
    ((435, 213), (448, 216), (451, 211), (506, 211), (510, 216), (523, 213), (523, 226), (517, 239), (442, 239)),
    ((447, 238), (513, 238), (513, 272), (447, 272)),
    ((446, 267), (453, 267), (453, 298), (446, 298)),
    ((508, 267), (516, 267), (516, 298), (508, 298)),
))
HOME_LANTERNS = (
    _lantern(116, 179, 49, 88, (101, 250, 34, 18)),
    _lantern(844, 179, 49, 88, (825, 250, 34, 18)),
)
HOME_PROPS = (HOME_SIGN, *HOME_LANTERNS)
HALL_LANTERNS = (
    _lantern(307, 66, 38, 69, (294, 123, 28, 12)),
    _lantern(633, 66, 38, 69, (620, 123, 28, 12)),
    _lantern(210, 190, 59, 88, (195, 265, 32, 14)),
    _lantern(738, 190, 59, 88, (723, 265, 32, 14)),
    _lantern(82, 358, 70, 135, (57, 471, 52, 22)),
    _lantern(864, 358, 70, 135, (839, 471, 52, 22)),
)


@lru_cache(maxsize=48)
def _foreground_layer(background: pygame.Surface, prop: SceneryProp) -> tuple[pygame.Surface, pygame.Rect]:
    points = [point for polygon in prop.polygons for point in polygon]
    bounds = pygame.Rect(min(x for x, _ in points), min(y for _, y in points), 1, 1)
    bounds.width = max(x for x, _ in points) - bounds.x + 1
    bounds.height = max(y for _, y in points) - bounds.y + 1
    layer = pygame.Surface(bounds.size, pygame.SRCALPHA)
    layer.blit(background, (0, 0), bounds)
    mask = pygame.Surface(bounds.size, pygame.SRCALPHA)
    for polygon in prop.polygons:
        pygame.draw.polygon(mask, (255, 255, 255, 255), [(x - bounds.x, y - bounds.y) for x, y in polygon])
    layer.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    return layer, bounds


def draw_scenery_foreground(surface: pygame.Surface, background: pygame.Surface, props: tuple[SceneryProp, ...], camera_offset: tuple[int, int], feet_y: int) -> None:
    """Paint only the solid prop silhouette over an actor standing behind it."""
    for prop in props:
        if feet_y > prop.footprint[1] + prop.footprint[3]:
            continue
        layer, bounds = _foreground_layer(background, prop)
        destination = bounds.move(camera_offset)
        if destination.colliderect(surface.get_rect()):
            surface.blit(layer, destination)
