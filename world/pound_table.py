"""捣药台场景物体。"""

from __future__ import annotations

import pygame

from utils import palette
from utils.assets import load_image
from utils.pixel_art import draw_filled_rect, draw_rect


class PoundTable:
    """玉兔附近的静态捣药台。"""

    def __init__(self, x: int = 724, y: int = 304) -> None:
        self.position = pygame.Vector2(x, y)
        self.rect = pygame.Rect(x, y, 16, 16)

    def update(self, dt: float) -> None:
        """静态物体保留 update 接口，方便主循环统一调用。"""
        _ = dt

    def draw(self, surface: pygame.Surface, camera_offset: tuple[int, int] = (0, 0)) -> None:
        """绘制木质捣药台。"""
        rect = self.rect.move(camera_offset)
        try:
            sprite = load_image("sprites/moonspace/pound_table.png")
        except (FileNotFoundError, pygame.error):
            sprite = None

        if sprite is not None:
            surface.blit(sprite, (rect.x - 4, rect.y - 6))
            return

        draw_filled_rect(surface, (rect.x + 1, rect.y + 6, 14, 8), palette.WOOD_BROWN)
        draw_rect(surface, rect.x + 1, rect.y + 6, 14, 8, palette.WOOD_DARK)
        draw_filled_rect(surface, (rect.x + 4, rect.y + 2, 8, 6), palette.ASH_GRAY)
        draw_filled_rect(surface, (rect.x + 5, rect.y + 3, 6, 3), palette.BLACK)
        draw_filled_rect(surface, (rect.x + 7, rect.y - 2, 2, 10), palette.MOON_WHITE)
        draw_filled_rect(surface, (rect.x + 3, rect.y + 14, 2, 2), palette.WOOD_DARK)
        draw_filled_rect(surface, (rect.x + 11, rect.y + 14, 2, 2), palette.WOOD_DARK)
        draw_filled_rect(surface, (rect.x + 14, rect.y + 4, 1, 1), palette.PALE_MOON)

    def get_collision_rect(self) -> pygame.Rect:
        """返回捣药台碰撞。"""
        return self.rect.copy()
