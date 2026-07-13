"""MoonSpace scene transition screen."""

from __future__ import annotations

import math
from collections.abc import Callable

import pygame

import config
from utils import palette
from utils.assets import load_image, load_sprite_grid
from utils.font import render_text
from utils.pixel_art import draw_double_rect, draw_filled_rect, draw_line, draw_rect


class SceneTransition:
    """Moon Palace loading transition with a reveal pause before changing scenes."""

    LOAD_DURATION = 1.45
    REVEAL_HOLD = 0.65
    FOUND_PROGRESS = 0.98
    MONITOR_SCREEN_RECT = pygame.Rect(115, 30, 251, 161)
    MONITOR_FRAME_RECT = pygame.Rect(115, 48, 251, 126)
    MONITOR_SOURCE_CROP = pygame.Rect(22, 2, 318, 177)
    MONITOR_SHEET_PATH = "sprites/moonspace/sheets/scene_transition_monitor_24frames.png"
    MONITOR_FRAME_SIZE = (362, 181)
    MONITOR_GRID_SIZE = (6, 4)
    MONITOR_FRAME_COUNT = 24

    def __init__(self) -> None:
        self.active = False
        self.progress = 0.0
        self.caption = ""
        self.found_message = "找到你了"
        self.reveal_started = False
        self.search_offset = 0
        self._elapsed = 0.0
        self._reveal_elapsed = 0.0
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
        self._on_complete = on_complete
        self._on_found = on_found
        self._found_called = False
        self._completed = False

    def update(self, dt: float) -> None:
        """Advance loading progress, then hold on the screen-facing reveal."""
        if not self.active:
            return

        if not self.reveal_started:
            self._elapsed = min(self.LOAD_DURATION, self._elapsed + dt)
            self.progress = min(1.0, self._elapsed / self.LOAD_DURATION)
            self.search_offset = int(round(3 * math.sin(self._elapsed * 15.0)))
            if self.progress >= self.FOUND_PROGRESS:
                self.reveal_started = True
                self._call_found_once()
            return

        if self.progress < 1.0:
            self._elapsed = min(self.LOAD_DURATION, self._elapsed + dt)
            self.progress = min(1.0, self._elapsed / self.LOAD_DURATION)
            return

        self._reveal_elapsed += dt
        if self._reveal_elapsed < self.REVEAL_HOLD:
            return

        self.active = False
        if not self._completed and self._on_complete is not None:
            self._completed = True
            self._on_complete()

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
        if not monitor_sequence_drawn:
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
        frame = pygame.transform.smoothscale(frame, self.MONITOR_FRAME_RECT.size)
        draw_filled_rect(surface, self.MONITOR_SCREEN_RECT, palette.BLACK)
        surface.blit(frame, self.MONITOR_FRAME_RECT.topleft)
        return True

    def _monitor_frame_index(self) -> int:
        """将加载进度映射到转身过程，并把最后两帧留给发现提示。"""
        if not self.reveal_started:
            return min(21, int(self.progress * 22))

        reveal_progress = min(1.0, self._reveal_elapsed / max(self.REVEAL_HOLD, 0.001))
        return min(self.MONITOR_FRAME_COUNT - 1, 22 + int(reveal_progress * 2))

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

    def _draw_searching_shadow(self, surface: pygame.Surface) -> None:
        """Before 98%, make the screen figure search by twitching its head."""
        cx, cy = config.SCREEN_WIDTH // 2 + self.search_offset, config.SCREEN_HEIGHT // 2 + 2
        draw_filled_rect(surface, (cx - 8, cy - 17, 16, 11), palette.BLACK)
        draw_filled_rect(surface, (cx - 10 + self.search_offset, cy - 20, 8, 2), palette.DEEP_BLUE)
        draw_filled_rect(surface, (cx + 4 + self.search_offset, cy - 19, 7, 2), palette.DEEP_BLUE)
        draw_line(surface, (cx - 13, cy - 4), (cx + 13, cy - 4), palette.DARK_BLOOD)

    def _draw_found_you(self, surface: pygame.Surface) -> None:
        """At 98%, make the figure snap its neck around and announce it found you."""
        cx, cy = config.SCREEN_WIDTH // 2, config.SCREEN_HEIGHT // 2 + 2
        veil = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT), pygame.SRCALPHA)
        veil.fill((*palette.DARK_BLOOD, 48))
        surface.blit(veil, (0, 0))
        try:
            face = load_image("sprites/moonspace/transition_found_you_face.png")
        except (FileNotFoundError, pygame.error):
            face = None

        if face is not None:
            face = pygame.transform.smoothscale(face, (62, 76))
            face.set_alpha(178)
            shadow = pygame.Surface(face.get_size(), pygame.SRCALPHA)
            shadow.fill((*palette.BLACK, 88))
            face.blit(shadow, (0, 0), special_flags=pygame.BLEND_RGBA_SUB)
            clip = pygame.Surface((62, 54), pygame.SRCALPHA)
            clip.blit(face, (0, 0), pygame.Rect(0, 0, 62, 54))
            surface.blit(clip, (cx - clip.get_width() // 2, cy - 24))
        else:
            draw_filled_rect(surface, (cx - 14, cy - 18, 28, 24), palette.BLACK)
            draw_filled_rect(surface, (cx - 9, cy - 10, 5, 2), palette.BLOOD_RED)
            draw_filled_rect(surface, (cx + 4, cy - 10, 5, 2), palette.BLOOD_RED)
            draw_line(surface, (cx - 10, cy - 2), (cx + 10, cy - 2), palette.DARK_BLOOD)
            draw_filled_rect(surface, (cx - 18, cy + 5, 36, 52), palette.BLACK)

        draw_filled_rect(surface, (cx - 27, cy + 19, 54, 2), palette.BLOOD_RED)
        draw_filled_rect(surface, (cx - 2, cy + 20, 4, 14), palette.DARK_BLOOD)
        render_text(surface, self.found_message, cx - 36, config.SCREEN_HEIGHT - 68, 18, palette.BLOOD_RED)
