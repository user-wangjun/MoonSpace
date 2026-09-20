"""游戏内暂停菜单 UI。"""

from __future__ import annotations

import pygame

import config
from core.input_manager import InputManager
from utils import palette
from utils.font import load_font, render_text
from utils.pixel_art import draw_double_rect, draw_filled_rect, draw_rect


PAUSE_RESUME = "pause_resume"
PAUSE_SAVE = "pause_save"
PAUSE_LOAD = "pause_load"
PAUSE_SETTINGS = "pause_settings"
PAUSE_MAIN_MENU = "pause_main_menu"


class PauseMenu:
    """冻结游戏逻辑时使用的轻量菜单。"""

    MENU_ITEMS = (
        ("1  继续游戏", PAUSE_RESUME),
        ("2  备份存档点", PAUSE_SAVE),
        ("3  读取存档", PAUSE_LOAD),
        ("4  设置", PAUSE_SETTINGS),
        ("5  返回主菜单", PAUSE_MAIN_MENU),
    )

    def __init__(self) -> None:
        self.selected_index = 0
        self.animation_time = 0.0

    def open(self) -> None:
        """打开并将选择归位到继续游戏。"""
        self.selected_index = 0
        self.animation_time = 0.0

    def update(self, dt: float, input_manager: InputManager) -> str | None:
        """处理上下选择、数字快捷键、确认和 Esc 返回游戏。"""
        self.animation_time += max(0.0, dt)
        if input_manager.was_pressed(config.ACTION_QUIT):
            return PAUSE_RESUME

        for index, key in enumerate((pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5)):
            if input_manager.was_key_pressed(key):
                self.selected_index = index
                return self.MENU_ITEMS[index][1]

        if input_manager.was_key_pressed(pygame.K_UP) or input_manager.was_key_pressed(pygame.K_w):
            self.selected_index = (self.selected_index - 1) % len(self.MENU_ITEMS)
        elif input_manager.was_key_pressed(pygame.K_DOWN) or input_manager.was_key_pressed(pygame.K_s):
            self.selected_index = (self.selected_index + 1) % len(self.MENU_ITEMS)

        if input_manager.was_key_pressed(pygame.K_RETURN) or input_manager.was_pressed(config.ACTION_INTERACT):
            return self.MENU_ITEMS[self.selected_index][1]
        return None

    def draw(self, surface: pygame.Surface) -> None:
        """在冻结的场景上绘制半透明暂停面板。"""
        shade = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        shade.fill((0, 0, 0, 158))
        surface.blit(shade, (0, 0))

        panel = pygame.Rect(82, 42, 316, 204)
        draw_filled_rect(surface, panel, palette.BLACK)
        draw_double_rect(surface, panel, palette.MOON_WHITE, palette.DARK_BLOOD)
        render_text(surface, "游戏暂停", panel.centerx - 42, panel.y + 18, 18, palette.PALE_MOON)
        draw_filled_rect(surface, (panel.x + 20, panel.y + 48, panel.width - 40, 1), palette.DEEP_BLUE)

        font = load_font(14)
        start_y = panel.y + 62
        for index, (label, _action) in enumerate(self.MENU_ITEMS):
            width, height = font.size(label)
            rect = pygame.Rect(panel.centerx - width // 2, start_y + index * 27, width, height)
            color = palette.PALE_MOON if index == self.selected_index else palette.MOON_WHITE
            if index == self.selected_index and int(self.animation_time * 4) % 2 == 0:
                draw_filled_rect(surface, (rect.x - 24, rect.y + rect.height // 2 - 1, 8, 3), palette.BLOOD_RED)
            render_text(surface, label, rect.x, rect.y, 14, color)

        render_text(surface, "↑↓ / WASD 选择    Enter / E 确认    Esc 继续", 106, 232, 10, palette.ASH_GRAY)
