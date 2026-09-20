"""MoonSpace scene transition screen."""

from __future__ import annotations

import math
from collections.abc import Callable

import pygame

import config
from utils import palette
from utils.assets import load_image, load_sprite_grid
from utils.font import load_font, render_text
from utils.pixel_art import draw_double_rect, draw_filled_rect, draw_line, draw_rect


class SceneTransition:
    """Screen-only transition with a 5.2-second push and head-turn reveal."""

    # Match the locked K00-K12 storyboard: searching has room to breathe,
    # the neck turn stays abrupt, and the final face gets a readable hold.
    SEARCH_DURATION = 3.00
    REVEAL_DURATION = 0.80
    FINAL_HOLD_DURATION = 1.40
    TOTAL_DURATION = SEARCH_DURATION + REVEAL_DURATION + FINAL_HOLD_DURATION
    # Keep the older public names available to callers that use the transition
    # as a loading gate. LOAD_DURATION now means the complete timeline, while
    # REVEAL_HOLD remains the final-face hold duration.
    LOAD_DURATION = TOTAL_DURATION
    REVEAL_HOLD = FINAL_HOLD_DURATION
    FOUND_PROGRESS = SEARCH_DURATION / TOTAL_DURATION
    SEARCH_FRAME_INDEX = 0
    SEARCH_FRAME_START = SEARCH_FRAME_INDEX
    SEARCH_FRAME_END = 11
    SEARCH_START_ZOOM = 1.0
    SEARCH_END_ZOOM = 1.12
    REVEAL_FRAME_START = 12
    REVEAL_FRAME_END = 23
    REVEAL_MAX_ZOOM = 1.52
    MONITOR_SCREEN_RECT = pygame.Rect(115, 30, 251, 161)
    MONITOR_FRAME_RECT = pygame.Rect(115, 48, 251, 126)
    MONITOR_SOURCE_CROP = pygame.Rect(22, 2, 318, 177)
    MONITOR_SHEET_PATH = "sprites/moonspace/sheets/scene_transition_monitor_head_only_v2.png"
    MONITOR_FRAME_SIZE = (362, 181)
    MONITOR_GRID_SIZE = (6, 4)
    MONITOR_FRAME_COUNT = 24

    def __init__(self) -> None:
        self.active = False
        self.progress = 0.0
        self.caption = ""
        self.found_message = "找到你了！"
        self.reveal_started = False
        self.search_offset = 0
        self._elapsed = 0.0
        self._reveal_elapsed = 0.0
        self._final_hold_elapsed = 0.0
        self._on_complete: Callable[[], None] | None = None
        self._on_found: Callable[[], None] | None = None
        self._found_called = False
        self._completed = False

    def start(
        self,
        on_complete: Callable[[], None],
        caption: str = "月门正在核验来使身份",
        on_found: Callable[[], None] | None = None,
    ) -> None:
        """Start a loading transition and run callback after the reveal hold."""
        self.active = True
        self.progress = 0.0
        self.caption = caption
        self.reveal_started = False
        self.search_offset = 0
        self._elapsed = 0.0
        self._reveal_elapsed = 0.0
        self._final_hold_elapsed = 0.0
        self._on_complete = on_complete
        self._on_found = on_found
        self._found_called = False
        self._completed = False

    def update(self, dt: float) -> None:
        """Advance the search, head turn, and final-face hold timeline."""
        if not self.active:
            return

        remaining = max(0.0, float(dt))
        if remaining <= 0.0:
            return

        # Consume a large dt across phase boundaries as well. This keeps the
        # transition duration correct in tests and when a frame is delayed.
        while remaining > 0.0:
            if not self.reveal_started:
                phase_remaining = max(0.0, self.SEARCH_DURATION - self._elapsed)
                step = min(remaining, phase_remaining)
                self._elapsed += step
                self.progress = min(1.0, self._elapsed / self.TOTAL_DURATION)
                self.search_offset = int(round(3 * math.sin(self._elapsed * 15.0)))
                remaining -= step
                if self._elapsed + 1e-9 < self.SEARCH_DURATION:
                    return

                self._elapsed = self.SEARCH_DURATION
                self.progress = self.FOUND_PROGRESS
                self.reveal_started = True
                self._call_found_once()
                if remaining <= 0.0:
                    return

            if self._reveal_elapsed < self.REVEAL_DURATION:
                phase_remaining = self.REVEAL_DURATION - self._reveal_elapsed
                step = min(remaining, phase_remaining)
                self._reveal_elapsed += step
                self._elapsed = self.SEARCH_DURATION + self._reveal_elapsed
                self.progress = min(1.0, self._elapsed / self.TOTAL_DURATION)
                remaining -= step
                if self._reveal_elapsed + 1e-9 < self.REVEAL_DURATION:
                    return
                if remaining <= 0.0:
                    return

            if self._final_hold_elapsed < self.FINAL_HOLD_DURATION:
                phase_remaining = self.FINAL_HOLD_DURATION - self._final_hold_elapsed
                step = min(remaining, phase_remaining)
                self._final_hold_elapsed += step
                self._elapsed = self.SEARCH_DURATION + self.REVEAL_DURATION + self._final_hold_elapsed
                self.progress = min(1.0, self._elapsed / self.TOTAL_DURATION)
                remaining -= step
                if self._final_hold_elapsed + 1e-9 < self.FINAL_HOLD_DURATION:
                    return

            self.active = False
            if not self._completed and self._on_complete is not None:
                self._completed = True
                self._on_complete()
            return

    def _call_found_once(self) -> None:
        if self._found_called:
            return
        self._found_called = True
        if self._on_found is not None:
            self._on_found()

    def draw(self, surface: pygame.Surface) -> None:
        """Draw the red-moon monitor image, progress crack, and final stare."""
        try:
            background = load_image("sprites/moonspace/scene_transition_screen.png")
        except (FileNotFoundError, pygame.error):
            background = None

        if background is not None:
            surface.blit(background, (0, 0))
        else:
            self._draw_fallback_background(surface)

        monitor_sequence_drawn = self._draw_monitor_sequence(surface)
        self._draw_scanlines(surface)
        self._draw_progress(surface)
        if monitor_sequence_drawn and self._monitor_frame_index() >= self.REVEAL_FRAME_END - 1:
            self._draw_found_message(surface)
        elif not monitor_sequence_drawn:
            if self.reveal_started:
                self._draw_found_you(surface)
            else:
                self._draw_searching_shadow(surface)

    def _draw_monitor_sequence(self, surface: pygame.Surface) -> bool:
        """在电视屏幕内播放用户确认的 24 帧寻找转场。"""
        try:
            rows, cols = self.MONITOR_GRID_SIZE
            frame_width, frame_height = self.MONITOR_FRAME_SIZE
            grid = load_sprite_grid(self.MONITOR_SHEET_PATH, frame_width, frame_height, rows, cols)
        except (FileNotFoundError, ValueError, pygame.error):
            return False

        frames = [frame for row in grid for frame in row]
        frame = frames[self._monitor_frame_index()]
        frame = frame.subsurface(self.MONITOR_SOURCE_CROP).copy()
        zoom = self._monitor_zoom()
        target_size = (
            max(1, round(self.MONITOR_FRAME_RECT.width * zoom)),
            max(1, round(self.MONITOR_FRAME_RECT.height * zoom)),
        )
        frame = pygame.transform.smoothscale(frame, target_size)
        draw_filled_rect(surface, self.MONITOR_SCREEN_RECT, palette.BLACK)
        previous_clip = surface.get_clip()
        surface.set_clip(self.MONITOR_SCREEN_RECT)
        # Keep the scene and body anchor fixed. Head movement comes from the
        # authored atlas frames, not from translating the whole screen.
        frame_center = self.MONITOR_FRAME_RECT.center
        surface.blit(frame, frame.get_rect(center=frame_center))
        surface.set_clip(previous_clip)
        return True

    def _monitor_zoom(self) -> float:
        """Return the continuous slow push plus the final face-rush scale."""
        if not self.reveal_started:
            search_progress = min(1.0, self.progress / max(self.FOUND_PROGRESS, 0.001))
            return self.SEARCH_START_ZOOM + (
                self.SEARCH_END_ZOOM - self.SEARCH_START_ZOOM
            ) * search_progress
        reveal_progress = min(1.0, self._reveal_elapsed / max(self.REVEAL_DURATION, 0.001))
        # Keep the slow-push endpoint through the first reveal tick, then rush
        # toward the close-up as the head completes its turn.
        zoom_progress = reveal_progress**0.55
        return self.SEARCH_END_ZOOM + (
            self.REVEAL_MAX_ZOOM - self.SEARCH_END_ZOOM
        ) * zoom_progress

    def _monitor_frame_index(self) -> int:
        """Map authored search frames into the final turn-and-reveal sequence."""
        if not self.reveal_started:
            search_progress = min(1.0, self.progress / max(self.FOUND_PROGRESS, 0.001))
            search_span = self.SEARCH_FRAME_END - self.SEARCH_FRAME_START + 1
            return min(
                self.SEARCH_FRAME_END,
                self.SEARCH_FRAME_START + int(search_progress * search_span),
            )

        reveal_progress = min(1.0, self._reveal_elapsed / max(self.REVEAL_DURATION, 0.001))
        reveal_span = self.REVEAL_FRAME_END - self.REVEAL_FRAME_START + 1
        return min(
            self.REVEAL_FRAME_END,
            self.REVEAL_FRAME_START + int(reveal_progress * reveal_span),
        )

    def _draw_fallback_background(self, surface: pygame.Surface) -> None:
        surface.fill(palette.BLACK)
        monitor = pygame.Rect(62, 28, 356, 188)
        draw_filled_rect(surface, monitor, palette.DEEP_BLUE)
        draw_double_rect(surface, monitor, palette.ASH_GRAY, palette.BLACK)
        pygame.draw.circle(surface, palette.BLOOD_RED, monitor.center, 56)
        draw_filled_rect(surface, (monitor.centerx - 8, monitor.centery + 22, 16, 42), palette.BLACK)

    def _draw_scanlines(self, surface: pygame.Surface) -> None:
        overlay = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT), pygame.SRCALPHA)
        for y in range(0, config.SCREEN_HEIGHT, 4):
            draw_filled_rect(overlay, (0, y, config.SCREEN_WIDTH, 1), (*palette.BLACK, 45))
        surface.blit(overlay, (0, 0))

    def _draw_progress(self, surface: pygame.Surface) -> None:
        panel = pygame.Rect(62, config.SCREEN_HEIGHT - 42, 356, 22)
        draw_filled_rect(surface, panel, palette.BLACK)
        draw_double_rect(surface, panel, palette.MOON_WHITE, palette.DARK_BLOOD)
        inner = pygame.Rect(panel.x + 8, panel.y + 9, panel.width - 16, 4)
        draw_rect(surface, inner.x, inner.y, inner.width, inner.height, palette.DEEP_BLUE)
        fill_width = int(inner.width * self.progress)
        if fill_width > 0:
            draw_filled_rect(surface, (inner.x, inner.y, fill_width, inner.height), palette.BLOOD_RED)
            for x in range(inner.x, inner.x + fill_width, 18):
                draw_line(surface, (x, inner.y + 3), (min(x + 9, inner.x + fill_width), inner.y), palette.PALE_MOON)

        render_text(surface, self.caption, panel.x + 12, panel.y - 16, 11, palette.PALE_MOON)

    def _draw_found_message(self, surface: pygame.Surface) -> None:
        """Cover any atlas lettering and render the exact final title."""
        band = pygame.Rect(
            self.MONITOR_SCREEN_RECT.x,
            self.MONITOR_SCREEN_RECT.bottom - 44,
            self.MONITOR_SCREEN_RECT.width,
            44,
        )
        overlay = pygame.Surface(band.size, pygame.SRCALPHA)
        overlay.fill((*palette.BLACK, 255))
        surface.blit(overlay, band.topleft)

        font = load_font(18)
        text_width, text_height = font.size(self.found_message)
        x = band.centerx - text_width // 2
        y = band.centery - text_height // 2
        render_text(surface, self.found_message, x, y, 18, palette.BLOOD_RED)

    def _draw_searching_shadow(self, surface: pygame.Surface) -> None:
        """Before 98%, keep the fallback body fixed while the head searches."""
        cx, cy = config.SCREEN_WIDTH // 2, config.SCREEN_HEIGHT // 2 + 2
        head_offset = int(round(self.search_offset * 0.5))
        draw_filled_rect(surface, (cx - 8 + head_offset, cy - 17, 16, 11), palette.BLACK)
        draw_filled_rect(surface, (cx - 10 + head_offset, cy - 20, 8, 2), palette.DEEP_BLUE)
        draw_filled_rect(surface, (cx + 4 + head_offset, cy - 19, 7, 2), palette.DEEP_BLUE)
        draw_line(surface, (cx - 13, cy - 4), (cx + 13, cy - 4), palette.DARK_BLOOD)

    def _draw_found_you(self, surface: pygame.Surface) -> None:
        """At 98%, make the figure snap its neck around and announce it found you."""
        cx, cy = config.SCREEN_WIDTH // 2, config.SCREEN_HEIGHT // 2 + 2
        veil = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT), pygame.SRCALPHA)
        veil.fill((*palette.DARK_BLOOD, 48))
        surface.blit(veil, (0, 0))
        draw_filled_rect(surface, (cx - 14, cy - 18, 28, 24), palette.BLACK)
        draw_filled_rect(surface, (cx - 9, cy - 10, 5, 2), palette.BLOOD_RED)
        draw_filled_rect(surface, (cx + 4, cy - 10, 5, 2), palette.BLOOD_RED)
        draw_line(surface, (cx - 10, cy - 2), (cx + 10, cy - 2), palette.DARK_BLOOD)
        draw_filled_rect(surface, (cx - 18, cy + 5, 36, 52), palette.BLACK)

        draw_filled_rect(surface, (cx - 27, cy + 19, 54, 2), palette.BLOOD_RED)
        draw_filled_rect(surface, (cx - 2, cy + 20, 4, 14), palette.DARK_BLOOD)
        render_text(surface, self.found_message, cx - 36, config.SCREEN_HEIGHT - 68, 18, palette.BLOOD_RED)
