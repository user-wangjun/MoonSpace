"""广寒宫来使登记册交互。"""

from __future__ import annotations

import pygame

import config
from core.input_manager import InputManager
from utils import palette
from utils.font import render_text
from utils.pixel_art import draw_double_rect, draw_filled_rect, draw_rect


class EnvoyRegister:
    """处理登记、旧卷查阅和封卷反馈，不承担主线判定。"""

    MODE_MENU = "menu"
    MODE_WRITE = "write"
    MODE_READ = "read"
    MODE_COMPLETE = "complete"
    MODE_SEALED = "sealed"

    RECORDS = (
        ("第一卷", "甲子六九", "姓名：李玄", "复命：已完成", "归返：已归档"),
        ("第二卷", "甲子七一", "姓名：沈云", "复命：已完成", "归返：已归档"),
        ("第三卷", "甲子七二", "姓名：——", "复命：已完成", "归返：已归档"),
    )

    def __init__(self) -> None:
        self.active = False
        self.mode = self.MODE_MENU
        self.menu_index = 0
        self.page = 0
        self.name = ""
        self.draft_name = ""
        self.registered = False

    def open(self) -> None:
        self.active = True
        self.mode = self.MODE_SEALED if self.registered else self.MODE_MENU
        self.menu_index = 0
        self.draft_name = ""
        pygame.key.start_text_input()

    def close(self) -> None:
        self.active = False
        pygame.key.stop_text_input()

    def update(self, input_manager: InputManager) -> bool:
        """推进交互；登记刚完成时返回 True，便于调用方存档。"""
        if not self.active:
            return False
        if input_manager.was_pressed(config.ACTION_QUIT):
            self.close()
            return False

        if self.mode == self.MODE_SEALED:
            if input_manager.was_pressed(config.ACTION_INTERACT):
                self.close()
            return False

        if self.mode == self.MODE_COMPLETE:
            if input_manager.was_pressed(config.ACTION_INTERACT):
                self.mode = self.MODE_SEALED
            return False

        if self.mode == self.MODE_MENU:
            if input_manager.was_key_pressed(pygame.K_UP) or input_manager.was_key_pressed(pygame.K_DOWN):
                self.menu_index = 1 - self.menu_index
            if input_manager.was_pressed(config.ACTION_INTERACT):
                self.mode = self.MODE_WRITE if self.menu_index == 0 else self.MODE_READ
            return False

        if self.mode == self.MODE_READ:
            if input_manager.was_key_pressed(pygame.K_LEFT):
                self.page = max(0, self.page - 1)
            elif input_manager.was_key_pressed(pygame.K_RIGHT):
                self.page = min(len(self.RECORDS) - 1, self.page + 1)
            elif input_manager.was_key_pressed(pygame.K_BACKSPACE):
                self.mode = self.MODE_MENU
            return False

        if input_manager.was_key_pressed(pygame.K_BACKSPACE):
            self.draft_name = self.draft_name[:-1]
        for char in input_manager.text_input:
            if char.isprintable() and not char.isspace() and len(self.draft_name) < 12:
                self.draft_name += char
        if self.draft_name and (
            input_manager.was_key_pressed(pygame.K_RETURN)
            or input_manager.was_key_pressed(pygame.K_KP_ENTER)
        ):
            self.name = self.draft_name
            self.registered = True
            self.mode = self.MODE_COMPLETE
            return True
        return False

    def draw(self, surface: pygame.Surface) -> None:
        if not self.active:
            return
        shade = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        shade.fill((4, 8, 18, 184))
        surface.blit(shade, (0, 0))
        panel = pygame.Rect(76, 25, 328, 220)
        draw_filled_rect(surface, panel, (27, 53, 62))
        draw_filled_rect(surface, panel.inflate(-8, -8), (170, 207, 190))
        draw_double_rect(surface, panel, palette.PALE_MOON, palette.DEEP_BLUE)
        for x in range(panel.x + 14, panel.right - 12, 18):
            draw_rect(surface, x, panel.y + 12, 14, panel.height - 24, (92, 143, 139))

        render_text(surface, "凌霄来使名录", 176, 41, 18, (24, 54, 58))
        render_text(surface, "Esc 退出", 336, 42, 11, (58, 75, 76))
        if self.mode == self.MODE_MENU:
            self._draw_menu(surface)
        elif self.mode == self.MODE_WRITE:
            self._draw_write(surface)
        elif self.mode == self.MODE_READ:
            self._draw_record(surface)
        elif self.mode == self.MODE_COMPLETE:
            render_text(surface, f"姓名：{self.name}", 166, 102, 17, palette.DARK_BLOOD)
            render_text(surface, "入宫：已登记", 166, 137, 17, (40, 67, 68))
            render_text(surface, "E 合卷", 211, 188, 12, (58, 75, 76))
        else:
            render_text(surface, "本卷已封", 193, 112, 20, palette.DARK_BLOOD)
            render_text(surface, "E / Esc 退出", 198, 151, 12, (58, 75, 76))

    def _draw_menu(self, surface: pygame.Surface) -> None:
        options = ("登记来使身份", "查看旧日记录")
        for index, label in enumerate(options):
            color = palette.DARK_BLOOD if index == self.menu_index else (40, 67, 68)
            prefix = "◇ " if index == self.menu_index else "  "
            render_text(surface, prefix + label, 166, 100 + index * 38, 16, color)
        render_text(surface, "↑↓ 选择    E 打开", 174, 202, 12, (58, 75, 76))

    def _draw_write(self, surface: pygame.Surface) -> None:
        render_text(surface, "姓名", 136, 105, 16, (40, 67, 68))
        shown = self.draft_name or "在此写下姓名"
        color = palette.DARK_BLOOD if self.draft_name else (95, 119, 112)
        render_text(surface, shown, 195, 105, 17, color)
        draw_filled_rect(surface, (190, 130, 168, 1), (58, 75, 76))
        render_text(surface, "输入姓名，按 Enter 落笔", 158, 177, 12, (58, 75, 76))
        render_text(surface, "Esc 可不登记离开", 176, 198, 11, (76, 89, 86))

    def _draw_record(self, surface: pygame.Surface) -> None:
        lines = self.RECORDS[self.page]
        for index, line in enumerate(lines):
            render_text(surface, line, 144, 78 + index * 25, 14, (40, 67, 68))
        if self.page == 2:
            render_text(surface, "不要留下姓名！", 254, 151, 18, palette.DARK_BLOOD)
            draw_filled_rect(surface, (248, 174, 126, 2), palette.DARK_BLOOD)
        render_text(surface, "← 上一卷", 108, 211, 12, (58, 75, 76))
        render_text(surface, f"{self.page + 1} / 3", 226, 211, 12, (58, 75, 76))
        render_text(surface, "下一卷 →", 315, 211, 12, (58, 75, 76))
        render_text(surface, "Backspace 返回", 190, 229, 10, (76, 89, 86))

    def apply_save_data(self, data: dict) -> None:
        self.name = str(data.get("name", ""))[:12]
        self.draft_name = ""
        self.registered = bool(data.get("registered", False))
        self.active = False
        self.mode = self.MODE_SEALED if self.registered else self.MODE_MENU

    def collect_save_data(self) -> dict:
        return {"name": self.name, "registered": self.registered}
