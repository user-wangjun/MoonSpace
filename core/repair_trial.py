"""Transient, deterministic sixty-second moon-fragment examination."""

from __future__ import annotations

import math


class RepairTrial:
    DURATION = 60.0
    SEAL_DURATION = 5.5
    DEATH_DURATION = 2.2
    CRACKED_PIECE = 2
    DRAG_DEGREES_PER_PIXEL = 0.65
    LIGHT_YAW = 34.0
    LIGHT_PITCH = 20.0
    REVEAL_ALIGNMENT = 0.965

    def __init__(self, completed: bool = False) -> None:
        self.phase = "complete" if completed else "idle"
        self.remaining = self.DURATION
        self.elapsed = 0.0
        self.selected: int | None = None
        self.yaw = 0.0
        self.pitch = 0.0
        self.spin_yaw = 0.0
        self.spin_pitch = 0.0
        self.dragging = False
        self.inspecting = False
        self.in_light = False
        self.crack_revealed = False
        self.death_reason = ""

    def brief(self) -> None:
        if self.phase == "idle":
            self.phase = "briefing"

    def start(self) -> None:
        if self.phase == "briefing":
            self.phase = "active"
            self.remaining = self.DURATION

    def pick_up(self, index: int) -> None:
        if self.phase == "active" and index in (0, 1, 2):
            self.selected = index
            self.set_orientation(0.0, 0.0)
            self.spin_yaw = self.spin_pitch = 0.0
            self.dragging = False
            self.crack_revealed = False

    def put_back(self) -> None:
        if self.phase == "active":
            self.selected = None
            self.inspecting = False
            self.in_light = False
            self.dragging = False
            self.spin_yaw = self.spin_pitch = 0.0
            self.crack_revealed = False

    def rotate(self, direction: int) -> None:
        """Legacy programmatic rotation; gameplay uses free mouse dragging."""
        if self.phase == "active" and self.selected is not None:
            self.set_orientation(self.yaw + direction * 45.0, self.pitch)

    def flip(self) -> None:
        """Legacy programmatic flip; gameplay uses free mouse dragging."""
        if self.phase == "active" and self.selected is not None:
            self.set_orientation(self.yaw + 180.0, self.pitch)

    @staticmethod
    def _normal_for(yaw: float, pitch: float) -> tuple[float, float, float]:
        yaw_radians = math.radians(yaw)
        pitch_radians = math.radians(pitch)
        cos_pitch = math.cos(pitch_radians)
        return (
            math.sin(yaw_radians) * cos_pitch,
            -math.sin(pitch_radians),
            math.cos(yaw_radians) * cos_pitch,
        )

    @staticmethod
    def _wrap_degrees(value: float) -> float:
        return (value + 180.0) % 360.0 - 180.0

    def set_orientation(self, yaw: float, pitch: float) -> None:
        self.yaw = self._wrap_degrees(yaw)
        self.pitch = self._wrap_degrees(pitch)

    @property
    def normal(self) -> tuple[float, float, float]:
        return self._normal_for(self.yaw, self.pitch)

    @property
    def back(self) -> bool:
        return self.normal[2] < 0.0

    @property
    def angle(self) -> int:
        """Quantized yaw retained for static previews and old save-free callers."""
        return round(self.yaw / 45.0) % 8

    @property
    def light_alignment(self) -> float:
        normal = self.normal
        light = self._normal_for(self.LIGHT_YAW, self.LIGHT_PITCH)
        return sum(component * light_component for component, light_component in zip(normal, light))

    @property
    def reveal_strength(self) -> float:
        if not self.in_light:
            return 0.0
        return max(0.0, min(1.0, (self.light_alignment - 0.92) / 0.075))

    def begin_rotation(self) -> None:
        if self.phase == "active" and self.selected is not None and self.inspecting:
            self.dragging = True
            self.spin_yaw = self.spin_pitch = 0.0

    def drag_rotation(self, dx: float, dy: float) -> None:
        if not self.dragging:
            return
        yaw_delta = dx * self.DRAG_DEGREES_PER_PIXEL
        pitch_delta = dy * self.DRAG_DEGREES_PER_PIXEL
        self.set_orientation(self.yaw + yaw_delta, self.pitch + pitch_delta)
        self.spin_yaw = max(-90.0, min(90.0, dx * 1.5))
        self.spin_pitch = max(-90.0, min(90.0, dy * 1.5))

    def end_rotation(self) -> None:
        self.dragging = False

    @property
    def resonating(self) -> bool:
        return bool(self.phase == "active" and self.selected == self.CRACKED_PIECE
                    and self.in_light and self.light_alignment >= self.REVEAL_ALIGNMENT)

    def record_observation(self) -> bool:
        """Remember that the player actually exposed the internal crack."""
        if self.resonating:
            self.crack_revealed = True
        return self.crack_revealed

    def submit(self) -> str | None:
        if self.phase != "active" or self.selected is None:
            return None
        self.inspecting = False
        if self.remaining <= 0:
            self.kill("超时")
        elif self.selected != self.CRACKED_PIECE:
            self.kill("错片")
        elif not self.crack_revealed:
            self.kill("未验")
        else:
            self.phase = "sealing"
            self.elapsed = 0.0
        return self.phase

    def kill(self, reason: str) -> None:
        if self.phase != "active":
            return
        self.phase = "death"
        self.death_reason = reason
        self.elapsed = 0.0
        self.inspecting = False
        self.dragging = False
        self.spin_yaw = self.spin_pitch = 0.0

    def tick(self, dt: float) -> str | None:
        dt = max(0.0, dt)
        if self.phase == "active":
            if self.inspecting and not self.dragging:
                self.set_orientation(
                    self.yaw + self.spin_yaw * dt,
                    self.pitch + self.spin_pitch * dt,
                )
                damping = math.exp(-8.0 * dt)
                self.spin_yaw *= damping
                self.spin_pitch *= damping
            self.remaining = max(0.0, self.remaining - dt)
            if self.remaining <= 0:
                self.kill("超时")
                return "death"
        elif self.phase in ("sealing", "death"):
            self.elapsed += dt
            if self.phase == "sealing" and self.elapsed >= self.SEAL_DURATION:
                self.phase = "complete"
                self.selected = None
                return "completed"
            if self.phase == "death" and self.elapsed >= self.DEATH_DURATION:
                return "restore"
        return None
