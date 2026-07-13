"""字体渲染测试。"""

import pygame

from utils.font import render_text


def test_render_text_survives_pygame_reinitialization():
    surface = pygame.Surface((160, 32), pygame.SRCALPHA)

    assert render_text(surface, "MoonSpace 血月", 0, 0)

    pygame.quit()
    pygame.init()
    surface = pygame.Surface((160, 32), pygame.SRCALPHA)

    assert render_text(surface, "MoonSpace 血月", 0, 0)
