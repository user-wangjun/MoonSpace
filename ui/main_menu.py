"""主菜单 UI。"""

from __future__ import annotations

import math

import pygame

import config
from core.input_manager import InputManager
from utils import palette
from utils.assets import load_image
from utils.font import load_font, render_text
from utils.pixel_art import draw_filled_rect


MENU_NEW_GAME = "new_game"
MENU_LOAD_GAME = "load_game"
MENU_SETTINGS = "settings"
MENU_DELETE_SAVE = "delete_save"
MENU_QUIT = "quit"


class MainMenu:
    """游戏启动主菜单：新游戏、读档、设置、删除存档、退出。"""

    MENU_ITEMS = (
        ("1  新游戏", MENU_NEW_GAME),
        ("2  读档", MENU_LOAD_GAME),
        ("3  设置", MENU_SETTINGS),
        ("4  删除存档", MENU_DELETE_SAVE),
        ("5  退出", MENU_QUIT),
    )

    def __init__(self) -> None:
        self.selected_action: str | None = None
        self.selected_index = 0
        self.animation_time = 0.0

    def layout(self) -> dict[str, object]:
        """计算主菜单文字与面板矩形，避免不同中文字体下贴边。"""
        panel = pygame.Rect(82, 42, 316, 204)
        title_size = 18
        item_size = 14
        esc_size = 11

        title_font = load_font(title_size)
        item_font = load_font(item_size)
        esc_font = load_font(esc_size)

        title_text = "MoonSpace（月之隙）"
        title_width, title_height = title_font.size(title_text)
        title_rect = pygame.Rect(
            panel.centerx - title_width // 2,
            panel.y + 20,
            title_width,
            title_height,
        )

        item_rects = []
        start_y = panel.y + 52
        for index, (label, _action) in enumerate(self.MENU_ITEMS):
            width, height = item_font.size(label)
            item_rects.append(
                pygame.Rect(
                    panel.centerx - width // 2,
                    start_y + index * 28,
                    width,
                    height,
                )
            )

        esc_text = "Esc 退出"
        esc_width, esc_height = esc_font.size(esc_text)
        esc_rect = pygame.Rect(
            config.SCREEN_WIDTH - esc_width - 12,
            config.SCREEN_HEIGHT - esc_height - 12,
            esc_width,
            esc_height,
        )

        return {
            "panel": panel,
            "inner": pygame.Rect(panel.x + 8, panel.y + 8, panel.width - 16, panel.height - 16),
            "panel_points": (
                panel.topleft,
                panel.topright,
                panel.bottomright,
                panel.bottomleft,
            ),
            "inner_points": (
                (panel.left + 10, panel.top + 10),
                (panel.right - 10, panel.top + 10),
                (panel.right - 10, panel.bottom - 10),
                (panel.left + 10, panel.bottom - 10),
            ),
            "highlight_points": (
                (panel.left + 16, panel.top + 14),
                (panel.right - 16, panel.top + 14),
                (panel.right - 28, panel.top + 48),
                (panel.left + 28, panel.top + 48),
            ),
            "title": title_rect,
            "title_size": title_size,
            "items": item_rects,
            "item_size": item_size,
            "esc": esc_rect,
            "esc_size": esc_size,
        }

    def update(self, dt: float, input_manager: InputManager) -> str | None:
        """处理菜单快捷键、选中项和背景动画时间。"""
        self.animation_time += dt
        if input_manager.was_pressed(config.ACTION_QUIT):
            return MENU_QUIT

        if input_manager.was_key_pressed(pygame.K_1):
            return MENU_NEW_GAME
        if input_manager.was_key_pressed(pygame.K_2):
            return MENU_LOAD_GAME
        if input_manager.was_key_pressed(pygame.K_3):
            return MENU_SETTINGS
        if input_manager.was_key_pressed(pygame.K_4):
            return MENU_DELETE_SAVE
        if input_manager.was_key_pressed(pygame.K_5):
            return MENU_QUIT

        if input_manager.was_key_pressed(pygame.K_UP) or input_manager.was_key_pressed(pygame.K_w):
            self.selected_index = (self.selected_index - 1) % len(self.MENU_ITEMS)
        elif input_manager.was_key_pressed(pygame.K_DOWN) or input_manager.was_key_pressed(pygame.K_s):
            self.selected_index = (self.selected_index + 1) % len(self.MENU_ITEMS)

        if input_manager.was_key_pressed(pygame.K_RETURN) or input_manager.was_pressed(config.ACTION_INTERACT):
            self.selected_action = self.MENU_ITEMS[self.selected_index][1]
            return self.selected_action
        return None

    def draw(self, surface: pygame.Surface) -> None:
        """绘制主菜单。"""
        try:
            background = load_image("sprites/moonspace/main_menu_bg.png")
        except (FileNotFoundError, pygame.error):
            background = None

        cloud_shift = int(self.animation_time * 8) % 64
        moon_pulse = int((math.sin(self.animation_time * 2.4) + 1) * 2)
        if background is not None:
            surface.blit(background, (0, 0))
        else:
            surface.fill(palette.NIGHT_BLACK)
            draw_filled_rect(surface, (0, 178, config.SCREEN_WIDTH, 92), palette.GROUND_DARK)
            for cloud_x in range(-64, config.SCREEN_WIDTH + 64, 96):
                draw_filled_rect(surface, (cloud_x + cloud_shift, 68, 52, 5), palette.DEEP_BLUE)
                draw_filled_rect(surface, (cloud_x + 18 + cloud_shift, 61, 38, 6), palette.GROUND_MID)
            for x in range(0, config.SCREEN_WIDTH, 32):
                draw_filled_rect(surface, (x, 158, 22, 32), palette.PALACE_STONE)
                draw_filled_rect(surface, (x + 4, 148, 14, 10), palette.DEEP_BLUE)
                draw_filled_rect(surface, (x + 8, 166, 6, 10), palette.BLACK)
            draw_filled_rect(surface, (180, 134, 120, 56), palette.PALACE_STONE)
            draw_filled_rect(surface, (194, 122, 92, 14), palette.DEEP_BLUE)
            draw_filled_rect(surface, (226, 146, 28, 44), palette.BLACK)
            draw_filled_rect(surface, (238, 139, 4, 38), palette.PALE_MOON)

            pygame.draw.circle(surface, palette.DARK_BLOOD, (240, 58), 30 + moon_pulse)
            pygame.draw.circle(surface, palette.BLOOD_RED, (240, 58), 24 + moon_pulse // 2)
            pygame.draw.circle(surface, palette.PALE_MOON, (230, 49), 3)
        layout = self.layout()
        panel = layout["panel"]

        self._draw_straight_glass_panel(surface, layout)

        title_rect = layout["title"]
        render_text(surface, "MoonSpace（月之隙）", title_rect.x, title_rect.y, layout["title_size"], palette.PALE_MOON)
        item_rects = layout["items"]
        for index, (label, _action) in enumerate(self.MENU_ITEMS):
            item_rect = item_rects[index]
            color = palette.PALE_MOON if index == self.selected_index else palette.MOON_WHITE
            if index == len(self.MENU_ITEMS) - 1:
                color = palette.ASH_GRAY if index != self.selected_index else palette.MOON_WHITE
            if index == self.selected_index and int(self.animation_time * 4) % 2 == 0:
                draw_filled_rect(surface, (item_rect.x - 26, item_rect.y + item_rect.height // 2 - 1, 9, 3), palette.BLOOD_RED)
            render_text(surface, label, item_rect.x, item_rect.y, layout["item_size"], color)
        esc_rect = layout["esc"]
        render_text(surface, "Esc 退出", esc_rect.x, esc_rect.y, layout["esc_size"], palette.ASH_GRAY)

        draw_filled_rect(surface, (0, 0, 480, 4), palette.BLOOD_RED)
        draw_filled_rect(surface, (0, 266, 480, 4), palette.DARK_BLOOD)

    def _draw_straight_glass_panel(self, surface: pygame.Surface, layout: dict[str, object]) -> None:
        """绘制正放半透明菜单面板，保留背景可见性。"""
        panel_points = layout["panel_points"]
        inner_points = layout["inner_points"]
        highlight_points = layout["highlight_points"]
        panel = layout["panel"]

        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        pygame.draw.rect(overlay, (8, 10, 18, 176), panel)
        pygame.draw.polygon(overlay, (70, 86, 104, 44), highlight_points)
        surface.blit(overlay, (0, 0))

        pygame.draw.polygon(surface, palette.DARK_BLOOD, panel_points, 2)
        pygame.draw.rect(surface, palette.MOON_WHITE, panel.inflate(-6, -6), 1)
        pygame.draw.polygon(surface, palette.DEEP_BLUE, inner_points, 1)
        draw_filled_rect(surface, (panel.left + 18, panel.bottom - 18, panel.width - 36, 1), palette.DARK_BLOOD)
