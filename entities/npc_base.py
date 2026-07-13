"""NPC 基类：交互范围和对话触发。"""

from __future__ import annotations

import pygame

from core.event_bus import DIALOG_ACTIVE_CHANGED, EventBus, SHOW_DIALOG


class NPCBase:
    """NPC 公共能力，避免吴刚、玉兔重复实现交互和对话触发。"""

    def __init__(
        self,
        npc_id: str,
        x: int,
        y: int,
        width: int,
        height: int,
        dialogs: list[str],
        event_bus: EventBus,
    ) -> None:
        self.npc_id = npc_id
        self.position = pygame.Vector2(x, y)
        self.rect = pygame.Rect(x, y, width, height)
        self.interaction_rect = self.rect.inflate(28, 24)
        self.dialogs = dialogs
        self.event_bus = event_bus
        self.player_in_range = False
        self.dialog_active = False
        self.event_bus.subscribe(DIALOG_ACTIVE_CHANGED, self._on_dialog_active_changed)

    def update(self, dt: float, player_rect: pygame.Rect | None = None) -> None:
        """更新交互范围；子类可扩展动画和行为。"""
        _ = dt
        if player_rect is not None:
            self.player_in_range = self.interaction_rect.colliderect(player_rect)

    def draw(self, surface: pygame.Surface, camera_offset: tuple[int, int] = (0, 0)) -> None:
        """子类负责具体绘制。"""
        _ = surface, camera_offset

    def interact(self) -> bool:
        """玩家按交互键时触发对话；成功触发返回 True。"""
        if not self.player_in_range or self.dialog_active:
            return False

        self.event_bus.emit(SHOW_DIALOG, speaker_id=self.npc_id, lines=self.dialogs)
        return True

    def can_interact(self, player_rect: pygame.Rect) -> bool:
        """判断玩家是否在交互范围内。"""
        return self.interaction_rect.colliderect(player_rect)

    def get_collision_rect(self) -> pygame.Rect:
        """返回 NPC 碰撞矩形。"""
        return self.rect.copy()

    def get_interaction_hint_anchor(self) -> tuple[int, int]:
        """返回交互提示锚点；大型角色可按可视精灵覆盖。"""
        return self.rect.midtop

    def _on_dialog_active_changed(self, active: bool, **payload) -> None:
        """记录对话状态，避免对话中重复触发。"""
        _ = payload
        self.dialog_active = active
