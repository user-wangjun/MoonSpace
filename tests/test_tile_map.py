"""程序化瓦片地图测试。"""

import config
import pygame
from utils import palette
from world.tile_map import TileMap


def test_tile_map_has_expected_size():
    tile_map = TileMap()

    assert tile_map.width == config.MAP_WIDTH_TILES
    assert tile_map.height == config.MAP_HEIGHT_TILES
    assert len(tile_map.tiles) == config.MAP_HEIGHT_TILES
    assert len(tile_map.tiles[0]) == config.MAP_WIDTH_TILES
    assert config.MAP_WIDTH > config.SCREEN_WIDTH
    assert config.MAP_HEIGHT > config.SCREEN_HEIGHT


def test_tile_generation_is_deterministic():
    first = TileMap()
    second = TileMap()

    assert first.tiles == second.tiles
    assert first.decorations == second.decorations


def test_top_rows_are_walls():
    tile_map = TileMap()

    assert all(tile == TileMap.TILE_WALL for tile in tile_map.tiles[0])
    assert all(tile == TileMap.TILE_WALL for tile in tile_map.tiles[1])


def test_pool_area_uses_pool_tiles():
    tile_map = TileMap()

    for y in range(tile_map.pool_rect.top, tile_map.pool_rect.bottom):
        for x in range(tile_map.pool_rect.left, tile_map.pool_rect.right):
            assert tile_map.get_tile(x, y) == TileMap.TILE_POOL_EDGE


def test_collision_rects_include_wall_and_pool():
    tile_map = TileMap()
    rects = tile_map.get_collision_rects()

    assert rects[0].width == config.MAP_WIDTH
    assert len(rects) == 2


def test_tile_map_draw_fills_right_edge():
    tile_map = TileMap()
    surface = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))

    tile_map.draw(surface)

    assert surface.get_at((config.SCREEN_WIDTH - 1, 40))[:3] != palette.BLACK


def test_tile_map_draw_uses_png_courtyard_background():
    tile_map = TileMap()
    surface = pygame.Surface((config.MAP_WIDTH, config.MAP_HEIGHT), pygame.SRCALPHA)

    tile_map.draw(surface)

    colors = {
        surface.get_at((x, y))[:3]
        for x in range(config.MAP_WIDTH)
        for y in range(config.MAP_HEIGHT)
    }
    assert len(colors) > 300
