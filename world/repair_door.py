"""A courtyard puzzle in which one stone toad is rotated to match the other."""
from __future__ import annotations

import math
import pygame

import config
from utils.assets import load_image
from utils.font import render_text


class RepairDoor:
    SHEET = "sprites/moonspace/sheets/repair_toad_door.png"
    TOADS = "sprites/moonspace/sheets/repair_toad_turn.png"
    SIZE = (92, 94)
    LEFT_ZONE = pygame.Rect(55, 257, 44, 38)
    RIGHT_ZONE = pygame.Rect(96, 188, 38, 30)
    WALL_PATCH = pygame.Rect(0, 130, 145, 150)
    ALIGN_SECONDS = .65
    OPEN_SECONDS = 1.2
    # Z/X are the unambiguous courtyard controls: movement keeps WASD and
    # the arrow keys. A/D and left/right remain accepted as legacy aliases
    # for existing playtests and muscle memory.
    TURN_LEFT_KEYS = (pygame.K_z, pygame.K_a, pygame.K_LEFT)
    TURN_RIGHT_KEYS = (pygame.K_x, pygame.K_d, pygame.K_RIGHT)
    def __init__(self):
        self.frames = []
        self.toads = []
        self.toad_cache = {}
        self.wall_frames = []
        self.reset()

    def reset(self, unlocked=False):
        self.active = False
        self.phase = "open" if unlocked else "closed"
        self.angle = 0 if unlocked else 3
        self.alignment = 0.0
        self.elapsed = self.OPEN_SECONDS if unlocked else 0.0
        self.time = 0.0
        self.last_can_turn = False
        self.last_tree_bleeding = False

    @property
    def reference_angle(self):
        return 0

    @property
    def light_color(self):
        return (201, 28, 38) if self.phase in ("opening", "open") else (238, 214, 148)

    @property
    def unlocked(self):
        return self.phase == "open"

    @property
    def toads_aligned(self):
        """Whether the rotating left toad matches the fixed right toad."""
        return self.angle == self.reference_angle

    @property
    def waiting_for_anomaly(self):
        """Whether the toads match but Laurel still blocks the mechanism."""
        return bool(
            self.active
            and self.phase == "closed"
            and self.last_can_turn
            and self.toads_aligned
            and not self.last_tree_bleeding
        )

    @property
    def shadow_aligned(self):
        """Backward-compatible name for older save/test helpers."""
        return self.toads_aligned

    def update(self, dt, inputs, *, can_turn=True, tree_bleeding=False):
        """Advance the direct left-toad/right-toad alignment mechanism.

        The left toad can only be checked while the player is beside it and
        Laurel is in the existing bleeding/anomaly window.  Once its facing
        matches the fixed right toad, the entrance opens directly; there is
        no separate moon-shadow or projection step.
        """
        dt = max(0, dt)
        self.time += dt
        self.last_can_turn = bool(can_turn)
        self.last_tree_bleeding = bool(tree_bleeding)
        if not self.active:
            return None
        if self.phase == "opening":
            self.elapsed = min(self.OPEN_SECONDS, self.elapsed + dt)
            if self.elapsed >= self.OPEN_SECONDS:
                self.phase = "open"
                return "opened"
            return None
        if inputs.was_pressed(config.ACTION_QUIT):
            self.active = False
            return None
        if self.unlocked:
            if inputs.was_pressed(config.ACTION_INTERACT):
                self.active = False
                return "enter"
            return None
        if inputs.was_pressed(config.ACTION_INTERACT):
            self.active = False
            return None
        turn = 0
        if can_turn and any(inputs.was_key_pressed(key) for key in self.TURN_LEFT_KEYS):
            turn -= 1
        if can_turn and any(inputs.was_key_pressed(key) for key in self.TURN_RIGHT_KEYS):
            turn += 1
        if turn:
            self.angle = (self.angle + turn) % 8
            self.alignment = 0.0
        if can_turn and tree_bleeding and self.toads_aligned:
            self.alignment += dt
        else:
            self.alignment = 0.0
        if self.alignment >= self.ALIGN_SECONDS:
            self.phase = "opening"
            self.elapsed = 0.0
            return "aligned"
        elif turn:
            return "turned"
        return None

    def _load_frames(self):
        if self.frames:
            return
        sheet = load_image(self.SHEET)
        width, height = sheet.get_width() // 2, sheet.get_height() // 2
        for row in range(2):
            for col in range(2):
                frame = sheet.subsurface((col * width, row * height, width, height))
                frame = frame.subsurface(frame.get_bounding_rect(min_alpha=32))
                self.frames.append(frame.copy())
        sheet = load_image(self.TOADS)
        width, height = sheet.get_width() // 4, sheet.get_height() // 2
        for row in range(2):
            for col in range(4):
                sprite = sheet.subsurface((col * width, row * height, width, height))
                sprite = sprite.subsurface(sprite.get_bounding_rect(min_alpha=32))
                self.toads.append(sprite.copy())

    @property
    def frame_index(self):
        return 0 if self.phase == "closed" else min(3, int(self.elapsed / .3))

    def artwork(self, scale=1):
        self._load_frames()
        width, height = (value * scale for value in self.SIZE)
        frame = pygame.transform.smoothscale(self.frames[self.frame_index], (width, height))
        cx, cy, radius = round(width * .50), round(height * .54), 9 * scale
        glow = pygame.Surface((width, height), pygame.SRCALPHA)
        brightness = round(8 * math.sin(self.time * 2.1))
        if self.phase in ("opening", "open"):
            # Light emerges through the widening interior opening, behind leaves.
            gap = (.0, .055, .09, .11)[self.frame_index]
            if gap:
                left, right = round(width * (.5 - gap)), round(width * (.5 + gap))
                for y in range(round(height * .44), round(height * .86)):
                    for x in range(left, right):
                        pixel = frame.get_at((x, y))
                        strength = 1 - abs(x - width * .5) / (width * gap + 1)
                        frame.set_at((x, y), (min(180, 58 + round(strength * 65) + pixel.r // 4),
                                              pixel.g // 5, pixel.b // 7, pixel.a))
            # Split and foreshorten the completed moon onto the moving leaves.
            # The light never floats across the dark gap after the doors open.
            inner = (.50, .445, .410, .390)[self.frame_index]
            ratio = (inner - .335) / (.50 - .335)
            lit_width = max(3 * scale, round(radius * ratio))
            for right in (False, True):
                light = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
                pygame.draw.circle(light, (*self.light_color, 175 + brightness), (radius, radius), radius)
                half = light.subsurface((radius if right else 0, 0, radius, radius * 2))
                half = pygame.transform.smoothscale(half, (lit_width, radius * 2))
                x = round(width * (1 - inner)) if right else round(width * inner) - lit_width
                glow.blit(half, (x, cy - radius))
            # A softer pool of the same lamplight catches the threshold.
            pygame.draw.ellipse(glow, (*self.light_color, 105), (28 * scale, 86 * scale, 39 * scale, 5 * scale))
        frame.blit(glow, (0, 0))
        return frame

    def toad_artwork(self, reference=False, scale=1, side=False):
        self._load_frames()
        index = ((2 if side else 4) + (self.reference_angle if reference else self.angle)) % 8
        key = (index, scale, self.light_color)
        if key in self.toad_cache:
            return self.toad_cache[key]
        source = self.toads[index]
        sprite = pygame.transform.smoothscale(source, (34 * scale, 40 * scale))
        # Tint only existing bright lantern glass pixels, preserving stone texture.
        light = pygame.Surface(sprite.get_size(), pygame.SRCALPHA)
        rgb = self.light_color
        for y in range(round(17 * scale)):
            for x in range(sprite.get_width()):
                pixel = sprite.get_at((x, y))
                if pixel.a > 80 and min(pixel.r, pixel.g, pixel.b) > 100:
                    light.set_at((x, y), (*rgb, 175))
                elif pixel.a > 80 and self.phase in ("opening", "open"):
                    light.set_at((x, y), (*rgb, 58))
        sprite.blit(light, (0, 0))
        self.toad_cache[key] = sprite
        return sprite

    def collision_rects(self):
        return [pygame.Rect(95, 198, 25, 12), pygame.Rect(54, 267, 25, 12)]

    def wall_artwork(self):
        if not self.wall_frames:
            for state in ("closed", "open"):
                source = load_image(f"sprites/moonspace/backgrounds/repair_west_{state}.png")
                source = pygame.transform.smoothscale(source, (960, 640))
                patch = source.subsurface(self.WALL_PATCH).copy().convert_alpha()
                # Blend the small scene insert into the existing floor at its edges.
                for y in range(patch.get_height()):
                    for x in range(patch.get_width()):
                        edge = min(y, patch.get_height() - 1 - y, patch.get_width() - 1 - x)
                        if edge < 12:
                            color = patch.get_at((x, y))
                            color.a = round(255 * max(0, edge) / 12)
                            patch.set_at((x, y), color)
                self.wall_frames.append(patch)
        frame = self.wall_frames[0].copy()
        if self.phase in ("opening", "open"):
            opened = self.wall_frames[1].copy()
            opened.set_alpha(round(255 * min(1, self.elapsed / self.OPEN_SECONDS)))
            frame.blit(opened, (0, 0))
        return frame

    def draw_world(self, surface, entry_rect, offset, player_rect):
        rect = entry_rect.move(offset)
        surface.blit(self.wall_artwork(), self.WALL_PATCH.move(offset))
        for reference, zone in ((False, self.LEFT_ZONE), (True, self.RIGHT_ZONE)):
            surface.blit(self.toad_artwork(reference, side=True),
                         (zone.x - 6 + offset[0], zone.y - 23 + offset[1]))
        if not self.active and player_rect.inflate(100, 80).colliderect(entry_rect):
            close = player_rect.colliderect(entry_rect)
            label = "E 进入偏殿" if close and self.unlocked else "修月偏殿"
            pygame.draw.rect(surface, (8, 12, 19), (rect.x - 42, rect.y - 20, 80, 15))
            render_text(surface, label, rect.x - 38, rect.y - 18, 11, (192, 209, 208))
        if self.LEFT_ZONE.colliderect(player_rect) and not self.unlocked and not self.active:
            x, y = 12 + offset[0], self.LEFT_ZONE.bottom + offset[1]
            pygame.draw.rect(surface, (8, 12, 19), (x, y, 78, 15))
            render_text(surface, "E 转动石蟾", x + 4, y + 2, 11, (192, 209, 208))

    def draw_active_hint(self, surface, **_kwargs):
        """Compatibility hook; the puzzle is communicated by the world."""
        _ = surface
