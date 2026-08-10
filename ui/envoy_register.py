"""广寒宫来使登记与旧卷查阅界面。"""

from __future__ import annotations

import pygame

import config
from core.input_manager import InputManager
from utils import palette
from utils.assets import load_image
from utils.font import load_font
from utils.pixel_art import draw_double_rect, draw_filled_rect


class EnvoyRegister:
    """用同一套十五片玉简制式处理登记、旧卷查阅与封卷。"""

    MODE_MENU = "menu"
    MODE_VERIFY = "verify"
    MODE_WRITE = "write"
    MODE_READ = "read"
    MODE_COMPLETE = "complete"
    MODE_SEALED = "sealed"

    MAX_NAME_LENGTH = 4
    ETCH_INTERVAL = 0.15
    SLIP_BOUNDARIES = (42, 70, 97, 124, 151, 178, 204, 231, 258, 285, 311, 337, 363, 388, 412, 435)
    NAME_SLIP_INDEX = 11
    BACKGROUNDS = (
        "sprites/moonspace/ui/jade_register_volume_1.png",
        "sprites/moonspace/ui/jade_register_volume_2.png",
        "sprites/moonspace/ui/jade_register_volume_3.png",
    )
    RECORD_COLUMNS = (
        (
            "第一卷", "甲子七二", "凌霄来使", "姓名李玄", "奉命巡月",
            "月桂无异", "玉兔如常", "入宫复命", "登记无误", "候月一刻",
            "准返凌霄", "神志清明", "形貌如初", "归返归档", "广寒宫录",
        ),
        (
            "第二卷", "甲子七一", "凌霄来使", "姓名沈云", "奉命点药",
            "药杵无损", "玉兔如常", "月桂未查", "入宫复命", "登记无误",
            "候月二刻", "准返凌霄", "神志清明", "药册归档", "广寒宫录",
        ),
        (
            "第三卷", "甲子六九", "凌霄来使", "姓名无载", "奉命巡池",
            "月池有影", "桂下无人", "玉兔停杵", "入宫复命", "登记有缺",
            "候月三刻", "返程无录", "神志无录", "墨迹中断", "勿留姓名",
        ),
    )
    # 兼容已有测试和可能读取旧结构的外部代码。
    RECORDS = RECORD_COLUMNS

    def __init__(self) -> None:
        self.active = False
        self.mode = self.MODE_VERIFY
        self.menu_index = 0
        self.page = 0
        self.name = ""
        self.draft_name = ""
        self.registered = False
        self.etched_char_count = 0
        self.etch_timer = 0.0

    def open(self) -> None:
        """兼容旧调用：打开登记入口。"""
        self.open_register()

    def open_register(self) -> None:
        """从登记位置打开可选的来使验牒，不要求输入个人姓名。"""
        self.active = True
        self.mode = self.MODE_SEALED if self.registered else self.MODE_VERIFY
        self.menu_index = 0
        self.draft_name = ""
        self.etched_char_count = 0
        self.etch_timer = 0.0
        pygame.key.stop_text_input()

    def open_records(self) -> None:
        """从查阅位置直接打开由新到旧排列的三卷名录。"""
        self.active = True
        self.mode = self.MODE_READ
        self.page = 0
        self.draft_name = ""
        self.etched_char_count = 0
        self.etch_timer = 0.0
        pygame.key.stop_text_input()

    def close(self) -> None:
        self.active = False
        pygame.key.stop_text_input()

    def update(self, input_manager: InputManager, dt: float = 0.0) -> bool:
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

        if self.mode == self.MODE_READ:
            if input_manager.was_key_pressed(pygame.K_LEFT):
                self.page = max(0, self.page - 1)
            elif input_manager.was_key_pressed(pygame.K_RIGHT):
                self.page = min(len(self.RECORD_COLUMNS) - 1, self.page + 1)
            elif input_manager.was_key_pressed(pygame.K_BACKSPACE):
                self.close()
            return False

        if self.mode == self.MODE_VERIFY:
            if input_manager.was_pressed(config.ACTION_INTERACT):
                self.registered = True
                self.mode = self.MODE_COMPLETE
                return True
            return False

        if self.mode == self.MODE_MENU:
            self.mode = self.MODE_WRITE

        if input_manager.was_key_pressed(pygame.K_BACKSPACE):
            self.draft_name = self.draft_name[:-1]
            self.etched_char_count = min(self.etched_char_count, len(self.draft_name))
            self.etch_timer = 0.0
        for char in input_manager.text_input:
            if char.isprintable() and not char.isspace() and len(self.draft_name) < self.MAX_NAME_LENGTH:
                self.draft_name += char

        self._update_etch_animation(max(0.0, dt))

        if self.draft_name and (
            input_manager.was_key_pressed(pygame.K_RETURN)
            or input_manager.was_key_pressed(pygame.K_KP_ENTER)
        ):
            self.name = self.draft_name
            self.registered = True
            self.etched_char_count = len(self.name)
            self.mode = self.MODE_COMPLETE
            pygame.key.stop_text_input()
            return True
        return False

    def _update_etch_animation(self, dt: float) -> None:
        """让已输入姓名以固定节奏逐字刻入玉片。"""
        if self.etched_char_count >= len(self.draft_name):
            self.etch_timer = 0.0
            return
        self.etch_timer += dt
        while self.etch_timer >= self.ETCH_INTERVAL and self.etched_char_count < len(self.draft_name):
            self.etch_timer -= self.ETCH_INTERVAL
            self.etched_char_count += 1

    def draw(self, surface: pygame.Surface) -> None:
        if not self.active:
            return
        page = self.page if self.mode == self.MODE_READ else 0
        self._draw_background(surface, page)

        if self.mode == self.MODE_READ:
            self._draw_columns(surface, self.RECORD_COLUMNS[self.page], warning=self.page == 2)
            self._draw_navigation(surface)
            return

        if self.mode == self.MODE_VERIFY:
            self._draw_columns(surface, self._verification_columns())
            self._draw_identity_verify(surface)
            return

        finalized = self.mode in (self.MODE_COMPLETE, self.MODE_SEALED)
        if self.mode == self.MODE_WRITE:
            self._draw_name_highlight(surface)
        self._draw_columns(surface, self._registration_columns(finalized))
        if self.mode == self.MODE_WRITE:
            self._draw_name_input(surface)
        else:
            self._draw_close_action(surface, "E 合卷" if self.mode == self.MODE_COMPLETE else "E / Esc 退出")

    def _draw_background(self, surface: pygame.Surface, page: int) -> None:
        try:
            background = load_image(self.BACKGROUNDS[page])
            if background.get_size() != surface.get_size():
                background = pygame.transform.smoothscale(background, surface.get_size())
            surface.blit(background, (0, 0))
        except (FileNotFoundError, pygame.error):
            surface.fill(palette.NIGHT_BLACK)

    @classmethod
    def _slip_safe_rects(cls) -> list[pygame.Rect]:
        return [
            pygame.Rect(left + 3, 136, right - left - 6, 54)
            for left, right in zip(cls.SLIP_BOUNDARIES, cls.SLIP_BOUNDARIES[1:])
        ]

    def _draw_columns(self, surface: pygame.Surface, columns: tuple[str, ...], *, warning: bool = False) -> None:
        font = load_font(10)
        safe_rects = self._slip_safe_rects()
        for column, slip_index in zip(columns, range(len(safe_rects) - 1, -1, -1)):
            safe = safe_rects[slip_index]
            color = (112, 18, 22) if warning and column == "勿留姓名" else (18, 29, 27)
            start_y = 149 if len(column) <= 2 else 137
            for row, char in enumerate(column[:4]):
                glyph = font.render(char, False, color)
                rect = glyph.get_rect(midtop=(safe.centerx, start_y + row * 12))
                surface.blit(glyph, rect)

    def _registration_columns(self, finalized: bool) -> tuple[str, ...]:
        if finalized:
            shown_name = self.name or "无名"
            registration_status = "登记已成"
        else:
            shown_name = self.draft_name[: self.etched_char_count] or "待书"
            registration_status = "入宫登记"
        return (
            "新登记", "凌霄来使", "来使姓名", shown_name,
            "职司已验", "月桂已查", "玉兔已查", registration_status,
            "复命未毕", "候月未定", "返程未定", "神志清明",
            "形貌如初", "尚未归档", "广寒宫录",
        )

    @staticmethod
    def _verification_columns() -> tuple[str, ...]:
        """验牒页只确认已有来使身份，明确提示不必留下姓名。"""
        return (
            "身份验牒", "凌霄来使", "姓名不记", "无需留名",
            "职司待验", "月桂待查", "玉兔待查", "复命未毕",
            "不得代职", "不得候宫", "准入广寒", "归返月谷",
            "旧卷可阅", "验牒可撤", "广寒宫录",
        )

    def _draw_identity_verify(self, surface: pygame.Surface) -> None:
        """绘制不收集姓名的身份确认提示。"""
        panel = pygame.Rect(94, 219, 292, 25)
        draw_filled_rect(surface, panel, (4, 8, 15))
        draw_double_rect(surface, panel, palette.MOON_WHITE, palette.DEEP_BLUE)
        font = load_font(10)
        text = font.render("身份：凌霄来使    无需留名", False, palette.MOON_WHITE)
        surface.blit(text, text.get_rect(center=panel.center))
        self._draw_button(surface, pygame.Rect(126, 249, 105, 18), "Esc 退出", active=False)
        self._draw_button(surface, pygame.Rect(249, 249, 105, 18), "E 确认验牒", active=True)

    def _draw_name_highlight(self, surface: pygame.Surface) -> None:
        left = self.SLIP_BOUNDARIES[self.NAME_SLIP_INDEX]
        right = self.SLIP_BOUNDARIES[self.NAME_SLIP_INDEX + 1]
        rect = pygame.Rect(left + 2, 132, right - left - 4, 62)
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        pygame.draw.rect(overlay, (205, 180, 92, 42), rect)
        pygame.draw.rect(overlay, (225, 205, 120, 210), rect, 1)
        surface.blit(overlay, (0, 0))

    def _draw_name_input(self, surface: pygame.Surface) -> None:
        input_panel = pygame.Rect(105, 219, 270, 25)
        draw_filled_rect(surface, input_panel, (4, 8, 15))
        draw_double_rect(surface, input_panel, palette.MOON_WHITE, palette.DEEP_BLUE)
        font = load_font(11)
        typed = font.render(f"姓名：{self.draft_name}│", False, palette.MOON_WHITE)
        surface.blit(typed, typed.get_rect(center=input_panel.center))

        self._draw_button(surface, pygame.Rect(126, 249, 105, 18), "Esc 退出", active=False)
        self._draw_button(surface, pygame.Rect(249, 249, 105, 18), "Enter 登记", active=True)

    @staticmethod
    def _draw_button(surface: pygame.Surface, rect: pygame.Rect, label: str, *, active: bool) -> None:
        draw_filled_rect(surface, rect, (25, 35, 45) if active else (4, 8, 15))
        draw_double_rect(surface, rect, (225, 205, 120) if active else palette.MOON_WHITE, palette.DEEP_BLUE)
        font = load_font(9)
        text = font.render(label, False, (244, 222, 145) if active else palette.MOON_WHITE)
        surface.blit(text, text.get_rect(center=rect.center))

    def _draw_navigation(self, surface: pygame.Surface) -> None:
        panel = pygame.Rect(128, 244, 224, 19)
        draw_filled_rect(surface, panel, (4, 8, 15))
        draw_double_rect(surface, panel, palette.MOON_WHITE, palette.DEEP_BLUE)
        font = load_font(10)
        text = font.render(f"← 上一卷    {self.page + 1} / 3    下一卷 →", False, palette.MOON_WHITE)
        surface.blit(text, text.get_rect(center=panel.center))

    def _draw_close_action(self, surface: pygame.Surface, label: str) -> None:
        rect = pygame.Rect(174, 244, 132, 20)
        self._draw_button(surface, rect, label, active=True)

    def apply_save_data(self, data: dict) -> None:
        self.name = str(data.get("name", ""))[: self.MAX_NAME_LENGTH]
        self.draft_name = ""
        self.registered = bool(data.get("registered", False))
        self.active = False
        self.mode = self.MODE_SEALED if self.registered else self.MODE_VERIFY
        self.etched_char_count = 0
        self.etch_timer = 0.0

    def collect_save_data(self) -> dict:
        return {"name": self.name, "registered": self.registered}
