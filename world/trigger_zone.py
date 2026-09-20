"""规则触发区域。"""

from __future__ import annotations

import pygame


class TriggerZone:
    """矩形触发区，支持进入、停留和冷却控制。"""

    def __init__(
        self,
        rect: pygame.Rect | tuple[int, int, int, int],
        rule_id: str,
        trigger_type: str = "enter",
        cooldown: float = 1.0,
        required_stay: float = 0.0,
    ) -> None:
        self.rect = pygame.Rect(rect)
        self.rule_id = rule_id
        self.trigger_type = trigger_type
        self.cooldown = cooldown
        self.required_stay = required_stay
        self._was_inside = False
        self._cooldown_remaining = 0.0
        self._stay_time = 0.0

    def update(self, dt: float, target_rect: pygame.Rect) -> bool:
        """更新触发区状态；达到触发条件时返回 True。"""
        self._cooldown_remaining = max(0.0, self._cooldown_remaining - dt)
        inside = self.rect.colliderect(target_rect)
        triggered = False

        if inside:
            self._stay_time += dt
        else:
            self._stay_time = 0.0

        if self._cooldown_remaining <= 0.0:
            if self.trigger_type == "enter":
                triggered = inside and not self._was_inside
            elif self.trigger_type == "stay":
                triggered = inside and self._stay_time >= self.required_stay
            elif self.trigger_type == "inside":
                triggered = inside

        if triggered:
            self._cooldown_remaining = self.cooldown
            if self.trigger_type == "stay":
                self._stay_time = 0.0

        self._was_inside = inside
        return triggered

    def reset(self) -> None:
        """重置触发区内部状态，用于重开游戏。"""
        self._was_inside = False
        self._cooldown_remaining = 0.0
        self._stay_time = 0.0

    @property
    def stay_progress(self) -> float:
        """连续停留进度，供环境预兆使用，不额外推进规则计时。"""
        if self.required_stay <= 0:
            return 0.0
        return min(1.0, self._stay_time / self.required_stay)


class CircularTriggerZone(TriggerZone):
    """圆形触发区；用目标矩形到圆心的最近点判断相交。"""

    def __init__(
        self,
        center: tuple[int, int],
        radius: int,
        rule_id: str,
        trigger_type: str = "enter",
        cooldown: float = 1.0,
        required_stay: float = 0.0,
    ) -> None:
        self.center = (int(center[0]), int(center[1]))
        self.radius = int(radius)
        bounds = pygame.Rect(0, 0, self.radius * 2, self.radius * 2)
        bounds.center = self.center
        super().__init__(bounds, rule_id, trigger_type, cooldown, required_stay)

    def update(self, dt: float, target_rect: pygame.Rect) -> bool:
        closest_x = max(target_rect.left, min(self.center[0], target_rect.right))
        closest_y = max(target_rect.top, min(self.center[1], target_rect.bottom))
        dx = closest_x - self.center[0]
        dy = closest_y - self.center[1]
        intersects = dx * dx + dy * dy <= self.radius * self.radius
        proxy = pygame.Rect(self.center[0], self.center[1], 1, 1) if intersects else pygame.Rect(-9999, -9999, 1, 1)
        return super().update(dt, proxy)
