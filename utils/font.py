"""字体加载与文本绘制工具。"""

from __future__ import annotations

from pathlib import Path

import pygame

from utils import palette
from utils.assets import asset_path
from utils.pixel_art import draw_filled_rect


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FONT_CANDIDATES = [
    PROJECT_ROOT / "assets" / "fonts" / "pixel.ttf",
    PROJECT_ROOT / "assets" / "fonts" / "NotoSansCJK-Regular.ttc",
    PROJECT_ROOT / "assets" / "fonts" / "NotoSansCJK-Regular.otf",
    PROJECT_ROOT / "assets" / "fonts" / "SimHei.ttf",
    Path("C:/Windows/Fonts/msyh.ttc"),
    Path("C:/Windows/Fonts/msyh.ttf"),
    Path("C:/Windows/Fonts/simhei.ttf"),
    Path("C:/Windows/Fonts/simsun.ttc"),
    Path("C:/Windows/Fonts/Deng.ttf"),
]
FONT_MATCH_NAMES = [
    "microsoftyahei",
    "microsoft yahei",
    "simhei",
    "simsun",
    "dengxian",
    "noto sans cjk sc",
]


def load_font(size: int) -> pygame.font.Font:
    """优先加载中文字体；缺失时使用 Pygame 默认字体降级。

    Pygame Font 对象不能安全跨 pygame.quit() 复用，因此这里不缓存对象。
    """
    if not pygame.font.get_init():
        pygame.font.init()

    # Native 10/12 pixel glyph grids stay legible at the game's 480x270 scale.
    # Use integral enlargement for titles; fractional pixel scaling breaks strokes.
    if size <= 11:
        grid, rendered_size = 10, 10
    elif size < 18:
        grid, rendered_size = 12, 12
    elif size < 22:
        grid, rendered_size = 10, 20
    else:
        grid, rendered_size = 12, max(24, round(size / 12) * 12)
    bundled = asset_path(f"fonts/fusion-pixel-{grid}px-monospaced-zh_hans.otf")
    if bundled.exists():
        return pygame.font.Font(str(bundled), rendered_size)

    for font_path in FONT_CANDIDATES:
        if font_path.exists():
            return pygame.font.Font(str(font_path), size)

    for font_name in FONT_MATCH_NAMES:
        try:
            matched = pygame.font.match_font(font_name)
        except (TypeError, pygame.error):
            matched = None
        if matched:
            return pygame.font.Font(matched, size)

    return pygame.font.Font(None, size)


def render_text(
    surface: pygame.Surface,
    text: str,
    x: int,
    y: int,
    size: int = 14,
    color: tuple[int, int, int] = palette.MOON_WHITE,
) -> bool:
    """渲染单行文本；成功返回 True，失败由调用方决定是否降级。"""
    try:
        font = load_font(size)
        rendered = font.render(text, False, color)
        surface.blit(rendered, (x, y))
        return True
    except Exception:
        return False


def wrap_text(text: str, max_chars: int) -> list[str]:
    """按字符数做轻量换行，适合当前像素风中文 UI。"""
    if max_chars <= 0:
        return [text]

    lines: list[str] = []
    current = ""
    for char in text:
        current += char
        if len(current) >= max_chars or char in "。！？；":
            lines.append(current)
            current = ""
    if current:
        lines.append(current)
    return lines or [""]


def render_wrapped_text(
    surface: pygame.Surface,
    lines: list[str],
    x: int,
    y: int,
    size: int = 14,
    color: tuple[int, int, int] = palette.MOON_WHITE,
    line_height: int = 16,
    max_chars: int | None = None,
) -> bool:
    """逐行渲染文本，可选按字符数自动折行。"""
    success = True
    expanded_lines: list[str] = []
    for line in lines:
        if max_chars is None:
            expanded_lines.append(line)
        else:
            expanded_lines.extend(wrap_text(line, max_chars))

    for index, line in enumerate(expanded_lines):
        success = render_text(surface, line, x, y + index * line_height, size, color) and success
    return success


def render_block_text(surface: pygame.Surface, text: str, x: int, y: int) -> None:
    """无字体可用时的像素块降级，占位表达文本长度。"""
    max_chars = 38
    for index, _char in enumerate(text[:max_chars]):
        block_x = x + (index % 19) * 10
        block_y = y + (index // 19) * 14
        draw_filled_rect(surface, (block_x, block_y, 6, 5), palette.MOON_WHITE)
        if index % 3 == 0:
            draw_filled_rect(surface, (block_x + 7, block_y + 2, 1, 2), palette.ASH_GRAY)
