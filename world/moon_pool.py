"""月池场景物体。"""

from __future__ import annotations

import math

import pygame

from utils import palette
from utils.assets import load_image
from utils.pixel_art import draw_filled_rect, draw_rect


class MoonPool:
    """月池提供实体碰撞和倒影规则触发区域。"""

    SPRITE_PATH = "sprites/moonspace/moon_pool_large.png"
    FALLBACK_SPRITE_PATH = "sprites/moonspace/moon_pool.png"
    DEFAULT_CENTER = (480, 360)
    SPRITE_SIZE = (144, 144)
    COLLISION_SIZE = (112, 112)
    REFLECTION_INFLATE = (56, 56)
    WATER_INSET = 22
    REFLECTION_MAX_HEIGHT = 52

    def __init__(self, center_x: int = DEFAULT_CENTER[0], center_y: int = DEFAULT_CENTER[1]) -> None:
        self.position = pygame.Vector2(center_x, center_y)
        self.rect = pygame.Rect(0, 0, *self.COLLISION_SIZE)
        self.rect.center = (center_x, center_y)
        self.visual_rect = pygame.Rect(0, 0, *self.SPRITE_SIZE)
        self.visual_rect.center = (center_x, center_y)
        self.reflection_rect = self.visual_rect.inflate(*self.REFLECTION_INFLATE)
        self._time = 0.0
        self.reflection_flash_timer = 0.0
        self.gaze_progress = 0.0

    def update(self, dt: float) -> None:
        """推进水面波纹计时。"""
        self._time += dt
        self.reflection_flash_timer = max(0.0, self.reflection_flash_timer - dt)

    def draw(
        self,
        surface: pygame.Surface,
        camera_offset: tuple[int, int] = (0, 0),
        *,
        reflection_sprite: pygame.Surface | None = None,
        anomaly_sprite: pygame.Surface | None = None,
        observer_center: tuple[int, int] | None = None,
        show_reflection: bool = False,
        show_pollution: bool = False,
    ) -> None:
        """绘制正式月池资源、污染附加层与倒影反馈。"""
        rect = self.rect.move(camera_offset)
        visual_rect = self.visual_rect.move(camera_offset)
        try:
            sprite = load_image(self.SPRITE_PATH)
        except (FileNotFoundError, pygame.error):
            try:
                sprite = load_image(self.FALLBACK_SPRITE_PATH)
            except (FileNotFoundError, pygame.error):
                sprite = None

        if sprite is not None:
            if sprite.get_size() != visual_rect.size:
                sprite = pygame.transform.smoothscale(sprite, visual_rect.size)
            surface.blit(sprite, visual_rect.topleft)
            self._draw_water_feedback(
                surface,
                visual_rect,
                reflection_sprite=reflection_sprite,
                anomaly_sprite=anomaly_sprite,
                observer_center=observer_center,
                show_reflection=show_reflection,
                show_pollution=show_pollution,
            )
            return

        draw_filled_rect(surface, rect, palette.DEEP_BLUE)
        draw_rect(surface, rect.x, rect.y, rect.width, rect.height, palette.POOL_HIGHLIGHT)
        inner = rect.inflate(-6, -6)
        draw_filled_rect(surface, inner, (6, 11, 21))
        draw_rect(surface, inner.x, inner.y, inner.width, inner.height, palette.PALE_MOON)
        phase = int(self._time * 4) % 4
        for i in range(3):
            y = inner.y + 5 + i * 6
            x = inner.x + 4 + ((phase + i) % 4)
            draw_filled_rect(surface, (x, y, 29, 1), palette.POOL_HIGHLIGHT)
        if self.reflection_flash_timer > 0:
            self._draw_reflection_face(surface, inner)
        if show_pollution:
            self._draw_water_feedback(
                surface,
                visual_rect,
                observer_center=observer_center,
                show_pollution=True,
            )

    def _draw_water_feedback(
        self,
        surface: pygame.Surface,
        visual_rect: pygame.Rect,
        *,
        reflection_sprite: pygame.Surface | None = None,
        anomaly_sprite: pygame.Surface | None = None,
        observer_center: tuple[int, int] | None = None,
        show_reflection: bool = False,
        show_pollution: bool = False,
    ) -> None:
        """在池面内部绘制低干扰波纹、污染扩散和违规倒影。"""
        feedback = pygame.Surface(visual_rect.size, pygame.SRCALPHA)
        inner = pygame.Rect(0, 0, *visual_rect.size).inflate(-self.WATER_INSET * 2, -self.WATER_INSET * 2)
        if show_pollution:
            self._draw_pollution_overlay(feedback, inner)
        if show_reflection and reflection_sprite is not None:
            anomalous = self.reflection_flash_timer > 0
            sprite = anomaly_sprite if anomalous and anomaly_sprite is not None else reflection_sprite
            # 先让水中身影悄悄转向观察者，真正违规后才显露红眼。
            anticipation = max(0.0, min(1.0, (self.gaze_progress - 0.45) / 0.45))
            if not anomalous and anticipation > 0 and anomaly_sprite is not None:
                sprite = reflection_sprite.copy()
                turned = pygame.transform.smoothscale(anomaly_sprite, sprite.get_size())
                turned.set_alpha(round(255 * anticipation))
                sprite.blit(turned, (0, 0))
            self._draw_player_reflection(
                feedback,
                inner,
                sprite,
                observer_center=observer_center,
                anomalous=anomalous,
            )

        phase = int(self._time * 5) % 6
        ripple_alpha = round(62 * (1.0 - 0.85 * self.gaze_progress))
        for i, width in enumerate((56, 42, 64)):
            x = inner.centerx - width // 2 + ((phase + i * 2) % 5) - 2
            y = inner.centery - 18 + i * 17
            draw_filled_rect(feedback, (x, y, width, 1), (*palette.HORROR_CYAN_GRAY, ripple_alpha))
        surface.blit(feedback, visual_rect.topleft)

    def _draw_pollution_overlay(self, feedback: pygame.Surface, water_rect: pygame.Rect) -> None:
        """以独立 Alpha 层表现污染从池心向外扩散，不覆盖石质池沿。"""
        layer = pygame.Surface(feedback.get_size(), pygame.SRCALPHA)
        center = water_rect.center
        spread = int((math.sin(self._time * 1.7) + 1.0) * 2.0)
        max_radius = min(water_rect.width, water_rect.height) // 2

        for index, base_radius in enumerate((22, 36, 50)):
            radius = min(max_radius, base_radius + spread + index)
            alpha = max(28, 88 - index * 18)
            pygame.draw.circle(layer, (138, 22, 42, alpha), center, radius, 1)

        for index in range(8):
            angle = self._time * (0.45 + index * 0.02) + index * math.tau / 8.0
            inner_radius = 18 + (index % 3) * 6
            outer_radius = min(max_radius, 44 + (index % 4) * 4 + spread)
            start = (
                round(center[0] + math.cos(angle) * inner_radius),
                round(center[1] + math.sin(angle) * inner_radius),
            )
            end = (
                round(center[0] + math.cos(angle) * outer_radius),
                round(center[1] + math.sin(angle) * outer_radius),
            )
            pygame.draw.line(layer, (108, 16, 34, 46), start, end, 1)

        mask = pygame.Surface(feedback.get_size(), pygame.SRCALPHA)
        pygame.draw.ellipse(mask, (255, 255, 255, 255), water_rect)
        layer.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        feedback.blit(layer, (0, 0))

    def _draw_player_reflection(
        self,
        feedback: pygame.Surface,
        water_rect: pygame.Rect,
        sprite: pygame.Surface,
        *,
        observer_center: tuple[int, int] | None,
        anomalous: bool,
    ) -> None:
        """绘制受水面遮罩限制的翻转、压暗和横向错位角色倒影。"""
        scale = min(1.0, self.REFLECTION_MAX_HEIGHT / max(1, sprite.get_height()))
        scaled_size = (
            max(1, round(sprite.get_width() * scale)),
            max(1, round(sprite.get_height() * scale)),
        )
        reflected = pygame.transform.smoothscale(sprite, scaled_size)
        reflected = pygame.transform.smoothscale(
            reflected,
            (reflected.get_width(), max(1, round(reflected.get_height() * 0.68))),
        )
        moon_glow = pygame.Surface(reflected.get_size(), pygame.SRCALPHA)
        moon_glow.fill((58, 70, 84, 0))
        reflected.blit(moon_glow, (0, 0), special_flags=pygame.BLEND_RGB_ADD)
        tint = pygame.Surface(reflected.get_size(), pygame.SRCALPHA)
        tint.fill((176, 194, 214, 158))
        reflected.blit(tint, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

        amplitude = 4 if anomalous else 2
        distorted = pygame.Surface((reflected.get_width() + amplitude * 2, reflected.get_height()), pygame.SRCALPHA)
        for y in range(0, reflected.get_height(), 2):
            height = min(2, reflected.get_height() - y)
            offset = round(math.sin(self._time * 7.0 + y * 0.65) * amplitude)
            distorted.blit(
                reflected,
                (amplitude + offset, y),
                pygame.Rect(0, y, reflected.get_width(), height),
            )

        outward = pygame.Vector2(0, 1)
        if observer_center is not None:
            outward = pygame.Vector2(observer_center) - pygame.Vector2(self.visual_rect.center)
            if outward.length_squared() == 0:
                outward = pygame.Vector2(0, 1)
        outward = outward.normalize()
        angle = math.degrees(math.atan2(outward.x, outward.y))
        distorted = pygame.transform.rotate(distorted, angle)
        shore_radius = min(water_rect.width, water_rect.height) * 0.40
        shore_anchor = pygame.Vector2(water_rect.center) + outward * shore_radius
        center = shore_anchor - outward * (max(distorted.get_width(), distorted.get_height()) * 0.28)
        target = distorted.get_rect(center=(round(center.x), round(center.y)))

        reflection_layer = pygame.Surface(feedback.get_size(), pygame.SRCALPHA)
        reflection_layer.blit(distorted, target)
        if anomalous:
            face = shore_anchor - outward * 6
            side = pygame.Vector2(-outward.y, outward.x) * 4
            for eye in (face - side, face + side):
                draw_filled_rect(reflection_layer, (round(eye.x) - 1, round(eye.y) - 1, 3, 2), (*palette.BLOOD_RED, 220))

        water_mask = pygame.Surface(feedback.get_size(), pygame.SRCALPHA)
        pygame.draw.ellipse(water_mask, (255, 255, 255, 255), water_rect)
        reflection_layer.blit(water_mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        feedback.blit(reflection_layer, (0, 0))

    def _draw_reflection_face(self, surface: pygame.Surface, inner: pygame.Rect) -> None:
        """触发违规或污染结算时，让月池短暂显出倒影。"""
        head_y = inner.centery - 14
        draw_filled_rect(surface, (inner.centerx - 6, head_y, 12, 13), palette.HORROR_CYAN_GRAY)
        draw_filled_rect(surface, (inner.centerx - 4, head_y + 5, 3, 2), palette.BLACK)
        draw_filled_rect(surface, (inner.centerx + 2, head_y + 5, 3, 2), palette.BLACK)
        draw_filled_rect(surface, (inner.centerx - 2, head_y + 14, 4, 8), palette.DARK_BLOOD)
        draw_filled_rect(surface, (inner.centerx - 13, head_y + 24, 26, 2), palette.BLOOD_RED)

    def flash_reflection(self, duration: float = 1.1) -> None:
        """触发一次倒影显形，用于月池规则反馈。"""
        self.reflection_flash_timer = max(self.reflection_flash_timer, duration)

    def get_collision_rect(self) -> pygame.Rect:
        """返回水面碰撞，避免玩家直接走入月池。"""
        return self.rect.copy()
