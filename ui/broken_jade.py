"""首次凝视月池后获得的残破玉简查看界面。"""

from __future__ import annotations

import pygame

import config
from utils import palette
from utils.assets import load_image
from utils.font import render_text, render_wrapped_text, wrap_text
from utils.pixel_art import draw_double_rect, draw_filled_rect


class BrokenJadeView:
    """独立于规则手册的残破玉简拾取与查看界面。"""

    ITEM_PATH = "sprites/moonspace/props/broken_jade_slip.png"
    STAGE_PICKUP = "pickup"
    STAGE_INSPECT = "inspect"
    PICKUP_EXPLANATION = "字迹已被月水浸蚀，无法辨认。"

    def __init__(self) -> None:
        self.acquired = False
        self.active = False
        self.stage = self.STAGE_PICKUP

    def acquire(self) -> None:
        self.acquired = True
        self.active = True
        self.stage = self.STAGE_PICKUP

    def update(self, input_manager) -> None:
        if not self.active:
            return
        if input_manager.was_pressed(config.ACTION_OPEN_RULE_BOOK):
            self.active = False
            return
        if input_manager.was_pressed(config.ACTION_INTERACT):
            if self.stage == self.STAGE_PICKUP:
                self.stage = self.STAGE_INSPECT
            else:
                self.active = False

    def draw(self, surface: pygame.Surface) -> None:
        if not self.active:
            return
        shade = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        shade.fill((*palette.BLACK, 148))
        surface.blit(shade, (0, 0))

        try:
            item = load_image(self.ITEM_PATH)
        except (FileNotFoundError, pygame.error):
            item = None
        if item is not None:
            target_height = 82
            width = max(1, round(item.get_width() * target_height / item.get_height()))
            item = pygame.transform.smoothscale(item, (width, target_height))
            surface.blit(item, item.get_rect(center=(config.SCREEN_WIDTH // 2, 116)))

        panel = pygame.Rect(55, 166, 370, 74)
        draw_filled_rect(surface, panel, palette.BLACK)
        draw_double_rect(surface, panel, palette.MOON_WHITE, palette.DEEP_BLUE)
        if self.stage == self.STAGE_PICKUP:
            render_text(surface, "获得：残破玉简", 176, 180, 15, palette.PALE_MOON)
            render_text(surface, self.PICKUP_EXPLANATION, 118, 201, 10, palette.MOON_WHITE)
            render_text(surface, "E 打开", 218, 222, 11, palette.ASH_GRAY)
        else:
            lines = wrap_text("由于太过破旧和长时间的浸泡，根本无法辨别上面的字迹....", 24)
            render_wrapped_text(surface, lines[:2], 72, 178, 12, palette.MOON_WHITE, 15)
            render_text(surface, "E 收起", 218, 222, 11, palette.ASH_GRAY)
