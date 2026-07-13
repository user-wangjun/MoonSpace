"""程序化瓦片地图。"""

from __future__ import annotations

import pygame

import config
from utils import palette
from utils.assets import load_image
from utils.pixel_art import draw_filled_rect, draw_pixel


class TileMap:
    """大地图瓦片层，优先使用 imagegen 大地图背景。"""

    TILE_FLOOR_0 = 0
    TILE_FLOOR_1 = 1
    TILE_FLOOR_2 = 2
    TILE_POOL_EDGE = 3
    TILE_WALL = 4

    def __init__(self) -> None:
        self.width = config.MAP_WIDTH_TILES
        self.height = config.MAP_HEIGHT_TILES
        self.tile_size = config.TILE_SIZE
        self.pool_rect = pygame.Rect(38, 23, 4, 3)
        self.tiles = self._generate_tiles()
        self.decorations = self._generate_decorations()
        self._surface_cache = pygame.Surface((config.MAP_WIDTH, config.MAP_HEIGHT))
        self._cache_dirty = True

    def draw(self, surface: pygame.Surface, camera_offset: tuple[int, int] = (0, 0)) -> None:
        """绘制缓存后的瓦片层，避免每帧重复生成地图。"""
        try:
            background = load_image("sprites/moonspace/courtyard_bg_large.png")
        except (FileNotFoundError, pygame.error):
            background = None

        if background is not None:
            surface.blit(background, camera_offset)
            return

        if self._cache_dirty:
            self._redraw_cache()
        surface.blit(self._surface_cache, camera_offset)

    def get_collision_rects(self) -> list[pygame.Rect]:
        """返回地图硬碰撞，当前包含顶部宫墙和月池水面。"""
        return [
            pygame.Rect(0, 0, config.MAP_WIDTH, 24),
            pygame.Rect(
                self.pool_rect.x * self.tile_size,
                self.pool_rect.y * self.tile_size,
                self.pool_rect.width * self.tile_size,
                self.pool_rect.height * self.tile_size,
            ),
        ]

    def get_tile(self, tile_x: int, tile_y: int) -> int:
        """读取瓦片编号，越界视为墙体。"""
        if not (0 <= tile_x < self.width and 0 <= tile_y < self.height):
            return self.TILE_WALL
        return self.tiles[tile_y][tile_x]

    def _generate_tiles(self) -> list[list[int]]:
        """生成地面、宫墙和月池边缘瓦片。"""
        rows: list[list[int]] = []
        for y in range(self.height):
            row: list[int] = []
            for x in range(self.width):
                if y <= 1:
                    tile = self.TILE_WALL
                elif self.pool_rect.collidepoint(x, y):
                    tile = self.TILE_POOL_EDGE
                else:
                    value = self._hash(x, y) % 10
                    if value < 6:
                        tile = self.TILE_FLOOR_0
                    elif value < 9:
                        tile = self.TILE_FLOOR_1
                    else:
                        tile = self.TILE_FLOOR_2
                row.append(tile)
            rows.append(row)
        return rows

    def _generate_decorations(self) -> list[tuple[int, int, tuple[int, int, int]]]:
        """生成石子、草叶、月尘等小装饰点。"""
        decorations = []
        colors = [palette.GROUND_LIGHT, palette.ASH_GRAY, palette.LAUREL_DARK]
        for y in range(2, self.height):
            for x in range(self.width):
                if self.pool_rect.collidepoint(x, y):
                    continue
                value = self._hash(x + 17, y + 31)
                if value % 4 == 0:
                    px = x * self.tile_size + 2 + value % 11
                    py = y * self.tile_size + 2 + (value // 7) % 11
                    decorations.append((px, py, colors[value % len(colors)]))
        return decorations

    def _redraw_cache(self) -> None:
        """把瓦片和装饰绘制到缓存 Surface。"""
        for y, row in enumerate(self.tiles):
            for x, tile in enumerate(row):
                self._draw_tile(self._surface_cache, x, y, tile)

        for x, y, color in self.decorations:
            draw_pixel(self._surface_cache, x, y, color)
            if (x + y) % 3 == 0:
                draw_pixel(self._surface_cache, x + 1, y, color)

        self._cache_dirty = False

    def _draw_tile(self, surface: pygame.Surface, tile_x: int, tile_y: int, tile: int) -> None:
        """绘制单个 16×16 瓦片。"""
        x = tile_x * self.tile_size
        y = tile_y * self.tile_size
        rect = pygame.Rect(x, y, self.tile_size, self.tile_size)
        if tile == self.TILE_WALL:
            draw_filled_rect(surface, rect, palette.PALACE_STONE)
            draw_filled_rect(surface, (x, y + 14, self.tile_size, 2), palette.DEEP_BLUE)
        elif tile == self.TILE_POOL_EDGE:
            draw_filled_rect(surface, rect, palette.POOL_BLUE)
            draw_filled_rect(surface, (x + 2, y + 7, 12, 1), palette.POOL_HIGHLIGHT)
        elif tile == self.TILE_FLOOR_1:
            draw_filled_rect(surface, rect, palette.GROUND_MID)
        elif tile == self.TILE_FLOOR_2:
            draw_filled_rect(surface, rect, palette.GROUND_LIGHT)
        else:
            draw_filled_rect(surface, rect, palette.GROUND_DARK)

    @staticmethod
    def _hash(x: int, y: int) -> int:
        """稳定整数哈希，避免使用随机种子导致地图变化。"""
        return (x * 73856093 ^ y * 19349663 ^ 0x9E3779B9) & 0xFFFFFFFF
