"""死亡画面 UI。"""

from __future__ import annotations

import pygame

import config
from core.event_bus import EventBus, PLAYER_DIED
from core.game_state import GameState
from core.input_manager import InputManager
from utils import palette
from utils.font import render_block_text, render_text


class DeathScreen:
    """违规三次后的死亡画面，支持 R 重启基础状态。"""

    def __init__(self, event_bus: EventBus, game_state: GameState) -> None:
        self.event_bus = event_bus
        self.game_state = game_state
        self.active = False
        self.fade_timer = 0.0
        self.event_bus.subscribe(PLAYER_DIED, self._on_player_died)

    def update(self, dt: float, input_manager: InputManager) -> bool:
        """更新黑屏淡入；按 R 时重置状态并返回 True。"""
        if not self.active:
            return False

        self.fade_timer = min(1.5, self.fade_timer + dt)
        if input_manager.was_pressed("restart"):
            self.active = False
            self.fade_timer = 0.0
            self.game_state.reset_violations()
            return True
        return False

    def draw(self, surface: pygame.Surface) -> None:
        """绘制死亡黑幕和提示文本。"""
        if not self.active:
            return

        alpha = int(220 * min(1.0, self.fade_timer / 1.5))
        overlay = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, alpha))
        surface.blit(overlay, (0, 0))

        if not render_text(surface, "你已陨落于月宫", 172, 112, 20, palette.BLOOD_RED):
            render_block_text(surface, "你已陨落于月宫", 172, 112)
        if not render_text(surface, "按 R 键重新开始", 180, 142, 14, palette.MOON_WHITE):
            render_block_text(surface, "按 R 键重新开始", 180, 142)

    def _on_player_died(self, **payload) -> None:
        """响应死亡事件，打开死亡画面。"""
        _ = payload
        self.active = True
        self.fade_timer = 0.0
