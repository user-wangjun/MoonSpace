"""规则手册 UI。"""

from __future__ import annotations

import pygame

from core.event_bus import EventBus, RULE_DISCOVERED
from core.game_state import GameState
from core.input_manager import InputManager
from utils import palette
from utils.font import render_block_text, render_text, wrap_text
from utils.pixel_art import draw_double_rect, draw_filled_rect, draw_rect


class RuleBook:
    """Tab 打开/关闭的规则手册，展示玩家已发现的规则。"""

    def __init__(self, event_bus: EventBus, game_state: GameState) -> None:
        self.event_bus = event_bus
        self.game_state = game_state
        self.is_open = False
        self.rules: dict[str, str] = dict(game_state.known_rules)
        self.broken_jade_obtained = False
        self.scroll_line = 0
        self.event_bus.subscribe(RULE_DISCOVERED, self._on_rule_discovered)

    def update(self, dt: float, input_manager: InputManager) -> None:
        """处理 Tab 切换。"""
        _ = dt
        if input_manager.was_pressed("open_rule_book"):
            self.toggle()
            return
        if not self.is_open:
            return
        delta = 0
        if self._key_pressed(input_manager, pygame.K_UP, pygame.K_w, pygame.K_PAGEUP):
            delta -= 1
        if self._key_pressed(input_manager, pygame.K_DOWN, pygame.K_s, pygame.K_PAGEDOWN):
            delta += 1
        scroll_y = int(getattr(input_manager, "scroll_y", 0))
        if scroll_y:
            delta -= scroll_y
        if delta:
            self.scroll_line = max(0, min(self._max_scroll(), self.scroll_line + delta))

    def draw(self, surface: pygame.Surface) -> None:
        """绘制规则手册面板。"""
        if not self.is_open:
            return

        panel = pygame.Rect(58, 28, 364, 212)
        draw_filled_rect(surface, panel, palette.WOOD_DARK)
        draw_filled_rect(surface, (panel.x + 4, panel.y + 4, panel.width - 8, panel.height - 8), palette.BLACK)
        draw_double_rect(surface, panel, palette.MOON_WHITE, palette.DARK_BLOOD)
        draw_filled_rect(surface, (panel.x + 10, panel.y + 34, panel.width - 20, 2), palette.DARK_BLOOD)
        draw_filled_rect(surface, (panel.x + 12, panel.bottom - 16, panel.width - 24, 1), palette.WOOD_DARK)

        if not render_text(surface, "月宫规条", panel.x + 14, panel.y + 10, 18, palette.PALE_MOON):
            render_block_text(surface, "月宫规条", panel.x + 14, panel.y + 14)
        render_text(surface, "Tab 关闭", panel.right - 74, panel.y + 14, 11, palette.ASH_GRAY)

        lines = self._visual_lines()
        if not lines:
            lines = ["尚未发现任何规则。靠近告示牌按 E 阅读。"]
        self.scroll_line = max(0, min(self._max_scroll(lines), self.scroll_line))
        content_rect = pygame.Rect(panel.x + 16, panel.y + 42, panel.width - 48, panel.height - 64)
        old_clip = surface.get_clip()
        surface.set_clip(content_rect)
        for index, line in enumerate(lines[self.scroll_line : self.scroll_line + self._visible_line_count()] ):
            y = content_rect.y + index * 18
            if not render_text(surface, line, content_rect.x, y, 13, palette.MOON_WHITE):
                render_block_text(surface, line, content_rect.x, y + 2)
        surface.set_clip(old_clip)
        self._draw_scrollbar(surface, panel, len(lines))

    def toggle(self) -> None:
        """切换规则手册打开状态。"""
        self.is_open = not self.is_open
        if self.is_open:
            self.scroll_line = max(0, min(self._max_scroll(), self.scroll_line))

    def close(self) -> None:
        """关闭规则手册。"""
        self.is_open = False
        self.scroll_line = 0

    def _on_rule_discovered(self, rule_id: str, rule_text: str, **payload) -> None:
        """规则发现后刷新本地展示缓存。"""
        _ = payload
        self.rules[rule_id] = rule_text
        self.scroll_line = max(0, min(self._max_scroll(), self.scroll_line))

    def _rule_lines(self) -> list[str]:
        """格式化规则文本行。"""
        lines = [f"{index}. {text}" for index, text in enumerate(self.rules.values(), start=1)]
        if self.broken_jade_obtained:
            lines.append("残破的玉简似乎蕴含了什么秘密。")
        return lines

    def set_broken_jade_obtained(self, obtained: bool) -> None:
        """同步残破玉简线索是否应出现在 Tab 手册中。"""
        self.broken_jade_obtained = bool(obtained)
        self.scroll_line = max(0, min(self._max_scroll(), self.scroll_line))

    def _visual_lines(self) -> list[str]:
        """把规则预先换成可滚动的视觉行，避免绘制时越过面板。"""
        lines: list[str] = []
        for line in self._rule_lines():
            lines.extend(wrap_text(line, 22))
        return lines

    @staticmethod
    def _visible_line_count() -> int:
        return 8

    def _max_scroll(self, lines: list[str] | None = None) -> int:
        visual_lines = self._visual_lines() if lines is None else lines
        return max(0, len(visual_lines) - self._visible_line_count())

    def _draw_scrollbar(self, surface: pygame.Surface, panel: pygame.Rect, total_lines: int) -> None:
        track = pygame.Rect(panel.right - 22, panel.y + 42, 8, panel.height - 64)
        draw_filled_rect(surface, track, palette.NIGHT_BLACK)
        draw_rect(surface, track.x, track.y, track.width, track.height, palette.WOOD_DARK)
        if total_lines <= self._visible_line_count():
            thumb = track.inflate(-2, -2)
        else:
            thumb_height = max(18, round(track.height * self._visible_line_count() / total_lines))
            travel = track.height - thumb_height - 2
            ratio = self.scroll_line / max(1, self._max_scroll())
            thumb = pygame.Rect(track.x + 2, track.y + 1 + round(travel * ratio), track.width - 4, thumb_height)
        draw_filled_rect(surface, thumb, palette.DARK_BLOOD)

    @staticmethod
    def _key_pressed(input_manager: InputManager, *keys: int) -> bool:
        was_key_pressed = getattr(input_manager, "was_key_pressed", None)
        return bool(was_key_pressed and any(was_key_pressed(key) for key in keys))
