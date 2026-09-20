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
            sprite = load_image("sprites/moonspace/laurel_tree.png")
        except (FileNotFoundError, pygame.error):
            sprite = None

        if sprite is not None:
            # Compose wounds before breathing/camera transforms so they stay on bark.
            living = sprite.copy()
            self._draw_living_overlay(living, sprite)
            self._blit_living_sprite(surface, living, ox, oy, breath)
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

    def _draw_living_overlay(self, surface: pygame.Surface, sprite: pygame.Surface) -> None:
        """Follow the painted wounds and bark grooves in sprite-local coordinates."""
        overlay = pygame.Surface(sprite.get_size(), pygame.SRCALPHA)
        paths = (
            ((85, 63), (86, 70), (92, 79), (93, 88), (87, 97)),
            ((77, 103), (79, 111), (86, 120), (88, 128)),
            ((89, 137), (86, 145), (90, 154), (97, 163)),
            ((101, 165), (98, 174), (91, 184), (87, 195), (78, 207)),
        )
        glow = (math.sin(self._time * 4.2) + 1) * 0.5
        for points in paths:
            pygame.draw.lines(overlay, (*palette.DARK_BLOOD, int(50 + glow * 45)), False, points[:2], 2)

        if self.bleeding:
            # The final two seconds close the wounds gradually, without flashing scars.
            strength = min(1.0, max(0.0, (self.BLEED_DURATION - self.bleed_time) / 2.0))
            for index, points in enumerate(paths):
                pygame.draw.lines(overlay, (*palette.DARK_BLOOD, int(220 * strength)), False, points, 3)
                pygame.draw.lines(overlay, (*palette.BLOOD_RED, int(255 * strength)), False, points, 1)
                travel = (self.bleed_time * 1.6 + index * 0.7) % (len(points) - 1)
                segment = int(travel)
                point = pygame.Vector2(points[segment]).lerp(points[segment + 1], travel - segment)
                pygame.draw.circle(overlay, (177, 39, 34, int(230 * strength)), (round(point.x), round(point.y)), 1)

        # Preserve transparency: no detached blood, rectangular puddle, or stray twigs.
        mask = sprite.copy()
        mask.fill((255, 255, 255, 0), special_flags=pygame.BLEND_RGBA_MAX)
        overlay.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        surface.blit(overlay, (0, 0))

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
