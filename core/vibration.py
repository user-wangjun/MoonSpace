"""可选手柄震动反馈。"""

from __future__ import annotations

from collections.abc import Iterable

import pygame

from core.event_bus import EventBus, PLAYER_DIED, RULE_DISCOVERED, VIOLATION_CHANGED


VIBRATION_RULE_DISCOVERED = "rule_discovered"
VIBRATION_VIOLATION = "violation"
VIBRATION_PLAYER_DIED = "player_died"
VIBRATION_TRANSITION_FOUND = "transition_found"


class VibrationManager:
    """为支持 rumble 的手柄提供可关闭的轻量触觉反馈。"""

    DEFAULT_ENABLED = True
    # low-frequency motor, high-frequency motor, duration in milliseconds
    PATTERNS = {
        VIBRATION_RULE_DISCOVERED: (0.16, 0.30, 100),
        VIBRATION_VIOLATION: (0.45, 0.72, 180),
        VIBRATION_PLAYER_DIED: (0.85, 1.00, 500),
        VIBRATION_TRANSITION_FOUND: (0.32, 0.68, 220),
    }

    def __init__(
        self,
        event_bus: EventBus | None = None,
        *,
        enabled: bool = DEFAULT_ENABLED,
        joysticks: Iterable[object] | None = None,
    ) -> None:
        self.enabled = bool(enabled)
        self._injected_joysticks = joysticks is not None
        self._joysticks = list(joysticks) if joysticks is not None else []
        self.last_event: str | None = None
        self.trigger_count = 0

        if event_bus is not None:
            event_bus.subscribe(RULE_DISCOVERED, self._on_rule_discovered)
            event_bus.subscribe(VIOLATION_CHANGED, self._on_violation_changed)
            event_bus.subscribe(PLAYER_DIED, self._on_player_died)

    def set_enabled(self, enabled: bool) -> None:
        """立即切换震动开关；关闭时停止已经在进行的震动。"""
        self.enabled = bool(enabled)
        if not self.enabled:
            self.stop()

    def status(self) -> dict[str, object]:
        """返回设置和设备状态，供设置菜单及测试使用。"""
        joysticks = self._get_joysticks()
        return {
            "enabled": self.enabled,
            "available": bool(joysticks),
            "device_count": len(joysticks),
        }

    def trigger(self, event: str) -> int:
        """触发一个命名震动；返回实际响应的设备数量。"""
        self.last_event = event
        self.trigger_count += 1
        pattern = self.PATTERNS.get(event)
        if not self.enabled or pattern is None:
            return 0

        low_frequency, high_frequency, duration = pattern
        triggered = 0
        for joystick in self._get_joysticks():
            rumble = getattr(joystick, "rumble", None)
            if not callable(rumble):
                continue
            try:
                result = rumble(low_frequency, high_frequency, duration)
            except (AttributeError, OSError, RuntimeError, TypeError, pygame.error):
                continue
            if result is not False:
                triggered += 1
        return triggered

    def stop(self) -> None:
        """停止已连接手柄上的震动，设备不支持时静默忽略。"""
        for joystick in self._get_joysticks():
            stop_rumble = getattr(joystick, "stop_rumble", None)
            if not callable(stop_rumble):
                continue
            try:
                stop_rumble()
            except (AttributeError, OSError, RuntimeError, TypeError, pygame.error):
                continue

    def _get_joysticks(self) -> list[object]:
        if self._injected_joysticks:
            return self._joysticks

        try:
            if not pygame.joystick.get_init():
                pygame.joystick.init()
            count = pygame.joystick.get_count()
        except pygame.error:
            self._joysticks = []
            return self._joysticks

        detected: list[object] = []
        for index in range(count):
            try:
                joystick = pygame.joystick.Joystick(index)
                if not joystick.get_init():
                    joystick.init()
                detected.append(joystick)
            except (AttributeError, OSError, RuntimeError, pygame.error):
                continue
        self._joysticks = detected
        return self._joysticks

    def _on_rule_discovered(self, **payload) -> None:
        _ = payload
        self.trigger(VIBRATION_RULE_DISCOVERED)

    def _on_violation_changed(self, **payload) -> None:
        try:
            count = int(payload.get("count", 0))
        except (TypeError, ValueError):
            count = 0
        if count > 0:
            self.trigger(VIBRATION_VIOLATION)

    def _on_player_died(self, **payload) -> None:
        _ = payload
        self.trigger(VIBRATION_PLAYER_DIED)
