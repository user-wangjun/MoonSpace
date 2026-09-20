"""广寒宫墙背景。"""

from __future__ import annotations

import pygame

import config
from utils import palette
from utils.assets import load_image
from utils.pixel_art import draw_filled_rect, draw_marker_pixels


class PalaceWall:
    """顶部背景墙，作为 Demo 结束方向的视觉提示。"""

    GATE_BACKGROUND_BY_STATE = {
        False: "sprites/moonspace/backgrounds/courtyard_expanded_closed.png",
        True: "sprites/moonspace/backgrounds/courtyard_expanded_open.png",
    }
    ENTRY_RECT = pygame.Rect(config.COURTYARD_WIDTH // 2 - 38, 158, 76, 34)

    def __init__(self) -> None:
        self.rect = pygame.Rect(0, 0, config.COURTYARD_WIDTH, 150)
        self.horror_level = 0
        self.gate_open = False
        self._time = 0.0
        self._gate_background_cache: dict[bool, pygame.Surface] = {}

    def update(self, dt: float) -> None:
        """推进远景宫墙的轻微闪烁。"""
        self._time += dt

    def draw(self, surface: pygame.Surface, camera_offset: tuple[int, int] = (0, 0)) -> None:
        """绘制由 16×16 瓦片感组成的宫墙。"""
        rect = self.rect.move(camera_offset)
        gate_background = self._get_gate_background()
        if gate_background is not None:
            surface.blit(gate_background, camera_offset)
            self._draw_horror_overlay(surface, rect)
            return

        try:
            load_image("sprites/moonspace/courtyard_bg_large.png")
            large_background_available = True
        except (FileNotFoundError, pygame.error):
            large_background_available = False

        if large_background_available:
            self._draw_horror_overlay(surface, rect)
            return

        try:
            sprite = load_image("sprites/moonspace/palace_wall_bg.png")
        except (FileNotFoundError, pygame.error):
            sprite = None

        if sprite is not None:
            surface.blit(sprite, camera_offset)
            self._draw_horror_overlay(surface, rect)
            return

        draw_filled_rect(surface, rect, palette.PALACE_STONE)
        draw_filled_rect(surface, (rect.x, rect.y, rect.width, 4), palette.DEEP_BLUE)
        for x in range(rect.x, rect.right, config.TILE_SIZE):
            if (x // config.TILE_SIZE) % 2 == 0:
                draw_filled_rect(surface, (x + 1, rect.y + 1, 14, 3), palette.PALACE_STONE)
                draw_filled_rect(surface, (x + 4, rect.y - 1, 8, 2), palette.DARK_BLOOD)
            draw_filled_rect(surface, (x, rect.y + 14, config.TILE_SIZE - 1, 2), palette.DEEP_BLUE)
            if (x // config.TILE_SIZE) % 2 == 0:
                draw_filled_rect(surface, (x + 5, rect.y + 4, 6, 5), palette.ASH_GRAY)

        gate_x = rect.centerx - 18
        draw_filled_rect(surface, (gate_x, rect.y + 5, 36, 18), palette.DEEP_BLUE)
        draw_filled_rect(surface, (gate_x + 4, rect.y + 8, 28, 14), palette.BLACK)
        draw_filled_rect(surface, (gate_x + 15, rect.y + 4, 6, 18), palette.PALE_MOON)
        draw_marker_pixels(
            surface,
            gate_x + 11,
            rect.y + 8,
            [(2, 2), (11, 2), (5, 6), (8, 6), (6, 10), (7, 10)],
            palette.MOON_WHITE,
        )
        draw_filled_rect(surface, (rect.centerx - 3, rect.y + 12, 6, 9), palette.PALE_MOON)
        self._draw_horror_overlay(surface, rect)

    def _get_gate_background(self) -> pygame.Surface | None:
        """加载并缓存与地图尺寸一致的宫门状态背景。"""
        if self.gate_open in self._gate_background_cache:
            return self._gate_background_cache[self.gate_open]

        try:
            background = load_image(self.GATE_BACKGROUND_BY_STATE[self.gate_open])
        except (FileNotFoundError, pygame.error):
            return None

        courtyard_size = (config.COURTYARD_WIDTH, config.COURTYARD_HEIGHT)
        if background.get_size() != courtyard_size:
            background = pygame.transform.smoothscale(background, courtyard_size)
        self._gate_background_cache[self.gate_open] = background
        return background

    def _draw_horror_overlay(self, surface: pygame.Surface, rect: pygame.Rect) -> None:
        """绘制违规导致的宫墙异化叠加。"""
        if self.horror_level > 0:
            gate_x = rect.centerx - 18
            flicker = int(self._time * 6) % 2
            draw_filled_rect(surface, (gate_x + 7, rect.y + 11, 22, 1 + flicker), palette.DARK_BLOOD)
            if self.horror_level >= 2:
                # 不再横跨整座广场绘制红色调试感直线，只保留门缝局部异化。
                draw_filled_rect(surface, (gate_x + 2, rect.y + 24, 32, 2), palette.DARK_BLOOD)
            if self.horror_level >= 3:
                draw_filled_rect(surface, (rect.centerx - 14, rect.y + 5, 28, 3), palette.BLOOD_RED)

    def set_horror_level(self, level: int) -> None:
        """设置违规导致的远景异化等级。"""
        self.horror_level = max(0, min(3, level))

    def set_gate_open(self, is_open: bool) -> None:
        """根据伐桂、捣药、修月三项检查进度切换宫门状态。"""
        self.gate_open = bool(is_open)

    def get_collision_rect(self) -> pygame.Rect:
        """返回宫墙碰撞。"""
        return self.rect.copy()

    def get_entry_rect(self) -> pygame.Rect:
        """返回与新宫门台阶对齐的复命交互区域。"""
        return self.ENTRY_RECT.copy()
