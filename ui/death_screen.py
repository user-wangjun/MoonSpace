"""死亡画面 UI。"""

from __future__ import annotations

import pygame

import config
from core.event_bus import EventBus, PLAYER_DIED
from core.game_state import GameState
from core.input_manager import InputManager
from utils import palette
from utils.assets import load_image
from utils.font import render_block_text, render_text


class DeathScreen:
    """违规三次后的死亡画面，支持 R 重启基础状态。"""

    SHOT_ASSETS = (
        "sprites/moonspace/cg/death_violation_01_reflection.png",
        "sprites/moonspace/cg/death_violation_02_pool_spreads.png",
        "sprites/moonspace/cg/death_violation_03_pool_pull.png",
    )
    SHOT_DURATION = 1.2
    BLACKOUT_START = 2.4
    BLACKOUT_MAX_AT = 4.0
    BLACKOUT_ALPHA = 220
    # Kept as a compatibility name for callers that used the old fade timer.
    FADE_DURATION = BLACKOUT_MAX_AT
    AUDIO_CUES = ((0.0, "cg_moon_pool"), (2.4, "cg_laurel_roots"))

    def __init__(self, event_bus: EventBus, game_state: GameState, audio=None) -> None:
        self.event_bus = event_bus
        self.game_state = game_state
        self.audio = audio
        self.active = False
        self.fade_timer = 0.0
        self._audio_tokens: set[str] = set()
        self.event_bus.subscribe(PLAYER_DIED, self._on_player_died)

    def update(self, dt: float, input_manager: InputManager) -> bool:
        """更新黑屏淡入；按 R 时重置状态并返回 True。"""
        if not self.active:
            return False

        if input_manager.was_pressed(config.ACTION_RESTART):
            self._reset_sequence()
            self.game_state.reset_violations()
            return True

        self.fade_timer = min(self.FADE_DURATION, self.fade_timer + max(0.0, dt))
        self._emit_audio_cues()
        return False

    def draw(self, surface: pygame.Surface) -> None:
        """绘制死亡黑幕和提示文本。"""
        if not self.active:
            return

        surface.fill(palette.BLACK)
        self._draw_shot_asset(surface)

        alpha = self.blackout_alpha
        if alpha:
            overlay = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, alpha))
            surface.blit(overlay, (0, 0))

        if self.show_messages:
            if not render_text(surface, "你已陨落于月宫", 172, 112, 20, palette.BLOOD_RED):
                render_block_text(surface, "你已陨落于月宫", 172, 112)
            if not render_text(surface, "按 R 返回最近存档点", 180, 142, 14, palette.MOON_WHITE):
                render_block_text(surface, "按 R 返回最近存档点", 180, 142)

    def _draw_shot_asset(self, surface: pygame.Surface) -> bool:
        """按独立镜头时钟切换三镜；缺图时以黑底安全降级。"""
        shot_index = self.current_shot_index(self.fade_timer)
        background = None
        # A missing single frame should not crash or blank the whole UI. Prefer
        # a neighbouring formal frame, while keeping the active sequence alive.
        candidates = [shot_index]
        candidates.extend(index for index in range(shot_index - 1, -1, -1))
        candidates.extend(index for index in range(shot_index + 1, len(self.SHOT_ASSETS)))
        for index in candidates:
            try:
                background = load_image(self.SHOT_ASSETS[index])
                break
            except (FileNotFoundError, pygame.error):
                continue
        if background is None:
            return False
        if background.get_size() != surface.get_size():
            background = pygame.transform.smoothscale(background, surface.get_size())
        surface.blit(background, (0, 0))
        return True

    @classmethod
    def current_shot_index(cls, timer: float) -> int:
        """Return D1/D2/D3 for a sequence timestamp."""
        return min(len(cls.SHOT_ASSETS) - 1, max(0, int(max(0.0, timer) / cls.SHOT_DURATION)))

    @property
    def show_messages(self) -> bool:
        """Death copy is withheld until the persistent D3 frame."""
        return self.fade_timer >= self.BLACKOUT_START

    @property
    def blackout_alpha(self) -> int:
        """Fade only after D3 begins, reaching the existing maximum at 4 s."""
        if self.fade_timer <= self.BLACKOUT_START:
            return 0
        progress = (self.fade_timer - self.BLACKOUT_START) / (self.BLACKOUT_MAX_AT - self.BLACKOUT_START)
        return int(self.BLACKOUT_ALPHA * min(1.0, max(0.0, progress)))

    def _emit_audio_cues(self) -> None:
        if self.audio is None:
            return
        for boundary, key in self.AUDIO_CUES:
            if self.fade_timer >= boundary:
                token = f"death:{boundary}:{key}"
                if token in self._audio_tokens:
                    continue
                self._audio_tokens.add(token)
                self.audio.play_cg_cue(key, token=token)

    def _reset_sequence(self) -> None:
        self.active = False
        self.fade_timer = 0.0
        self._audio_tokens.clear()
        if self.audio is not None:
            self.audio.stop_cg_sounds()

    def _on_player_died(self, **payload) -> None:
        """响应死亡事件，打开死亡画面。"""
        _ = payload
        if self.audio is not None:
            self.audio.begin_cg_cycle()
        self.active = True
        self.fade_timer = 0.0
        self._audio_tokens.clear()
        self._emit_audio_cues()
