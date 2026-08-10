"""吴刚 NPC。"""

from __future__ import annotations

import pygame

from core.event_bus import EventBus, TREE_BLEEDING
from entities.npc_base import NPCBase
from utils import palette
from utils.assets import load_sprite_grid
from utils.pixel_art import draw_filled_rect, draw_marker_pixels


class Wugang(NPCBase):
    """吴刚伐桂 NPC，每 2 秒砍一刀，第 5 刀触发树流血事件。"""

    CHOP_INTERVAL = 2.0
    CHOP_FRAME_COUNT = 16
    GRID_COLS = 4
    LARGE_FRAME_WIDTH = 76
    LARGE_FRAME_HEIGHT = 92
    REST_FRAME_ROW = 0
    REST_FRAME_COL = 0

    def __init__(self, event_bus: EventBus, x: int = 156, y: int = 346) -> None:
        super().__init__(
            "wugang",
            x,
            y,
            16,
            24,
            [
                "我是吴刚，被罚伐桂千年。",
                "记住：见树需稽首，否则树会记住你。",
                "第五千斧落下时，你会看到不该看的东西。",
            ],
            event_bus,
        )
        self.interaction_rect = self.rect.inflate(72, 40)
        self.anim_state = "chop"
        self.current_frame = 0
        self.chop_count = 0
        self._timer = 0.0
        self.resting_timer = 0.0

    @property
    def is_resting(self) -> bool:
        """月桂大出血自修复时，吴刚暂时停斧。"""
        return self.resting_timer > 0.0

    def rest(self, duration: float) -> None:
        """让吴刚进入休息状态，用于月桂 10 秒自修复窗口。"""
        self.resting_timer = max(self.resting_timer, duration)
        self.anim_state = "rest"
        self.current_frame = 0
        self._timer = 0.0

    def update(self, dt: float, player_rect: pygame.Rect | None = None) -> None:
        """更新交互范围和伐桂计时。"""
        super().update(dt, player_rect)
        if self.is_resting:
            self.resting_timer = max(0.0, self.resting_timer - dt)
            self.anim_state = "rest" if self.is_resting else "chop"
            self.current_frame = 0
            return

        self.anim_state = "chop"
        self._timer += dt
        while self._timer >= self.CHOP_INTERVAL:
            self._timer -= self.CHOP_INTERVAL
            self.chop_count += 1
            if self.chop_count > 0 and self.chop_count % 5 == 0:
                self.event_bus.emit(TREE_BLEEDING, source=self.npc_id)
        self.current_frame = min(
            self.CHOP_FRAME_COUNT - 1,
            int((self._timer / self.CHOP_INTERVAL) * self.CHOP_FRAME_COUNT),
        )

    def draw(self, surface: pygame.Surface, camera_offset: tuple[int, int] = (0, 0)) -> None:
        """绘制吴刚：宽肩、灰肤、异化肌理和伐桂斧动作。"""
        rect = self.rect.move(camera_offset)
        frame = self.current_frame % 4
        try:
            rows = load_sprite_grid(
                "sprites/moonspace/wugang_chop_large.png",
                self.LARGE_FRAME_WIDTH,
                self.LARGE_FRAME_HEIGHT,
                4,
                4,
            )
            if self.is_resting:
                sprite = rows[self.REST_FRAME_ROW][self.REST_FRAME_COL]
            else:
                frame_index = self.current_frame % self.CHOP_FRAME_COUNT
                sprite = rows[frame_index // self.GRID_COLS][frame_index % self.GRID_COLS]
            sprite = pygame.transform.flip(sprite, True, False)
        except (FileNotFoundError, pygame.error, ValueError):
            sprite = None

        if sprite is not None:
            surface.blit(sprite, (rect.centerx - sprite.get_width() // 2, rect.bottom - sprite.get_height()))
            return

        draw_filled_rect(surface, (rect.x + 4, rect.y - 7, 8, 7), palette.SKIN_PALE)
        draw_marker_pixels(
            surface,
            rect.x + 4,
            rect.y - 7,
            [(2, 2), (5, 2), (3, 5), (4, 5)],
            palette.ASH_GRAY,
        )

        draw_filled_rect(surface, (rect.x + 2, rect.y + 1, 12, 5), palette.WUGANG_ROBE)
        draw_filled_rect(surface, (rect.x + 1, rect.y + 6, 14, 9), palette.WUGANG_ROBE)
        draw_filled_rect(surface, (rect.x + 4, rect.y + 15, 3, 8), palette.WOOD_DARK)
        draw_filled_rect(surface, (rect.x + 9, rect.y + 15, 3, 8), palette.WOOD_DARK)
        draw_marker_pixels(
            surface,
            rect.x + 3,
            rect.y + 5,
            [(1, 1), (5, 2), (8, 1), (4, 5), (10, 6)],
            palette.ASH_GRAY,
        )

        if self.is_resting:
            handle = pygame.Rect(rect.x + 2, rect.y + 11, 20, 2)
            head = pygame.Rect(rect.x + 1, rect.y + 9, 6, 5)
        elif frame == 0:
            handle = pygame.Rect(rect.x + 12, rect.y - 10, 2, 20)
            head = pygame.Rect(rect.x + 9, rect.y - 12, 8, 4)
        elif frame == 1:
            handle = pygame.Rect(rect.x + 14, rect.y - 4, 2, 22)
            head = pygame.Rect(rect.x + 12, rect.y - 6, 9, 4)
        elif frame == 2:
            handle = pygame.Rect(rect.x + 15, rect.y + 4, 2, 18)
            head = pygame.Rect(rect.x + 13, rect.y + 16, 10, 4)
        else:
            handle = pygame.Rect(rect.x + 10, rect.y - 2, 2, 21)
            head = pygame.Rect(rect.x + 8, rect.y - 4, 9, 4)

        draw_filled_rect(surface, handle, palette.WOOD_DARK)
        draw_filled_rect(surface, head, palette.MOON_WHITE)
        draw_filled_rect(surface, (head.x + head.width - 2, head.y + 1, 2, head.height), palette.ASH_GRAY)

    def get_visual_rect(self) -> pygame.Rect:
        """返回与 76x92 大图一致的可视范围。"""
        rect = pygame.Rect(0, 0, self.LARGE_FRAME_WIDTH, self.LARGE_FRAME_HEIGHT)
        rect.midbottom = self.rect.midbottom
        return rect

    def get_interaction_hint_anchor(self) -> tuple[int, int]:
        """把 E 提示放在吴刚角色上方。"""
        return self.get_visual_rect().midtop
