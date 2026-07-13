"""月桂树场景物体。"""

from __future__ import annotations

import math

import pygame

from utils import palette
from utils.assets import load_image
from utils.pixel_art import draw_filled_rect, draw_marker_pixels, draw_rect


class LaurelTree:
    """月桂树规则锚点，作为前院里的大型恐怖地标。"""

    SPRITE_SIZE = (176, 220)
    BLEED_DURATION = 10.0
    RULE_RADIUS = 176

    def __init__(self, x: int = 24, y: int = 204) -> None:
        self.position = pygame.Vector2(x, y)
        self.sprite_rect = pygame.Rect(x, y, *self.SPRITE_SIZE)
        self.rect = pygame.Rect(x + 58, y + 136, 64, 76)
        # 地面禁区以树根为中心呈圆形；只有流血异像时才会解除。
        self.rule_center = (self.rect.centerx, self.rect.centery + 4)
        self.rule_radius = self.RULE_RADIUS
        self.rule_rect = pygame.Rect(0, 0, self.rule_radius * 2, self.rule_radius * 2)
        self.rule_rect.center = self.rule_center
        self.trunk_rect = pygame.Rect(x + 76, y + 70, 34, 138)
        self.crown_rect = pygame.Rect(x + 10, y, 156, 132)
        self.bleeding = False
        self.horror_intensity = 0.0
        self._time = 0.0
        self.bleed_time = 0.0

    def update(self, dt: float) -> None:
        """推进呼吸动画计时。"""
        self._time += dt
        if self.bleeding:
            self.bleed_time += dt
            if self.bleed_time >= self.BLEED_DURATION:
                self.set_bleeding(False)

    def draw(self, surface: pygame.Surface, camera_offset: tuple[int, int] = (0, 0)) -> None:
        """绘制呼吸感树冠和树干纹理。"""
        ox, oy = camera_offset
        pulse = 1 if math.sin(self._time * 2.0) > 0.4 else 0
        breath = 1 if math.sin(self._time * 1.4) > 0.35 else 0
        trunk = self.trunk_rect.move(ox, oy)
        crown = self.crown_rect.inflate(pulse * 2, pulse * 2).move(ox - pulse, oy - pulse)
        try:
            load_image("sprites/moonspace/courtyard_bg_large.png")
            large_background_available = True
        except (FileNotFoundError, pygame.error):
            large_background_available = False

        if large_background_available:
            try:
                sprite = load_image("sprites/moonspace/laurel_tree.png")
            except (FileNotFoundError, pygame.error):
                sprite = None

            if sprite is not None:
                self._blit_living_sprite(surface, sprite, ox, oy, breath)
            self._draw_large_background_overlay(surface, trunk)
            self._draw_living_overlay(surface, ox, oy)
            return

        try:
            sprite = load_image("sprites/moonspace/laurel_tree.png")
        except (FileNotFoundError, pygame.error):
            sprite = None

        if sprite is not None:
            self._blit_living_sprite(surface, sprite, ox, oy, breath)
            self._draw_living_overlay(surface, ox, oy)
            if self.bleeding:
                drip = int(self.bleed_time * 9) % 14
                pulse = int((math.sin(self.bleed_time * 5) + 1) * 2)
                draw_filled_rect(surface, (trunk.x + 7, trunk.y + 21, 2, 18), palette.BLOOD_RED)
                draw_filled_rect(surface, (trunk.x + 11, trunk.y + 26, 1, 13), palette.DARK_BLOOD)
                draw_filled_rect(surface, (trunk.x + 8, trunk.y + 23 + drip, 2, 3), palette.BLOOD_RED)
                draw_filled_rect(surface, (trunk.x - 6, trunk.bottom - 4, 18 + pulse, 1), palette.BLOOD_RED)
            return

        draw_filled_rect(surface, (trunk.x - 8, trunk.bottom - 6, 34, 3), palette.LAUREL_DARK)
        draw_filled_rect(surface, (trunk.x - 4, trunk.bottom - 2, 28, 2), palette.WOOD_DARK)
        draw_filled_rect(surface, trunk, palette.WOOD_DARK)
        draw_filled_rect(surface, (trunk.x + 3, trunk.y + 2, 5, trunk.height - 4), palette.WOOD_BROWN)
        draw_filled_rect(surface, (trunk.x + 10, trunk.y + 5, 4, trunk.height - 8), palette.LAUREL_DARK)

        draw_filled_rect(surface, crown, palette.LAUREL_GREEN)
        draw_filled_rect(surface, (crown.x + 4, crown.y - 4, 20, 11), palette.LAUREL_DARK)
        draw_filled_rect(surface, (crown.x + 16, crown.y + 4, 28, 15), palette.LAUREL_GREEN)
        draw_filled_rect(surface, (crown.x - 2, crown.y + 11, 22, 17), palette.LAUREL_DARK)
        draw_rect(surface, crown.x, crown.y, crown.width, crown.height, palette.LAUREL_DARK)

        draw_marker_pixels(
            surface,
            trunk.x + 4,
            trunk.y + 8,
            [(2, 2), (8, 2), (4, 8), (5, 8), (2, 15), (3, 15), (9, 16)],
            palette.ASH_GRAY,
        )
        draw_filled_rect(surface, (trunk.x + 6, trunk.y + 19, 6, 1), palette.ASH_GRAY)

        if self.bleeding:
            drip = int(self.bleed_time * 9) % 14
            pulse = int((math.sin(self.bleed_time * 5) + 1) * 2)
            draw_filled_rect(surface, (trunk.x + 7, trunk.y + 21, 2, 18), palette.BLOOD_RED)
            draw_filled_rect(surface, (trunk.x + 11, trunk.y + 26, 1, 13), palette.DARK_BLOOD)
            draw_filled_rect(surface, (trunk.x + 8, trunk.y + 23 + drip, 2, 3), palette.BLOOD_RED)
            draw_filled_rect(surface, (trunk.x - 6, trunk.bottom - 4, 18 + pulse, 1), palette.BLOOD_RED)

    def _blit_living_sprite(
        self,
        surface: pygame.Surface,
        sprite: pygame.Surface,
        ox: int,
        oy: int,
        breath: int,
    ) -> None:
        """Draw the tree bottom-anchored, with a tiny breathing scale."""
        if breath <= 0:
            surface.blit(sprite, self.sprite_rect.move(ox, oy))
            return

        width = sprite.get_width() + 2
        height = sprite.get_height() + 2
        living = pygame.transform.smoothscale(sprite, (width, height))
        x = self.sprite_rect.centerx + ox - width // 2
        y = self.sprite_rect.bottom + oy - height
        surface.blit(living, (x, y))

    def _draw_living_overlay(self, surface: pygame.Surface, ox: int, oy: int) -> None:
        """Add subtle branch twitches and wound glows so the tree feels alive."""
        sway = int(math.sin(self._time * 2.8) * 2)
        glow = 1 + int((math.sin(self._time * 4.2) + 1) * 1.5)
        base_x = self.sprite_rect.x + ox
        base_y = self.sprite_rect.y + oy
        wounds = (
            (88, 78),
            (101, 111),
            (75, 139),
            (114, 159),
            (91, 184),
        )
        for x, y in wounds:
            draw_filled_rect(surface, (base_x + x, base_y + y, 3, 2 + glow), palette.DARK_BLOOD)
            if glow >= 3:
                draw_filled_rect(surface, (base_x + x + 1, base_y + y + 1, 1, 2), palette.BLOOD_RED)

        twig_color = palette.HORROR_CYAN_GRAY if int(self._time * 5) % 2 else palette.DEEP_BLUE
        twigs = (
            ((base_x + 28, base_y + 68), (base_x + 15 + sway, base_y + 58)),
            ((base_x + 142, base_y + 72), (base_x + 157 + sway, base_y + 62)),
            ((base_x + 50, base_y + 38), (base_x + 42 - sway, base_y + 25)),
            ((base_x + 123, base_y + 35), (base_x + 132 + sway, base_y + 22)),
        )
        for start, end in twigs:
            pygame.draw.line(surface, twig_color, start, end, 1)

    def _draw_large_background_overlay(self, surface: pygame.Surface, trunk: pygame.Rect) -> None:
        """叠加规则反馈，让大月桂在流血状态更明显。"""
        if not self.bleeding:
            return

        progress = min(1.0, self.bleed_time / self.BLEED_DURATION)
        drip = int(self.bleed_time * 14) % 34
        pulse = int((math.sin(self.bleed_time * 5) + 1) * 4)
        repair = int(progress * 16)
        wounds = (
            (trunk.x - 4, trunk.y - 18, 2, 42),
            (trunk.x + 7, trunk.y - 8, 2, 48),
            (trunk.x + 20, trunk.y + 3, 2, 34),
        )
        for index, (x, y, width, height) in enumerate(wounds):
            visible_height = max(8, height - repair - index * 2)
            color = palette.BLOOD_RED if index % 2 else palette.DARK_BLOOD
            draw_filled_rect(surface, (x, y, width, visible_height), color)
            draw_filled_rect(surface, (x, y + 18 + drip // 2, width, 2), palette.BLOOD_RED)

        pool_width = 42 + pulse - repair
        draw_filled_rect(surface, (trunk.x - 8, trunk.bottom - 3, max(22, pool_width), 2), palette.DARK_BLOOD)
        draw_filled_rect(surface, (trunk.x + 8, trunk.bottom - 2, 10, 1), palette.BLOOD_RED)
        scar_color = palette.HORROR_CYAN_GRAY if int(self.bleed_time * 4) % 2 else palette.PALE_MOON
        pygame.draw.line(surface, scar_color, (trunk.x - 7, trunk.y - 20), (trunk.x + 25, trunk.y + 42), 1)
        pygame.draw.line(surface, scar_color, (trunk.x + 31, trunk.y + 8), (trunk.x + 3, trunk.y + 72), 1)

    def set_bleeding(self, bleeding: bool = True) -> None:
        """切换 10 秒流血/自修复状态，后续由吴刚第 5 刀事件触发。"""
        was_bleeding = self.bleeding
        self.bleeding = bleeding
        if bleeding and not was_bleeding:
            self.bleed_time = 0.0
        elif not bleeding:
            self.bleed_time = 0.0

    def get_collision_rect(self) -> pygame.Rect:
        """返回树的硬碰撞区域。"""
        return self.rect.copy()

    def get_rule_rect(self) -> pygame.Rect:
        """返回圆形规则区的外接矩形，供调试与边界检查。"""
        return self.rule_rect.copy()

    def get_rule_circle(self) -> tuple[tuple[int, int], int]:
        """返回月桂地面禁区的圆心与半径。"""
        return self.rule_center, self.rule_radius
