"""世界扭曲与违规反馈特效。"""

from __future__ import annotations

import math
import random

import pygame

import config
from core.event_bus import EventBus, PLAYER_DIED, RULE_DISCOVERED, TREE_BLEEDING, VIOLATION_CHANGED
from utils import palette


class DistortionEffect:
    """监听违规事件，提供屏幕震动、红色闪烁和恐怖色调覆盖。"""

    HORROR_BY_COUNT = {1: 0.15, 2: 0.4, 3: 0.8}

    def __init__(self, event_bus: EventBus, *, shake_enabled: bool = True) -> None:
        self.event_bus = event_bus
        self.shake_intensity = 0.0
        self.shake_duration = 0.0
        self.shake_timer = 0.0
        self.shake_enabled = bool(shake_enabled)
        self.horror_intensity = 0.0
        self.flash_timer = 0.0
        self.blood_pulse_timer = 0.0
        self.camera_offset = pygame.Vector2(0, 0)
        self._rng = random.Random(20260630)
        self.event_bus.subscribe(RULE_DISCOVERED, self._on_rule_discovered)
        self.event_bus.subscribe(VIOLATION_CHANGED, self._on_violation_changed)
        self.event_bus.subscribe(PLAYER_DIED, self._on_player_died)
        self.event_bus.subscribe(TREE_BLEEDING, self._on_tree_bleeding)

    def update(self, dt: float) -> None:
        """更新震动偏移和覆盖层计时。"""
        self.flash_timer = max(0.0, self.flash_timer - dt)
        self.blood_pulse_timer = max(0.0, self.blood_pulse_timer - dt)

        if self.shake_timer > 0:
            self.shake_timer = max(0.0, self.shake_timer - dt)
            ratio = self.shake_timer / max(self.shake_duration, 0.001)
            amplitude = self.shake_intensity * ratio
            self.camera_offset.update(
                self._rng.uniform(-amplitude, amplitude),
                self._rng.uniform(-amplitude, amplitude),
            )
        else:
            self.camera_offset.update(0, 0)

    def draw_overlay(self, surface: pygame.Surface) -> None:
        """绘制恐怖态色调、违规红闪和流血脉冲。"""
        if self.horror_intensity > 0:
            alpha = int(90 * min(1.0, self.horror_intensity))
            overlay = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((*palette.HORROR_CYAN_GRAY, alpha))
            surface.blit(overlay, (0, 0))

        if self.flash_timer > 0:
            alpha = int(150 * min(1.0, self.flash_timer / 0.35))
            overlay = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((*palette.BLOOD_RED, alpha))
            surface.blit(overlay, (0, 0))

        if self.blood_pulse_timer > 0:
            pulse = (math.sin(self.blood_pulse_timer * 12) + 1) / 2
            alpha = int(14 + 22 * pulse)
            overlay = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((*palette.DARK_BLOOD, alpha))
            surface.blit(overlay, (0, 0))

    def start_shake(self, intensity: float, duration: float) -> None:
        """启动屏幕震动。"""
        if not self.shake_enabled:
            return
        self.shake_intensity = intensity
        self.shake_duration = duration
        self.shake_timer = duration

    def set_shake_enabled(self, enabled: bool) -> None:
        """切换电脑端画面抖动开关，不影响红闪和恐怖色调。"""
        self.shake_enabled = bool(enabled)
        if not self.shake_enabled:
            self.shake_intensity = 0.0
            self.shake_duration = 0.0
            self.shake_timer = 0.0
            self.camera_offset.update(0, 0)

    def reset(self) -> None:
        """重置所有特效状态，用于死亡后重新开始。"""
        self.shake_intensity = 0.0
        self.shake_duration = 0.0
        self.shake_timer = 0.0
        self.horror_intensity = 0.0
        self.flash_timer = 0.0
        self.blood_pulse_timer = 0.0
        self.camera_offset.update(0, 0)

    def restore_violation_count(self, count: int) -> None:
        """按存档中的违规次数恢复常驻恐怖强度，不重播受击反馈。"""
        self.reset()
        self.horror_intensity = self.HORROR_BY_COUNT.get(count, 0.0)

    def _on_violation_changed(self, count: int, **payload) -> None:
        """违规次数变化时提升反馈强度。"""
        _ = payload
        if count <= 0:
            return
        intensity_by_count = {1: 2.0, 2: 4.0, 3: 7.0}
        self.start_shake(intensity_by_count.get(count, 3.0), 0.45)
        self.horror_intensity = max(self.horror_intensity, self.HORROR_BY_COUNT.get(count, 0.2))
        self.flash_timer = 0.35

    def _on_rule_discovered(self, **payload) -> None:
        """发现新规条时给出轻微、短促的画面反馈。"""
        _ = payload
        self.start_shake(1.5, 0.14)

    def _on_player_died(self, **payload) -> None:
        """死亡时给出较强的画面反馈。"""
        _ = payload
        self.start_shake(8.0, 0.55)

    def _on_tree_bleeding(self, **payload) -> None:
        """月桂流血时触发血色脉冲。"""
        _ = payload
        self.blood_pulse_timer = 1.2
        self.start_shake(3.0, 0.6)
