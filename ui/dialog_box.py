"""对话框 UI。"""

from __future__ import annotations

import pygame

from core.event_bus import DIALOG_ACTIVE_CHANGED, DIALOG_CHOICE_SELECTED, EventBus, SHOW_DIALOG
from core.input_manager import InputManager
from utils import palette
from utils.assets import load_image
from utils.font import render_block_text, render_text, render_wrapped_text, wrap_text
from utils.pixel_art import draw_double_rect, draw_filled_rect, draw_rect


class DialogBox:
    """底部对话框，监听 SHOW_DIALOG 并支持交互键推进文本和选项。"""

    SPEAKER_NAMES = {
        "wugang": "吴刚",
        "yutu": "玉兔",
        "repairman": "守月人",
        "toad_statue": "渗血蟾蜍像",
        "sign_board": "告示牌",
        "home_sign": "告示牌",
        "tutorial_shadow": "月影",
        "change": "嫦娥",
        "palace_gate": "广寒宫门",
        "courtyard_gate": "庭院南门",
        "moon_pool": "月池",
        "player": "凌霄来使",
    }
    LARGE_PORTRAIT_SHEET = "sprites/moonspace/portraits/dialog_portraits_large.png"
    PORTRAIT_COLUMNS = {
        "player": 0,
        "change": 1,
        "wugang": 2,
        "yutu": 3,
    }
    NPC_SPEAKERS = {"change", "wugang", "yutu"}

    def __init__(self, event_bus: EventBus) -> None:
        self.event_bus = event_bus
        self.active = False
        self.speaker_id = ""
        self.lines: list[str] = []
        self.current_index = 0
        self.choices: list[dict[str, str]] = []
        self.choice_context = ""
        self.selected_choice_index = 0
        self._blink_timer = 0.0
        self.event_bus.subscribe(SHOW_DIALOG, self._on_show_dialog)

    def update(self, dt: float, input_manager: InputManager) -> None:
        """更新闪烁提示，并在 E/Space 触发时推进文本或确认选项。"""
        if not self.active:
            return

        self._blink_timer += dt
        if self._choices_visible:
            self._update_choice_selection(input_manager)

        if input_manager.was_pressed("interact"):
            self.advance()

    def draw(self, surface: pygame.Surface) -> None:
        """绘制像素风对话框，优先使用真实字体，失败时像素块降级。"""
        if not self.active:
            return

        has_portrait = self.speaker_id in self.PORTRAIT_COLUMNS
        portrait_on_right = self.speaker_id in self.NPC_SPEAKERS
        panel_x = 18 if portrait_on_right or not has_portrait else 112
        panel_width = 350 if has_portrait else 444
        panel = (
            pygame.Rect(panel_x, 158, panel_width, 96)
            if self._choices_visible
            else pygame.Rect(panel_x, 188, panel_width, 66)
        )
        portrait_drawn = self._draw_portrait(surface, right=portrait_on_right) if has_portrait else False
        draw_filled_rect(surface, panel, palette.BLACK)
        draw_double_rect(surface, panel, palette.MOON_WHITE, palette.DEEP_BLUE)
        speaker_name = self.SPEAKER_NAMES.get(self.speaker_id, self.speaker_id)
        title_width = max(96, min(panel.width - 24, 28 + len(speaker_name) * 14))
        draw_filled_rect(surface, (panel.x + 8, panel.y, title_width, 18), palette.DARK_BLOOD)
        draw_rect(surface, panel.x + 8, panel.y, title_width, 18, palette.MOON_WHITE)
        draw_filled_rect(surface, (panel.x + 4, panel.y + 4, 3, 3), palette.BLOOD_RED)
        draw_filled_rect(surface, (panel.right - 7, panel.y + 4, 3, 3), palette.BLOOD_RED)
        draw_filled_rect(surface, (panel.x + 4, panel.bottom - 7, 3, 3), palette.BLOOD_RED)
        draw_filled_rect(surface, (panel.right - 7, panel.bottom - 7, 3, 3), palette.BLOOD_RED)

        text_x = panel.x + 12
        title_x = panel.x + 14
        wrap_width = 22 if portrait_drawn else 27

        if not render_text(surface, f"【{speaker_name}】", title_x, panel.y + 2, 13, palette.PALE_MOON):
            render_block_text(surface, speaker_name, title_x, panel.y + 4)

        line = self.current_line
        wrapped_lines = wrap_text(line, wrap_width)[:2]
        if not render_wrapped_text(
            surface,
            wrapped_lines,
            text_x,
            panel.y + 27,
            14,
            palette.MOON_WHITE,
            15,
        ):
            render_block_text(surface, line, text_x, panel.y + 27)

        if self._choices_visible:
            self._draw_choices(surface, panel, text_x)
        elif int(self._blink_timer * 2) % 2 == 0:
            if not render_text(surface, "E", panel.right - 28, panel.bottom - 18, 12, palette.MOON_WHITE):
                draw_filled_rect(surface, (panel.right - 22, panel.bottom - 14, 8, 2), palette.MOON_WHITE)
                draw_filled_rect(surface, (panel.right - 18, panel.bottom - 10, 4, 2), palette.MOON_WHITE)

    def _draw_portrait(self, surface: pygame.Surface, *, right: bool = False) -> bool:
        """从已确认的四列图集中裁切并绘制大幅半身立绘。"""
        column = self.PORTRAIT_COLUMNS.get(self.speaker_id)
        if column is None:
            return False
        try:
            sheet = load_image(self.LARGE_PORTRAIT_SHEET)
        except (FileNotFoundError, pygame.error):
            return False

        left = round(sheet.get_width() * column / 4)
        crop_right = round(sheet.get_width() * (column + 1) / 4)
        portrait = sheet.subsurface(pygame.Rect(left, 0, crop_right - left, sheet.get_height()))
        portrait_height = 224
        portrait_width = max(1, round(portrait.get_width() * portrait_height / portrait.get_height()))
        portrait = pygame.transform.smoothscale(portrait, (portrait_width, portrait_height))
        frame_x = surface.get_width() - portrait_width - 10 if right else 6
        # 原图已经自带完整边框；不再叠第二层外框，并让底边与对话框底边齐平。
        portrait_y = surface.get_height() - portrait_height - 16
        surface.blit(portrait, (frame_x, portrait_y))
        return True

    def _draw_choices(self, surface: pygame.Surface, panel: pygame.Rect, text_x: int) -> None:
        """绘制当前对话选项。"""
        for index, choice in enumerate(self.choices[:3]):
            y = panel.y + 56 + index * 12
            selected = index == self.selected_choice_index
            marker_color = palette.BLOOD_RED if selected else palette.DEEP_BLUE
            text_color = palette.PALE_MOON if selected else palette.MOON_WHITE
            draw_filled_rect(surface, (text_x, y + 3, 5, 5), marker_color)
            label = choice.get("text", "")
            if not render_text(surface, label, text_x + 10, y, 12, text_color):
                render_block_text(surface, label, text_x + 10, y)

    def _update_choice_selection(self, input_manager: InputManager) -> None:
        """根据方向键/WASD 或数字键更新选项选择。"""
        if not self.choices:
            return

        if self._key_pressed(input_manager, pygame.K_UP, pygame.K_w):
            self.selected_choice_index = (self.selected_choice_index - 1) % len(self.choices)
        if self._key_pressed(input_manager, pygame.K_DOWN, pygame.K_s):
            self.selected_choice_index = (self.selected_choice_index + 1) % len(self.choices)

        number_keys = (pygame.K_1, pygame.K_2, pygame.K_3)
        for index, key in enumerate(number_keys[: len(self.choices)]):
            if self._key_pressed(input_manager, key):
                self.selected_choice_index = index

    @staticmethod
    def _key_pressed(input_manager: InputManager, *keys: int) -> bool:
        """兼容测试替身的物理按键查询。"""
        was_key_pressed = getattr(input_manager, "was_key_pressed", None)
        if was_key_pressed is None:
            return False
        return any(was_key_pressed(key) for key in keys)

    @property
    def _choices_visible(self) -> bool:
        """选项只在最后一句文本出现，避免打断普通对话推进。"""
        return bool(self.choices) and self.current_index >= len(self.lines) - 1

    @property
    def current_line(self) -> str:
        """返回当前文本行。"""
        if not self.lines:
            return ""
        return self.lines[self.current_index]

    def advance(self) -> None:
        """推进到下一行；有选项时确认当前选项。"""
        if not self.active:
            return

        if self._choices_visible:
            choice = self.choices[self.selected_choice_index]
            speaker_id = self.speaker_id
            context = self.choice_context
            self.close()
            self.event_bus.emit(
                DIALOG_CHOICE_SELECTED,
                speaker_id=speaker_id,
                choice_id=choice.get("id", ""),
                choice_text=choice.get("text", ""),
                context=context,
            )
            return

        if self.current_index < len(self.lines) - 1:
            self.current_index += 1
            self._blink_timer = 0.0
            return

        self.close()

    def close(self) -> None:
        """关闭对话框并广播状态。"""
        self.active = False
        speaker_id = self.speaker_id
        self.choices = []
        self.choice_context = ""
        self.selected_choice_index = 0
        self.event_bus.emit(DIALOG_ACTIVE_CHANGED, active=False, speaker_id=speaker_id)

    def _on_show_dialog(
        self,
        speaker_id: str,
        lines: list[str],
        choices: list[dict[str, str]] | None = None,
        choice_context: str = "",
        **payload,
    ) -> None:
        """响应 NPC 或场景物体发出的显示对话事件。"""
        _ = payload
        self.speaker_id = speaker_id
        self.lines = list(lines)
        self.current_index = 0
        self.choices = [dict(choice) for choice in (choices or [])]
        self.choice_context = choice_context
        self.selected_choice_index = 0
        self.active = bool(self.lines)
        self._blink_timer = 0.0
        if self.active:
            self.event_bus.emit(DIALOG_ACTIVE_CHANGED, active=True, speaker_id=self.speaker_id)
