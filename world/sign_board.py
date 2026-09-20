"""告示牌场景物体。"""

from __future__ import annotations

import pygame

from core.demo_rules import (
    RULE_BOW_TO_TREE,
    RULE_NO_EYE_CONTACT,
    RULE_POOL_REFLECTION,
    RULE_TEXTS,
    RULE_TREE_BLEEDING,
)
from core.game_state import GameState
from utils import palette
from utils.assets import load_image
from utils.pixel_art import draw_filled_rect, draw_rect


RULE_MAINLINE_FLOW = "rule_mainline_flow"
RULE_MAINLINE_BOUNDARY = "rule_mainline_boundary"
RULE_REPAIR_MOON = "rule_repair_moon"


BASIC_RULES = {
    RULE_MAINLINE_FLOW: "凌霄来使入宫，须验明三职：吴刚伐桂、玉兔捣药、偏殿修月。三验俱全，方入广寒宫复命；命毕方可返月谷。",
    RULE_BOW_TO_TREE: RULE_TEXTS[RULE_BOW_TO_TREE],
    RULE_NO_EYE_CONTACT: RULE_TEXTS[RULE_NO_EYE_CONTACT],
    RULE_POOL_REFLECTION: RULE_TEXTS[RULE_POOL_REFLECTION],
    RULE_TREE_BLEEDING: RULE_TEXTS[RULE_TREE_BLEEDING],
    RULE_REPAIR_MOON: "修月偏殿在广场西墙中段。门前右蟾定向，左蟾可转；月桂未见血时不得近，异像现时方可转蟾。两蟾朝向相合，偏殿门自开；入内后限六十息验出真正裂口。",
    RULE_MAINLINE_BOUNDARY: "来使只验、只记、只复命；不得代职，不得候宫。",
}


class SignBoard:
    """初始告示牌，玩家交互后发现基础规则。"""

    def __init__(self, x: int = 170, y: int = 404) -> None:
        self.position = pygame.Vector2(x, y)
        self.rect = pygame.Rect(x, y, 18, 24)
        self.interaction_rect = self.rect.inflate(24, 20)
        self.has_been_read = False

    def update(self, dt: float) -> None:
        """静态告示牌保留统一接口。"""
        _ = dt

    def draw(self, surface: pygame.Surface, camera_offset: tuple[int, int] = (0, 0)) -> None:
        """绘制木质告示牌，已读后边框变为月白色。"""
        rect = self.rect.move(camera_offset)
        try:
            sprite = load_image("sprites/moonspace/sign_board.png")
        except (FileNotFoundError, pygame.error):
            sprite = None

        if sprite is not None:
            surface.blit(sprite, (rect.x - 3, rect.y - 4))
            if self.has_been_read:
                draw_rect(surface, rect.x - 1, rect.y, rect.width + 2, rect.height - 3, palette.MOON_WHITE)
            return

        draw_filled_rect(surface, (rect.x + 2, rect.y + 2, rect.width - 4, rect.height - 7), palette.WOOD_BROWN)
        draw_filled_rect(surface, (rect.x, rect.y, rect.width, 4), palette.WOOD_DARK)
        draw_filled_rect(surface, (rect.x + 3, rect.bottom - 6, 3, 6), palette.WOOD_DARK)
        draw_filled_rect(surface, (rect.right - 6, rect.bottom - 6, 3, 6), palette.WOOD_DARK)
        border_color = palette.MOON_WHITE if self.has_been_read else palette.WOOD_DARK
        draw_rect(surface, rect.x + 2, rect.y + 2, rect.width - 4, rect.height - 7, border_color)
        draw_filled_rect(surface, (rect.x + 4, rect.y + 5, 10, 1), palette.MOON_WHITE)
        draw_filled_rect(surface, (rect.x + 4, rect.y + 10, 8, 1), palette.MOON_WHITE)
        draw_filled_rect(surface, (rect.x + 4, rect.y + 15, 11, 1), palette.MOON_WHITE)
        draw_filled_rect(surface, (rect.x + 13, rect.y + 11, 1, 5), palette.DARK_BLOOD)

    def can_interact(self, player_rect: pygame.Rect) -> bool:
        """判断玩家是否进入告示牌交互范围。"""
        return self.interaction_rect.colliderect(player_rect)

    def interact(self, game_state: GameState) -> bool:
        """读取告示牌，将基础规则加入已知规则；返回是否首次读取。"""
        first_read = not self.has_been_read
        self.has_been_read = True
        for rule_id, rule_text in BASIC_RULES.items():
            game_state.add_known_rule(rule_id, rule_text)
        return first_read

    def get_collision_rect(self) -> pygame.Rect:
        """返回告示牌碰撞。"""
        return self.rect.copy()
