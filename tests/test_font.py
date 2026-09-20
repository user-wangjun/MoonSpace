"""字体渲染测试。"""

import pygame
import sys
from pathlib import Path

from utils.font import render_text, load_font


def test_render_text_survives_pygame_reinitialization():
    surface = pygame.Surface((160, 32), pygame.SRCALPHA)

    assert render_text(surface, "MoonSpace 血月", 0, 0)

    pygame.quit()
    pygame.init()
    surface = pygame.Surface((160, 32), pygame.SRCALPHA)
    assert render_text(surface, "MoonSpace 血月", 0, 0)


def test_bundled_pixel_fonts_render_small_chinese_at_native_grid():
    font = load_font(13)
    assert font.size("月宫规条")[0] == 48
    assert all(metric is not None for metric in font.metrics("嫦娥吴刚稽首药杵月桂"))
    glyph = font.render("月", False, (255, 255, 255))
    assert glyph.get_bounding_rect().height <= 12


def test_frozen_build_loads_its_bundled_font(monkeypatch, tmp_path):
    import shutil
    font_dir = tmp_path / "assets" / "fonts"
    font_dir.mkdir(parents=True)
    shutil.copyfile(
        Path("assets/fonts/fusion-pixel-12px-monospaced-zh_hans.otf"),
        font_dir / "fusion-pixel-12px-monospaced-zh_hans.otf",
    )
    monkeypatch.setattr(sys, "_MEIPASS", str(tmp_path), raising=False)
    assert load_font(14).size("月宫规条")[0] == 48
