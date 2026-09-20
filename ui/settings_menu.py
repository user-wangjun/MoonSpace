"""主菜单与游戏内共用的全局设置 UI。"""

from __future__ import annotations

import pygame

import config
from core.audio import AudioManager
from core.input_manager import InputManager
from core.settings_manager import SettingsManager
from core.vibration import VibrationManager
from effects.distortion import DistortionEffect
from utils import palette
from utils.font import load_font, render_text
from utils.pixel_art import draw_double_rect, draw_filled_rect


SETTINGS_BACK = "settings_back"


class SettingsMenu:
    """用统一键盘操作编辑全局 BGM/SFX 音量和震动开关。"""

    VOLUME_STEP = 0.1

    ITEM_COUNT = 6
    VIBRATION_INDEX = 2
    MUTE_INDEX = 3
    DEFAULTS_INDEX = 4
    BACK_INDEX = 5

    def __init__(
        self,
        settings_manager: SettingsManager,
        audio: AudioManager,
        vibration: VibrationManager | None = None,
        distortion: DistortionEffect | None = None,
    ) -> None:
        self.settings_manager = settings_manager
        self.audio = audio
        self.vibration = vibration
        self.distortion = distortion
        self.selected_index = 0
        self.animation_time = 0.0

    def open(self) -> None:
        """打开设置并把磁盘中的值同步到当前音频层。"""
        self.settings_manager.load()
        self._apply_settings()
        self.selected_index = 0
        self.animation_time = 0.0

    def update(self, dt: float, input_manager: InputManager) -> str | None:
        """处理上下选择、左右调节、Enter/E 确认和 Esc 返回。"""
        self.animation_time += max(0.0, dt)
        if input_manager.was_pressed(config.ACTION_QUIT):
            return SETTINGS_BACK

        if input_manager.was_key_pressed(pygame.K_UP) or input_manager.was_key_pressed(pygame.K_w):
            self.selected_index = (self.selected_index - 1) % self.ITEM_COUNT
        elif input_manager.was_key_pressed(pygame.K_DOWN) or input_manager.was_key_pressed(pygame.K_s):
            self.selected_index = (self.selected_index + 1) % self.ITEM_COUNT

        if self.selected_index in (0, 1):
            if input_manager.was_key_pressed(pygame.K_LEFT):
                self._adjust_volume(-self.VOLUME_STEP)
            elif input_manager.was_key_pressed(pygame.K_RIGHT):
                self._adjust_volume(self.VOLUME_STEP)
        elif self.selected_index == self.VIBRATION_INDEX:
            if input_manager.was_key_pressed(pygame.K_LEFT) or input_manager.was_key_pressed(pygame.K_RIGHT):
                self._toggle_vibration()

        if input_manager.was_key_pressed(pygame.K_RETURN) or input_manager.was_pressed(config.ACTION_INTERACT):
            if self.selected_index == self.VIBRATION_INDEX:
                self._toggle_vibration()
            elif self.selected_index == self.MUTE_INDEX:
                self.settings_manager.mute()
                self._apply_settings()
            elif self.selected_index == self.DEFAULTS_INDEX:
                self.settings_manager.restore_defaults()
                self._apply_settings()
            elif self.selected_index == self.BACK_INDEX:
                return SETTINGS_BACK
        return None

    def draw(self, surface: pygame.Surface) -> None:
        """绘制像素风设置面板；背景由 Game 提供主菜单或冻结场景。"""
        shade = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        shade.fill((0, 0, 0, 164))
        surface.blit(shade, (0, 0))

        panel = pygame.Rect(46, 10, 388, 250)
        draw_filled_rect(surface, panel, palette.BLACK)
        draw_double_rect(surface, panel, palette.MOON_WHITE, palette.DARK_BLOOD)
        render_text(surface, "设置", panel.centerx - 18, panel.y + 15, 18, palette.PALE_MOON)
        draw_filled_rect(surface, (panel.x + 18, panel.y + 46, panel.width - 36, 1), palette.DEEP_BLUE)

        rows = (
            ("BGM 音量", f"{round(self.settings_manager.values['bgm_volume'] * 100):3d}%"),
            ("音效音量", f"{round(self.settings_manager.values['sfx_volume'] * 100):3d}%"),
            ("震动", "开启" if self.settings_manager.values.get("vibration_enabled", True) else "关闭"),
            ("全部静音", "已静音" if self._is_muted else "按 Enter 静音"),
            ("恢复默认", "BGM / 音效 100% / 震动开启"),
            ("返回", ""),
        )
        font = load_font(13)
        for index, (label, value) in enumerate(rows):
            y = panel.y + 58 + index * 26
            selected = index == self.selected_index
            color = palette.PALE_MOON if selected else palette.MOON_WHITE
            if selected and int(self.animation_time * 4) % 2 == 0:
                draw_filled_rect(surface, (panel.x + 22, y + 6, 8, 3), palette.BLOOD_RED)
            render_text(surface, label, panel.x + 38, y, 13, color)
            if value:
                value_width, _ = font.size(value)
                render_text(surface, value, panel.right - 32 - value_width, y, 13, palette.ASH_GRAY)

        render_text(surface, "←→ 调整音量/震动    ↑↓ 选择    Enter / E 确认", 74, 228, 10, palette.ASH_GRAY)
        render_text(surface, "Esc 返回", 202, 242, 10, palette.ASH_GRAY)

    @property
    def _is_muted(self) -> bool:
        return (
            self.settings_manager.values.get("bgm_volume", 1.0) <= 0.0
            and self.settings_manager.values.get("sfx_volume", 1.0) <= 0.0
        )

    def _adjust_volume(self, delta: float) -> None:
        key = "bgm_volume" if self.selected_index == 0 else "sfx_volume"
        current = self.settings_manager.values.get(key, 1.0)
        self.settings_manager.set_volume(key, round(current + delta, 2))
        self._apply_settings()

    def _toggle_vibration(self) -> None:
        enabled = not bool(self.settings_manager.values.get("vibration_enabled", True))
        self.settings_manager.set_vibration_enabled(enabled)
        self._apply_settings()

    def _apply_settings(self) -> None:
        self.audio.set_volume_preferences(
            bgm_volume=self.settings_manager.values.get("bgm_volume", 1.0),
            sfx_volume=self.settings_manager.values.get("sfx_volume", 1.0),
        )
        if self.vibration is not None:
            self.vibration.set_enabled(bool(self.settings_manager.values.get("vibration_enabled", True)))
        if self.distortion is not None:
            self.distortion.set_shake_enabled(
                bool(self.settings_manager.values.get("vibration_enabled", True))
            )
