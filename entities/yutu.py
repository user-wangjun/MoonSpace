"""玉兔 NPC。"""

from __future__ import annotations

import pygame

from core.event_bus import EventBus, YUTU_POUNDING_CHANGED
from entities.npc_base import NPCBase
from utils import palette
from utils.assets import load_sprite_grid, load_sprite_sheet
from utils.pixel_art import draw_filled_rect, draw_marker_pixels


class Yutu(NPCBase):
    """玉兔捣药 NPC，保持捣药直到对话暂停并支持背后检查。"""

    LARGE_FRAME_WIDTH = 64
    LARGE_FRAME_HEIGHT = 78

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
        """绘制蹲伏类人玉兔，保留长耳、红眼和捣药动作。"""
        rect = self.rect.move(camera_offset)
        frame_index = self.current_frame % 16 if self.is_pounding else 15
        try:
            rows = load_sprite_grid(
                "sprites/moonspace/yutu_pounding_large.png",
                self.LARGE_FRAME_WIDTH,
                self.LARGE_FRAME_HEIGHT,
                4,
                4,
            )
            sprite = rows[frame_index // 4][frame_index % 4]
        except (FileNotFoundError, pygame.error, ValueError):
            try:
                sprite = load_sprite_sheet("sprites/moonspace/yutu_pounding.png", 24, 24)[frame_index % 4]
            except (FileNotFoundError, pygame.error, ValueError):
                sprite = None

        if sprite is not None:
            surface.blit(sprite, (rect.centerx - sprite.get_width() // 2, rect.bottom - sprite.get_height()))
            return

        ear_offset = 1 if self.current_frame == 1 and self.is_pounding else 0

        draw_filled_rect(surface, (rect.x + 3, rect.y - 8 - ear_offset, 2, 10), palette.YUTU_WHITE)
        draw_filled_rect(surface, (rect.x + 10, rect.y - 7 + ear_offset, 3, 9), palette.YUTU_WHITE)
        draw_filled_rect(surface, (rect.x + 5, rect.y + 1, 7, 6), palette.YUTU_WHITE)
        draw_filled_rect(surface, (rect.x + 3, rect.y + 7, 11, 6), palette.YUTU_WHITE)
        draw_filled_rect(surface, (rect.x + 2, rect.y + 12, 4, 3), palette.ASH_GRAY)
        draw_filled_rect(surface, (rect.x + 11, rect.y + 11, 4, 4), palette.ASH_GRAY)
        draw_marker_pixels(
            surface,
            rect.x + 6,
            rect.y + 3,
            [(0, 0), (4, 1)],
            palette.BLOOD_RED,
        )

        if self.is_pounding:
            pestle_y = rect.y + 7 + (self.current_frame % 3)
            draw_filled_rect(surface, (rect.x + 7, pestle_y, 2, 9), palette.MOON_WHITE)
            draw_filled_rect(surface, (rect.x + 5, rect.y + 13, 6, 2), palette.WOOD_DARK)
        else:
            draw_filled_rect(surface, (rect.x + 6, rect.y + 10, 5, 1), palette.MOON_WHITE)

    def get_visual_rect(self) -> pygame.Rect:
        """返回与 64x78 大图一致的可视范围。"""
        rect = pygame.Rect(0, 0, self.LARGE_FRAME_WIDTH, self.LARGE_FRAME_HEIGHT)
        rect.midbottom = self.rect.midbottom
        return rect

    def get_interaction_hint_anchor(self) -> tuple[int, int]:
        """把 E 提示放在玉兔耳尖上方。"""
        return self.get_visual_rect().midtop
