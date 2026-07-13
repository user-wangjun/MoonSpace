"""像素绘制工具测试。"""

import pygame

from utils.pixel_art import (
    draw_double_rect,
    draw_filled_rect,
    draw_line,
    draw_marker_pixels,
    draw_pixel,
    draw_pixel_data,
    draw_rect,
)


def test_draw_pixel_sets_color():
    surface = pygame.Surface((4, 4))
    draw_pixel(surface, 1, 1, (255, 0, 0))

    assert surface.get_at((1, 1))[:3] == (255, 0, 0)


def test_draw_pixel_ignores_out_of_bounds():
    surface = pygame.Surface((4, 4))
    draw_pixel(surface, -1, -1, (255, 0, 0))
    draw_pixel(surface, 99, 99, (255, 0, 0))


def test_draw_shapes_do_not_crash():
    surface = pygame.Surface((10, 10))
    draw_rect(surface, 1, 1, 4, 4, (255, 255, 255))
    draw_line(surface, (0, 0), (9, 9), (0, 255, 0))
    draw_filled_rect(surface, (2, 2, 3, 3), (255, 0, 0))

    assert surface.get_at((2, 2))[:3] == (255, 0, 0)


def test_draw_pixel_data_uses_color_map():
    surface = pygame.Surface((4, 4))
    draw_pixel_data(surface, [" A", "A "], {"A": (0, 0, 255)}, 0, 0)

    assert surface.get_at((1, 0))[:3] == (0, 0, 255)
    assert surface.get_at((0, 1))[:3] == (0, 0, 255)


def test_draw_double_rect_draws_outer_and_inner_borders():
    surface = pygame.Surface((12, 12))

    draw_double_rect(surface, pygame.Rect(1, 1, 10, 10), (255, 255, 255), (0, 255, 0))

    assert surface.get_at((1, 1))[:3] == (255, 255, 255)
    assert surface.get_at((3, 3))[:3] == (0, 255, 0)


def test_draw_marker_pixels_draws_relative_points():
    surface = pygame.Surface((8, 8))

    draw_marker_pixels(surface, 2, 2, [(0, 0), (2, 1)], (255, 0, 0))

    assert surface.get_at((2, 2))[:3] == (255, 0, 0)
    assert surface.get_at((4, 3))[:3] == (255, 0, 0)
