"""存档选择菜单。"""

from __future__ import annotations

import pygame

import config
from core.input_manager import InputManager
from core.save_manager import SaveManager
from utils import palette
from utils.font import render_text
from utils.pixel_art import draw_filled_rect, draw_rect


SAVE_MODE_NEW = "new"
SAVE_MODE_LOAD = "load"
SAVE_MODE_DELETE = "delete"
SAVE_MODE_SAVE = "save"
# Descriptive alias for integrations that prefer the full action name.
SAVE_MODE_SAVE_GAME = SAVE_MODE_SAVE


class SaveMenu:
    """三槽位存档菜单，可用于新游戏、读档、保存当前进度或删除存档。"""

    def __init__(self, save_manager: SaveManager) -> None:
        self.save_manager = save_manager
        self.mode = SAVE_MODE_LOAD
        self.selected_slot: int | None = None
        self.back_requested = False
        self.delete_message_timer = 0.0
        self.message = ""
        self.slots = self.save_manager.list_slots()
        self.back_destination = "主菜单"

    def open(self, mode: str, *, back_destination: str = "主菜单") -> None:
        """以指定模式打开存档菜单。"""
        self.mode = mode
        self.selected_slot = None
        self.back_requested = False
        self.message = ""
        self.delete_message_timer = 0.0
        self.back_destination = back_destination
        self.refresh()

    def refresh(self) -> None:
        """刷新槽位摘要。"""
        self.slots = self.save_manager.list_slots()

    def update(self, dt: float, input_manager: InputManager) -> int | None:
        """处理槽位选择；删除模式会直接删除并刷新，不返回槽位。"""
        self.delete_message_timer = max(0.0, self.delete_message_timer - dt)
        if self.delete_message_timer == 0.0:
            self.message = ""

        if input_manager.was_pressed(config.ACTION_QUIT):
            self.back_requested = True
            return None

        for slot_id, key in ((1, pygame.K_1), (2, pygame.K_2), (3, pygame.K_3)):
            if not input_manager.was_key_pressed(key):
                continue
            self.selected_slot = slot_id
            if self.mode == SAVE_MODE_DELETE:
                self._delete_slot(slot_id)
                return None
            summary = self.slots[slot_id - 1]
            if self.mode == SAVE_MODE_LOAD and summary.get("corrupted", False):
                self.message = f"槽位 {slot_id} 存档损坏，请删除后重建"
                self.delete_message_timer = 2.0
                return None
            return slot_id
        return None

    def show_message(self, message: str, duration: float = 2.0) -> None:
        """显示保存成功等非删除提示。"""
        self.message = message
        self.delete_message_timer = max(0.0, duration)

    def draw(self, surface: pygame.Surface, *, overlay: bool = False) -> None:
        """绘制存档菜单。"""
        if overlay:
            shade = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
            shade.fill((0, 0, 0, 170))
            surface.blit(shade, (0, 0))
        else:
            surface.fill(palette.NIGHT_BLACK)
        render_text(surface, "MoonSpace（月之隙）", 148, 30, 22, palette.PALE_MOON)
        render_text(surface, self._title(), 180, 64, 15, palette.MOON_WHITE)

        for index, summary in enumerate(self.slots):
            self._draw_slot(surface, summary, 76, 96 + index * 48)

        hint = self._hint()
        render_text(surface, hint, 112, 238, 12, palette.ASH_GRAY)
        if self.message:
            render_text(surface, self.message, 170, 218, 12, palette.BLOOD_RED)

    def _delete_slot(self, slot_id: int) -> None:
        """删除槽位并显示短提示。"""
        summary = self.slots[slot_id - 1]
        if not summary.get("exists", False):
            self.message = f"槽位 {slot_id} 没有存档"
        else:
            self.save_manager.delete(slot_id)
            self.message = f"槽位 {slot_id} 已删除"
        self.delete_message_timer = 1.2
        self.refresh()

    def _title(self) -> str:
        """返回当前模式标题。"""
        if self.mode == SAVE_MODE_NEW:
            return "选择新游戏槽位"
        if self.mode == SAVE_MODE_DELETE:
            return "选择要删除的存档"
        if self.mode == SAVE_MODE_SAVE:
            return "选择存档点备份槽位"
        return "选择要读取的存档"

    def _hint(self) -> str:
        """返回当前模式操作提示。"""
        if self.mode == SAVE_MODE_DELETE:
            return "按 1 / 2 / 3 删除对应槽位    Esc 返回"
        if self.mode == SAVE_MODE_SAVE:
            return f"按 1 / 2 / 3 备份最近存档点    Esc 返回{self.back_destination}"
        return f"按 1 / 2 / 3 选择槽位    Esc 返回{self.back_destination}"

    def _draw_slot(self, surface: pygame.Surface, summary: dict, x: int, y: int) -> None:
        """绘制单个槽位卡片。"""
        rect = pygame.Rect(x, y, 328, 36)
        draw_filled_rect(surface, rect, palette.BLACK)
        draw_rect(surface, rect.x, rect.y, rect.width, rect.height, palette.MOON_WHITE)

        slot_id = summary["slot_id"]
        if summary.get("corrupted", False):
            title = f"槽位 {slot_id}：存档损坏"
            if self.mode == SAVE_MODE_DELETE:
                detail = "可按数字键删除后重建"
            elif self.mode == SAVE_MODE_SAVE:
                detail = "保存当前进度会覆盖这个损坏的存档"
            elif self.mode == SAVE_MODE_NEW:
                detail = "新游戏会覆盖这个损坏的存档"
            else:
                detail = "请先返回主菜单并选择删除存档"
        elif summary["exists"]:
            action_label = "覆盖保存" if self.mode == SAVE_MODE_SAVE else "继续游戏"
            title = f"槽位 {slot_id}：{action_label}"
            detail = (
                f"{summary.get('saved_at', '未知时间')}  "
                f"规则 {summary.get('known_rule_count', 0)}  "
                f"违规 {summary.get('violation_count', 0)}/3"
            )
        else:
            title = f"槽位 {slot_id}：空"
            detail = "备份最近完成事件的存档" if self.mode == SAVE_MODE_SAVE else "新游戏将从血月之夜开始"

        if self.mode == SAVE_MODE_DELETE and not summary["exists"]:
            title = f"槽位 {slot_id}：空"
            detail = "无可删除存档"

        render_text(surface, title, x + 12, y + 6, 14, palette.PALE_MOON)
        render_text(surface, detail, x + 12, y + 21, 11, palette.ASH_GRAY)
