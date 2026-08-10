"""玉兔 NPC。"""

from __future__ import annotations

import pygame

from core.event_bus import EventBus, YUTU_POUNDING_CHANGED
from entities.npc_base import NPCBase
from utils import palette
from utils.assets import load_sprite_grid
from utils.pixel_art import draw_filled_rect, draw_marker_pixels


class Yutu(NPCBase):
    """玉兔捣药 NPC，保持捣药直到对话暂停并支持背后检查。"""

    LARGE_FRAME_WIDTH = 64
    LARGE_FRAME_HEIGHT = 78
    # The approved atlas was authored with the baked mortar on the left of the
    # rabbit. Once the prop is anchored at PoundTable's world collision point,
    # move only the character layers so hands and pestle still meet the bowl.
    DRAW_OFFSET_X = 24
    BODY_SPRITE_PATH = "sprites/moonspace/yutu_body_4x4.png"
    PESTLE_OVERLAY_PATH = "sprites/moonspace/yutu_pestle_overlay_4x4.png"
    LEGACY_LARGE_SPRITE_PATH = "sprites/moonspace/yutu_pounding_large.png"

    def __init__(self, event_bus: EventBus, x: int = 702, y: int = 304) -> None:
        super().__init__(
            "yutu",
            x,
            y,
            16,
            16,
            [
                "我是玉兔，在此捣药千年。",
                "切记：我捣药时，你不该看。",
                "月池中的倒影，不是你的。",
            ],
            event_bus,
        )
        # 大图远宽于 16x16 硬碰撞，交互区必须覆盖右侧药臼后的可达位置。
        self.interaction_rect = self.rect.inflate(92, 48)
        self.is_pounding = True
        self.current_frame = 0
        self._timer = 0.0

    def update(self, dt: float, player_rect: pygame.Rect | None = None) -> None:
        """更新可交互状态；对话期间停杵，关闭对话后恢复。"""
        was_pounding = self.is_pounding
        super().update(dt, player_rect)
        # 靠近本身不能让规则失效；只有进入对话暂停态时才停杵。
        self.is_pounding = not self.dialog_active
        if was_pounding != self.is_pounding:
            self.event_bus.emit(YUTU_POUNDING_CHANGED, is_pounding=self.is_pounding)

        if self.is_pounding:
            self._timer += dt
            while self._timer >= 0.35:
                self._timer -= 0.35
                self.current_frame = (self.current_frame + 1) % 16

    def draw(self, surface: pygame.Surface, camera_offset: tuple[int, int] = (0, 0)) -> None:
        """绘制分层玉兔：本体先画，手部/杵透明覆盖层后画。"""
        rect = self.rect.move(camera_offset)
        frame_index = self.current_frame % 16 if self.is_pounding else 15
        sprite = self._load_frame(self.BODY_SPRITE_PATH, frame_index)
        large_sprite = sprite is not None
        if sprite is None:
            # Compatibility fallback is deliberately after the new body layer;
            # the normal path never loads the old baked prop sheet.
            sprite = self._load_frame(self.LEGACY_LARGE_SPRITE_PATH, frame_index)
            large_sprite = sprite is not None
        if sprite is None:
            large_sprite = False

        if sprite is not None:
            surface.blit(
                sprite,
                (
                    rect.centerx + self.DRAW_OFFSET_X - sprite.get_width() // 2,
                    rect.bottom - sprite.get_height(),
                ),
            )
        else:
            self._draw_procedural_body(surface, rect)

        overlay = self._load_frame(self.PESTLE_OVERLAY_PATH, frame_index) if large_sprite else None
        if overlay is not None:
            surface.blit(
                overlay,
                (
                    rect.centerx + self.DRAW_OFFSET_X - overlay.get_width() // 2,
                    rect.bottom - overlay.get_height(),
                ),
            )
        else:
            self._draw_procedural_overlay(surface, rect)

    def _load_frame(self, path: str, frame_index: int) -> pygame.Surface | None:
        """Load one transparent body/overlay frame without letting missing art crash."""
        try:
            rows = load_sprite_grid(path, self.LARGE_FRAME_WIDTH, self.LARGE_FRAME_HEIGHT, 4, 4)
            return rows[frame_index // 4][frame_index % 4]
        except (FileNotFoundError, pygame.error, ValueError, IndexError):
            return None

    def _draw_procedural_body(self, surface: pygame.Surface, rect: pygame.Rect) -> None:
        """Minimal identity-preserving body fallback; props stay in the overlay."""
        ear_offset = 1 if self.current_frame == 1 and self.is_pounding else 0
        draw_filled_rect(surface, (rect.x + 3, rect.y - 8 - ear_offset, 2, 10), palette.YUTU_WHITE)
        draw_filled_rect(surface, (rect.x + 10, rect.y - 7 + ear_offset, 3, 9), palette.YUTU_WHITE)
        draw_filled_rect(surface, (rect.x + 5, rect.y + 1, 7, 6), palette.YUTU_WHITE)
        draw_filled_rect(surface, (rect.x + 3, rect.y + 7, 11, 6), palette.YUTU_WHITE)
        draw_filled_rect(surface, (rect.x + 2, rect.y + 12, 4, 3), palette.ASH_GRAY)
        draw_filled_rect(surface, (rect.x + 11, rect.y + 11, 4, 4), palette.ASH_GRAY)
        draw_marker_pixels(surface, rect.x + 6, rect.y + 3, [(0, 0), (4, 1)], palette.BLOOD_RED)

    def _draw_procedural_overlay(self, surface: pygame.Surface, rect: pygame.Rect) -> None:
        """Safe emergency hand/杵 layer used only when both transparent atlases are absent."""
        if self.is_pounding:
            pestle_y = rect.y + 7 + (self.current_frame % 3)
            draw_filled_rect(surface, (rect.x + 7, pestle_y, 2, 9), palette.MOON_WHITE)
            draw_filled_rect(surface, (rect.x + 5, rect.y + 13, 6, 2), palette.WOOD_DARK)
        else:
            draw_filled_rect(surface, (rect.x + 6, rect.y + 10, 5, 1), palette.MOON_WHITE)

    def get_visual_rect(self) -> pygame.Rect:
        """返回与 64x78 大图一致的可视范围。"""
        rect = pygame.Rect(0, 0, self.LARGE_FRAME_WIDTH, self.LARGE_FRAME_HEIGHT)
        rect.midbottom = (self.rect.centerx + self.DRAW_OFFSET_X, self.rect.bottom)
        return rect

    def get_interaction_hint_anchor(self) -> tuple[int, int]:
        """把 E 提示放在玉兔耳尖上方。"""
        return self.get_visual_rect().midtop
