"""捣药台场景物体。"""

from __future__ import annotations

import pygame

from utils import palette
from utils.assets import load_image
from utils.pixel_art import draw_filled_rect, draw_rect


class PoundTable:
    """玉兔附近的静态药臼；碰撞锚点保持原 16×16 世界位置。"""

    MORTAR_SPRITE_PATH = "sprites/moonspace/props/yutu_mortar.png"
    MORTAR_SIZE = (48, 32)
    FRONT_START = 18

    def __init__(self, x: int = 724, y: int = 304) -> None:
        self.position = pygame.Vector2(x, y)
        self.rect = pygame.Rect(x, y, 16, 16)

    def update(self, dt: float) -> None:
        """静态物体保留 update 接口，方便主循环统一调用。"""
        _ = dt

    def draw(self, surface: pygame.Surface, camera_offset: tuple[int, int] = (0, 0)) -> None:
        """兼容旧调用：按正确顺序绘制药臼后沿和前沿。"""
        self.draw_back(surface, camera_offset)
        self.draw_front(surface, camera_offset)

    def draw_back(self, surface: pygame.Surface, camera_offset: tuple[int, int] = (0, 0)) -> None:
        """绘制药臼后沿，必须位于玉兔本体之前。"""
        sprite = self._load_sprite()
        destination = self._destination(camera_offset, sprite)
        if sprite is not None:
            surface.blit(sprite, destination)
            return
        self._draw_fallback(surface, destination)

    def draw_front(self, surface: pygame.Surface, camera_offset: tuple[int, int] = (0, 0)) -> None:
        """绘制药臼前沿，压住手部/杵的必要遮挡区域。"""
        sprite = self._load_sprite()
        destination = self._destination(camera_offset, sprite)
        if sprite is not None:
            source = pygame.Rect(0, self.FRONT_START, sprite.get_width(), sprite.get_height() - self.FRONT_START)
            surface.blit(sprite, (destination[0], destination[1] + self.FRONT_START), source)
            return
        front = pygame.Rect(destination.x + 5, destination.y + self.FRONT_START, 38, 8)
        pygame.draw.ellipse(surface, palette.WOOD_DARK, front)
        draw_rect(surface, front.x, front.y, front.width, front.height, palette.PALE_MOON)

    def _load_sprite(self) -> pygame.Surface | None:
        try:
            sprite = load_image(self.MORTAR_SPRITE_PATH)
        except (FileNotFoundError, pygame.error):
            return None
        if sprite.get_size() != self.MORTAR_SIZE:
            sprite = pygame.transform.smoothscale(sprite, self.MORTAR_SIZE)
        return sprite

    def _destination(self, camera_offset: tuple[int, int], sprite: pygame.Surface | None) -> tuple[int, int]:
        size = sprite.get_size() if sprite is not None else self.MORTAR_SIZE
        return (
            self.rect.centerx + camera_offset[0] - size[0] // 2,
            self.rect.centery + camera_offset[1] - size[1] // 2,
        )

    @staticmethod
    def _draw_fallback(surface: pygame.Surface, destination: tuple[int, int]) -> None:
        """Clean, non-green emergency prop when the formal PNG is unavailable."""
        x, y = destination
        body = pygame.Rect(x + 4, y + 8, 40, 20)
        pygame.draw.ellipse(surface, palette.WOOD_BROWN, body)
        draw_rect(surface, body.x, body.y, body.width, body.height, palette.WOOD_DARK)
        inner = body.inflate(-7, -7)
        pygame.draw.ellipse(surface, palette.BLACK, inner)
        draw_rect(surface, inner.x, inner.y, inner.width, inner.height, palette.PALE_MOON)
        draw_filled_rect(surface, (x + 8, y + 25, 5, 7), palette.WOOD_DARK)
        draw_filled_rect(surface, (x + 35, y + 25, 5, 7), palette.WOOD_DARK)

    def get_collision_rect(self) -> pygame.Rect:
        """返回捣药台碰撞。"""
        return self.rect.copy()
