"""像素绘制工具。"""

from __future__ import annotations

import pygame


Color = tuple[int, int, int] | tuple[int, int, int, int]


def draw_pixel(surface: pygame.Surface, x: int, y: int, color: Color) -> None:
    """安全绘制单个像素；越界时忽略，便于像素数据复用。"""
    if 0 <= x < surface.get_width() and 0 <= y < surface.get_height():
        surface.set_at((int(x), int(y)), color)


def draw_rect(surface: pygame.Surface, x: int, y: int, width: int, height: int, color: Color) -> None:
    """绘制 1 像素边框矩形。"""
    pygame.draw.rect(surface, color, pygame.Rect(x, y, width, height), 1)


def draw_double_rect(
    surface: pygame.Surface,
    rect: pygame.Rect | tuple[int, int, int, int],
    outer_color: Color,
    inner_color: Color,
) -> None:
    """绘制双层边框，用于月宫 UI 面板和重点物体轮廓。"""
    box = pygame.Rect(rect)
    draw_rect(surface, box.x, box.y, box.width, box.height, outer_color)
    if box.width > 4 and box.height > 4:
        draw_rect(surface, box.x + 2, box.y + 2, box.width - 4, box.height - 4, inner_color)


def draw_filled_rect(surface: pygame.Surface, rect: pygame.Rect | tuple[int, int, int, int], color: Color) -> None:
    """绘制填充矩形，是当前代码像素风的主要构图方法。"""
    pygame.draw.rect(surface, color, rect)


def draw_line(surface: pygame.Surface, start: tuple[int, int], end: tuple[int, int], color: Color) -> None:
    """绘制硬边像素线。"""
    pygame.draw.line(surface, color, start, end, 1)


def draw_marker_pixels(
    surface: pygame.Surface,
    x: int,
    y: int,
    points: list[tuple[int, int]] | tuple[tuple[int, int], ...],
    color: Color,
) -> None:
    """按相对坐标绘制少量标记像素，适合眼点、刻痕和装饰点。"""
    for point_x, point_y in points:
        draw_pixel(surface, x + point_x, y + point_y, color)


def draw_pixel_data(
    surface: pygame.Surface,
    pixel_data: list[str],
    color_map: dict[str, Color],
    x: int,
    y: int,
    scale: int = 1,
) -> None:
    """按字符矩阵绘制像素图，空格和未映射字符会被跳过。"""
    for row_index, row in enumerate(pixel_data):
        for col_index, key in enumerate(row):
            if key == " " or key not in color_map:
                continue
            rect = pygame.Rect(
                x + col_index * scale,
                y + row_index * scale,
                scale,
                scale,
            )
            draw_filled_rect(surface, rect, color_map[key])
