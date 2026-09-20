"""Moon-repair side hall: authored space, examination UI and restrained horror."""

from __future__ import annotations

import math
import random

import pygame

from core.repair_trial import RepairTrial
from utils.assets import load_image
from utils.font import render_text, render_wrapped_text, wrap_text


INK = (9, 14, 22)
JADE = (186, 204, 202)
DIM = (116, 136, 150)
BLOOD = (137, 42, 43)


class RepairHall:
    SIZE = (720, 480)
    SPAWN = (360, 316)
    BACKGROUND = "sprites/moonspace/backgrounds/repair_hall.png"
    SCARE = "sprites/moonspace/cg/repair_toad_death.png"
    ENTRY_SPRITE = "sprites/moonspace/props/repair_hall_door.png"
    FRAGMENT = "sprites/moonspace/props/repair_moon_fragment.png"
    CLOTH_ASSETS = (
        "sprites/moonspace/props/repair_cloth_yuan.png",
        "sprites/moonspace/props/repair_cloth_zhong.png",
        "sprites/moonspace/props/repair_cloth_shu.png",
    )
    # The recessed entrance belongs to the west perimeter wall.
    COURTYARD_ENTRY = pygame.Rect(55, 215, 60, 36)
    COURTYARD_RETURN = (86, 246)
    INSPECTION_DRAG_ZONE = pygame.Rect(112, 48, 256, 146)
    PIECE_NAMES = ("第壹片", "第贰片", "第叁片")
    CLOTH_MARKS = ("元", "仲", "叔")

    INTRO = [
        "来使？正好，借你一眼。",
        "这三片旧月，今夜要封。有一片裂在里头。",
        "迎着窗下月光，翻面、转动。表上有痕，未必是内裂。",
        "认定了，放到右手空盘里。斧凿莫碰，封存由我来。",
        "只给六十息。交错了，或误了封期，石像自会来验你。",
        "E 取片、查看；察验时按住月片拖动，转到背面也一样。",
        "规程与验片所见会记入手册，忘了按 Tab 回看。",
        "桌边可换片，空盘前按 E 交片。此句读毕，开始计时。",
    ]
    NOTES = {
        "repair_procedure": "偏殿验片：三片旧月中有一片内裂。带到左侧窗下迎光，翻面、转动，亲眼验见裂口后，交到右手空盘。表面擦痕和旧接缝未必是内裂。不得碰斧凿，封存由守月人完成。",
        "repair_controls": "偏殿操作：桌边按 E 取片或换片；手持月片按 E 查看，按住月片拖动可自由翻转，E/Esc 收起；空盘前按 E 正式交片。说明读毕起限六十息，查看手册也计时；错片、未验明或超时都会失败。",
    }

    def __init__(self) -> None:
        self.trial = RepairTrial()
        self.table_zone = pygame.Rect(152, 170, 110, 40)
        self.tray_zone = pygame.Rect(265, 170, 52, 40)
        self.statue_zone = pygame.Rect(475, 173, 85, 46)
        self.light_zone = pygame.Rect(72, 211, 155, 86)
        self.exit_zone = pygame.Rect(320, 301, 80, 28)
        self.background: pygame.Surface | None = None
        self.scare: pygame.Surface | None = None
        self.fragment: pygame.Surface | None = None
        self.cloth_surfaces: list[pygame.Surface] | None = None
        self.time = 0.0
        self.drip_clock = 0.0
        self.chisel_clock = 0.0
        self.drip_index = 0
        self.drop_age = 1.0
        self.message = ""
        self.message_time = 0.0
        self.seen_observations: set[str] = set()
        self.choose_piece = False
        self.piece_cursor = 0
        self.piece_order = [0, 1, 2]
        self._rng = random.Random()
        self.refresh_piece_order()
        self.sounds_played: set[str] = set()

    def reset(self, completed: bool = False) -> None:
        self.trial = RepairTrial(completed)
        self.time = self.drip_clock = self.chisel_clock = 0.0
        self.drop_age = 1.0
        self.choose_piece = False
        self.piece_cursor = 0
        self.refresh_piece_order()
        self.message = ""
        self.message_time = 0.0
        self.seen_observations.clear()
        self.sounds_played.clear()

    def refresh_piece_order(self) -> None:
        """Move every fragment identity to a new slot for this hall visit."""
        previous = tuple(self.piece_order)
        shuffled = list(previous)
        for _ in range(8):
            self._rng.shuffle(shuffled)
            if tuple(shuffled) != previous:
                break
        if tuple(shuffled) == previous:
            shuffled = shuffled[1:] + shuffled[:1]
        self.piece_order = shuffled

    @property
    def cracked_slot(self) -> int:
        return self.piece_order.index(RepairTrial.CRACKED_PIECE)

    def slot_for_piece(self, piece_index: int) -> int:
        return self.piece_order.index(piece_index)

    def selected_slot_name(self) -> str:
        if self.trial.selected is None:
            return ""
        return self.PIECE_NAMES[self.slot_for_piece(self.trial.selected)]

    def collisions(self) -> list[pygame.Rect]:
        return [pygame.Rect(0, 0, 720, 170), pygame.Rect(0, 0, 52, 480),
                pygame.Rect(665, 0, 55, 480), pygame.Rect(0, 329, 720, 151)]

    def say(self, text: str, duration: float = 3.5) -> None:
        self.message, self.message_time = text, duration

    def nearby(self, player_rect: pygame.Rect) -> str | None:
        for name in ("tray", "table", "statue", "exit", "light"):
            if getattr(self, name + "_zone").colliderect(player_rect):
                return name
        return None

    def update_ambience(self, dt: float, player_rect: pygame.Rect, audio) -> None:
        self.time += dt
        self.message_time = max(0.0, self.message_time - dt)
        self.drop_age += dt
        phase = self.trial.phase
        if phase in ("death", "sealing"):
            return
        self.drip_clock += dt
        self.chisel_clock += dt
        interval = (1.7, 2.25, 1.45, 2.8)[self.drip_index % 4]
        if self.trial.resonating:
            interval = 0.42
        if phase == "complete":
            interval = 7.0
        if self.drip_clock >= interval:
            self.drip_clock = 0.0
            self.drip_index += 1
            self.drop_age = 0.0
            distance = pygame.Vector2(player_rect.center).distance_to((505, 160))
            audio.play_spatial("repair_drip", gain=max(0.18, 1.0 - distance / 600), pan=0.3)
        if self.chisel_clock >= 3.3:
            self.chisel_clock = 0.0
            audio.play_spatial("repair_chisel", gain=0.6, pan=-0.35)

    def draw(self, surface: pygame.Surface, player, offset: tuple[int, int], *, show_hints: bool = True) -> None:
        if self.background is None:
            self.background = pygame.transform.smoothscale(load_image(self.BACKGROUND), self.SIZE)
        surface.blit(self.background, offset)
        ox, oy = offset
        self._draw_cloth_hint(surface, offset)
        if self.trial.phase == "complete":
            self.draw_piece(surface, (287 + ox, 126 + oy), 2, 0, False, False, .10)
            self._draw_seal(surface, offset)
        # A restrained moving droplet sits on the original catch basin.
        if self.drop_age < 0.34 and self.trial.phase not in ("death", "sealing"):
            y = 100 + round(35 * self.drop_age / 0.34)
            pygame.draw.line(surface, BLOOD, (505 + ox, y + oy), (505 + ox, y + oy + 3), 2)
        # A minute glint follows the worker's tool; the body stays deliberately still.
        if self.chisel_clock < 0.10 and self.trial.phase not in ("death", "sealing"):
            pygame.draw.line(surface, JADE, (226 + ox, 123 + oy), (229 + ox, 125 + oy))
        player.draw(surface, offset)
        if self.trial.phase == "sealing":
            self._draw_sealing(surface, offset)
            return
        if self.trial.phase == "death":
            self._draw_death(surface)
            return
        if self.trial.selected is not None and not self.choose_piece and not self.trial.inspecting:
            render_text(surface, self.selected_slot_name(), 12, 31, 12, JADE)
        label = self.hint(player.rect)
        if show_hints and label and not self.trial.inspecting and not self.choose_piece:
            self._strip(surface, label, 170 if self.nearby(player.rect) == "exit" else 221)
        if show_hints and self.message_time > 0 and not self.trial.inspecting and not self.choose_piece:
            self._strip(surface, self.message, 196)
        if self.choose_piece:
            self._draw_piece_selection(surface)
        elif self.trial.inspecting:
            self._draw_inspection(surface)
        if self.trial.phase == "active":
            self.draw_timer(surface)
        else:
            render_text(surface, "修月偏殿" + (" · 已封存" if self.trial.phase == "complete" else ""),
                        12, 12, 13, JADE)

    def hint(self, rect: pygame.Rect) -> str:
        target = self.nearby(rect)
        phase = self.trial.phase
        if phase == "complete":
            return "E 返回广场" if target == "exit" else "E 查看" if target in ("table", "statue") else ""
        return {
            "table": "E 与守月人交谈" if phase == "idle" else "E 取片 / 换片",
            "tray": "E 正式交片" if phase == "active" else "E 查看验盘",
            "statue": "E 查看渗血石像",
            "light": "E 迎光察看片" if self.trial.selected is not None else "",
            "exit": "" if phase == "active" else "E 返回广场",
        }.get(target, "E 察看手中月片" if self.trial.selected is not None else "")

    @staticmethod
    def _strip(surface: pygame.Surface, text: str, y: int) -> None:
        rect = pygame.Rect(12, y, 456, 29)
        pygame.draw.rect(surface, INK, rect)
        pygame.draw.line(surface, (64, 77, 88), rect.topleft, rect.topright)
        render_wrapped_text(surface, wrap_text(text, 35)[:2], 20, y + 5, 12, JADE, 13)

    def draw_timer(self, surface: pygame.Surface) -> None:
        remaining = math.ceil(self.trial.remaining)
        pygame.draw.rect(surface, INK, (302, 8, 166, 34))
        color = BLOOD if remaining <= 15 else JADE
        render_text(surface, f"封期  {remaining:02d} / 60 息", 312, 13, 14, color)
        pygame.draw.rect(surface, (38, 48, 59), (312, 33, 144, 3))
        pygame.draw.rect(surface, color, (312, 33, round(144 * self.trial.remaining / 60), 3))

    def _draw_piece_selection(self, surface: pygame.Surface) -> None:
        pygame.draw.rect(surface, INK, (34, 54, 412, 151))
        pygame.draw.rect(surface, DIM, (34, 54, 412, 151), 1)
        render_text(surface, "待封旧月 · 选择一片取起", 58, 65, 15, JADE)
        for i in range(3):
            center = (110 + i * 130, 123)
            # All three candidates look sound on the tray.  Their actual
            # identities are assigned only after the slot is chosen.
            self.draw_piece(surface, center, -1, 0, False, False, 0.5)
            if self.piece_cursor == i:
                pygame.draw.rect(surface, JADE, (center[0] - 47, 92, 94, 77), 1)
            render_text(surface, self.PIECE_NAMES[i], center[0] - 18, 147, 13, JADE)
        render_text(surface, "A D / ← → 选择    E 取起    Esc 收起", 69, 181, 12, DIM)

    def _draw_cloth_hint(self, surface: pygame.Surface, offset: tuple[int, int]) -> None:
        """Replace the authored cloth with the embroidered clue for this visit."""
        ox, oy = offset
        if self.cloth_surfaces is None:
            self.cloth_surfaces = [
                pygame.transform.smoothscale(load_image(path), (38, 52))
                for path in self.CLOTH_ASSETS
            ]
        surface.blit(self.cloth_surfaces[self.cracked_slot], (148 + ox, 126 + oy))

    def observe_piece(self) -> tuple[str, str] | None:
        """Record each discovered observation for Tab without overlay narration."""
        trial = self.trial
        if not trial.inspecting or trial.selected is None:
            return None
        if not trial.in_light:
            key, text = "dark", "光线太暗。把月片带到左侧窗下，再迎光查看。"
        elif trial.selected == 0:
            key, text = "surface", "表面擦痕随光一闪，透过去，内部仍是完整的。"
        elif trial.selected == 1:
            if trial.back:
                key, text = "seam_back", "背面露出一道旧接缝，两侧已经紧紧合住。"
            else:
                key, text = "seam_front", "一道细线藏在玉里。翻到背面，能看得更清楚。"
        elif trial.resonating:
            key, text = "crack", "透光处露出一小块崩口，暗面藏在玉纹里。石像那边的滴落忽然密了。"
        else:
            key, text = "shadow", "里面像有一处阴影。缓缓转动，让月光透过去。"
        if key in self.seen_observations:
            return None
        self.seen_observations.add(key)
        title = "验片" if key == "dark" else self.selected_slot_name()
        return "repair_observation_" + key, title + "：" + text

    def _draw_inspection(self, surface: pygame.Surface) -> None:
        shade = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        shade.fill((4, 8, 14, 248))
        surface.blit(shade, (0, 0))
        trial = self.trial
        render_text(surface, "迎光察验" if trial.in_light else "背光察验", 24, 17, 15, JADE)
        render_text(surface, "背面" if trial.back else "正面", 24, 42, 12, DIM)
        self._draw_rotating_piece(surface, (240, 121))

    def draw_piece(self, surface, center, index, angle, back, light, scale=1.0) -> None:
        """Render a static fragment for selection, sealing, and world props."""
        piece = self._piece_surface(index, back, light, 0.0, 0.0, 0.0)
        if back:
            piece = pygame.transform.flip(piece, True, False)
        rotated = pygame.transform.rotozoom(piece, -angle * 45, scale)
        if scale >= 1 and rotated.get_height() > 146:
            ratio = 146 / rotated.get_height()
            rotated = pygame.transform.smoothscale(rotated, (round(rotated.get_width() * ratio), 146))
        surface.blit(rotated, rotated.get_rect(center=center))

    def _piece_surface(
        self,
        index: int,
        back: bool,
        light: bool,
        reveal: float,
        yaw: float,
        pitch: float,
    ) -> pygame.Surface:
        """Compose surface marks, inner fracture, and orientation-driven jade lighting."""
        if self.fragment is None:
            self.fragment = pygame.transform.smoothscale(load_image(self.FRAGMENT), (180, 124))
        piece = self.fragment.copy()
        normal = RepairTrial._normal_for(yaw, pitch)
        visible_normal = tuple(-value for value in normal) if back else normal
        light_normal = RepairTrial._normal_for(RepairTrial.LIGHT_YAW, RepairTrial.LIGHT_PITCH)
        diffuse = max(0.0, sum(a * b for a, b in zip(visible_normal, light_normal))) if light else 0.0
        facing = abs(normal[2])
        tint = (
            (round(143 + 67 * diffuse), round(168 + 66 * diffuse), round(157 + 59 * diffuse), 255)
            if light else (108, 130, 125, 255)
        )
        piece.fill(tint, special_flags=pygame.BLEND_RGBA_MULT)

        marks = pygame.Surface(piece.get_size(), pygame.SRCALPHA)
        if index == 0 and not back:
            pygame.draw.lines(marks, (184, 199, 188, 190), False,
                              [(66, 82), (79, 85), (91, 91), (106, 94)], 1)
        elif index == 1:
            seam_color = (153, 139, 98, 210) if back else (136, 156, 149, 205)
            pygame.draw.lines(marks, seam_color, False,
                              [(64, 67), (80, 76), (75, 87), (91, 94), (104, 102)], 2)
            pygame.draw.line(marks, (162, 151, 112, 70), (80, 76), (75, 87), 1)
        piece.blit(marks, (0, 0))

        alpha_mask = self.fragment.copy()
        alpha_mask.fill((255, 255, 255, 255), special_flags=pygame.BLEND_RGBA_MULT)
        if light:
            # Project the fixed window light into the fragment's local plane.
            # It changes diffuse shading and the specular lobe; no decorative
            # bands are attached to the texture.
            light_u = math.sin(math.radians(RepairTrial.LIGHT_YAW - yaw))
            light_v = -math.sin(math.radians(RepairTrial.LIGHT_PITCH - pitch))
            shade_small = pygame.Surface((45, 31), pygame.SRCALPHA)
            for x in range(shade_small.get_width()):
                for y in range(shade_small.get_height()):
                    u = x / max(1, shade_small.get_width() - 1) - 0.5
                    v = y / max(1, shade_small.get_height() - 1) - 0.5
                    away_from_light = max(0.0, -(u * light_u + v * light_v))
                    alpha = round(away_from_light * (34 + 24 * (1.0 - diffuse)))
                    if alpha:
                        shade_small.set_at((x, y), (7, 18, 17, alpha))
            shade = pygame.transform.smoothscale(shade_small, piece.get_size())
            shade.blit(alpha_mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            piece.blit(shade, (0, 0))

            view_normal = (0.0, 0.0, 1.0)
            half_vector = tuple(a + b for a, b in zip(light_normal, view_normal))
            half_length = math.sqrt(sum(value * value for value in half_vector))
            half_vector = tuple(value / half_length for value in half_vector)
            specular = max(0.0, sum(a * b for a, b in zip(visible_normal, half_vector))) ** 18
            highlight_small = pygame.Surface((45, 31), pygame.SRCALPHA)
            highlight_center = (
                round(22 + light_u * 13),
                round(15 + light_v * 9),
            )
            for radius in range(10, 0, -1):
                falloff = 1.0 - radius / 11.0
                alpha = round(specular * (8 + 62 * falloff))
                pygame.draw.ellipse(
                    highlight_small,
                    (151, 196, 178, alpha),
                    (highlight_center[0] - radius * 2, highlight_center[1] - radius,
                     radius * 4, radius * 2),
                )
            highlight = pygame.transform.smoothscale(highlight_small, piece.get_size())
            highlight.blit(alpha_mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            piece.blit(highlight, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)

            outline = pygame.mask.from_surface(self.fragment, 12).outline()
            if len(outline) > 2:
                rim = pygame.Surface(piece.get_size(), pygame.SRCALPHA)
                rim_alpha = round(10 + 48 * (1.0 - facing) + 18 * diffuse)
                pygame.draw.lines(rim, (157, 205, 184, rim_alpha), True, outline, 1)
                piece.blit(rim, (0, 0))

        if light and index == RepairTrial.CRACKED_PIECE and reveal > 0.0:
            shift_x = round(math.sin(math.radians(yaw)) * 3.0)
            shift_y = round(math.sin(math.radians(pitch)) * 2.0)
            # Shade a shallow concavity from local surface normals.  The two
            # opposing half-rims make it read as displaced jade instead of a
            # flat stain or an outlined symbol.
            flaw_visibility = reveal ** 3.0
            cx, cy = 103 + shift_x, 72 + shift_y
            radius_x, radius_y = 8.5, 6.0
            for py in range(cy - 7, cy + 8):
                for px in range(cx - 10, cx + 11):
                    nx = (px - cx) / radius_x
                    ny = (py - cy) / radius_y
                    angle = math.atan2(ny, nx)
                    irregular_edge = 1.0 + 0.07 * math.sin(angle * 3.0 + 0.8) + 0.035 * math.sin(angle * 5.0)
                    radial = math.sqrt(nx * nx + ny * ny) / irregular_edge
                    if radial >= 1.0:
                        continue
                    rim = math.exp(-((radial - 0.73) / 0.24) ** 2)
                    # Window light comes from the upper left.  On a concavity
                    # it catches the lower-right inner wall and shades the
                    # opposite wall, the inverse cue of a raised bump.
                    local_light = nx * 0.62 + ny * 0.78
                    edge_fade = min(1.0, max(0.0, (1.0 - radial) * 5.0))
                    shade = local_light * rim * 0.34 - (1.0 - radial) * 0.055
                    shade *= flaw_visibility * edge_fade
                    base = piece.get_at((px, py))
                    if base.a <= 12:
                        continue
                    warmth = max(0.0, local_light) * rim * flaw_visibility
                    piece.set_at(
                        (px, py),
                        (
                            max(0, min(255, round(base.r * (1.0 + shade) + 5.0 * warmth))),
                            max(0, min(255, round(base.g * (1.0 + shade) + 10.0 * warmth))),
                            max(0, min(255, round(base.b * (1.0 + shade) + 6.0 * warmth))),
                            base.a,
                        ),
                    )
        return piece

    def _draw_rotating_piece(self, surface: pygame.Surface, center: tuple[int, int]) -> None:
        """Project the flat jade layer as a freely rotated, slightly thick shard."""
        trial = self.trial
        yaw_radians = math.radians(trial.yaw)
        pitch_radians = math.radians(trial.pitch)
        cos_yaw = math.cos(yaw_radians)
        cos_pitch = math.cos(pitch_radians)
        piece = self._piece_surface(
            trial.selected or 0,
            trial.back,
            trial.in_light,
            trial.reveal_strength if trial.selected == RepairTrial.CRACKED_PIECE else 0.0,
            trial.yaw,
            trial.pitch,
        )
        if cos_yaw < 0:
            piece = pygame.transform.flip(piece, True, False)
        if cos_pitch < 0:
            piece = pygame.transform.flip(piece, False, True)
        width = max(9, round(piece.get_width() * abs(cos_yaw)))
        height = max(9, round(piece.get_height() * abs(cos_pitch)))
        projected = pygame.transform.smoothscale(piece, (width, height))
        roll = math.sin(yaw_radians) * math.sin(pitch_radians) * 12.0
        projected = pygame.transform.rotozoom(projected, -roll, 1.0)

        edge_on = 1.0 - abs(trial.normal[2])
        edge_depth = 3 + round(13 * edge_on)
        extrusion = pygame.Vector2(math.sin(yaw_radians), math.sin(pitch_radians) * 0.65)
        if extrusion.length_squared() < 0.01:
            extrusion.update(1.0, 0.0)
        else:
            extrusion = extrusion.normalize()

        side = projected.copy()
        side.fill((103, 143, 128, 255), special_flags=pygame.BLEND_RGBA_MULT)
        far_rim = projected.copy()
        far_rim.fill((139, 177, 157, 255), special_flags=pygame.BLEND_RGBA_MULT)
        for depth in range(edge_depth, 0, -1):
            offset = extrusion * depth
            side_rect = side.get_rect(center=(center[0] + round(offset.x), center[1] + round(offset.y)))
            surface.blit(far_rim if depth == edge_depth else side, side_rect)
        surface.blit(projected, projected.get_rect(center=center))

    @staticmethod
    def _draw_seal(surface: pygame.Surface, offset: tuple[int, int]) -> None:
        # A narrow paper seal lies across the textured tray already in the room art.
        x, y = 287 + offset[0], 125 + offset[1]
        pygame.draw.polygon(surface, (174, 175, 154), [(x-2,y-6),(x+2,y-5),(x+3,y+9),(x-2,y+8)])
        pygame.draw.line(surface, (74, 67, 53), (x-1,y-5), (x-1,y+7))
        pygame.draw.rect(surface, BLOOD, (x, y, 2, 3))

    def _draw_sealing(self, surface: pygame.Surface, offset: tuple[int, int]) -> None:
        t = self.trial.elapsed
        captions = ["守月人接过旧月，将裂片压进验盘。", "滴血声停了。", "封条尚未落下，盘底先响了一凿。", "他停了一瞬，把封条压实。"]
        self._strip(surface, captions[min(3, int(t / 1.4))], 207)
        self.draw_piece(surface, (287 + offset[0], 126 + offset[1]), 2, 0, False, False, .10)
        if t > 3.8:
            self._draw_seal(surface, offset)

    def _draw_death(self, surface: pygame.Surface) -> None:
        t = self.trial.elapsed
        if t < .24:
            if self.trial.death_reason == "超时":
                caption = "封期已误。"
            elif self.trial.death_reason == "未验":
                caption = "你还没有验见裂口。"
            else:
                caption = "错验。封存开始。"
            self._strip(surface, caption, 207)
            return
        if self.scare is None:
            self.scare = pygame.transform.smoothscale(load_image(self.SCARE), surface.get_size())
        if t < 1.58:
            self._draw_scare_lunge(surface, t - .24)
        else:
            surface.fill((0, 0, 0))
            title = {
                "错片": "错验旧月",
                "未验": "裂口未验",
                "超时": "封期已误",
            }.get(self.trial.death_reason, "验片失败")
            render_text(surface, title, 200, 112, 19, BLOOD)
            render_text(surface, "返回最近的存档点", 183, 150, 13, JADE)

    def _draw_scare_lunge(self, surface: pygame.Surface, elapsed: float) -> None:
        """Make the toad feel like it crossed the room, not like a static CG."""
        # A hard first snap is more legible as a scare than a slow uniform zoom.
        snap = min(1.0, elapsed / .34)
        if snap < .58:
            eased = (snap / .58) ** 0.42
            zoom = .92 + .90 * eased
        else:
            settle = (snap - .58) / .42
            zoom = 1.82 - .10 * settle
        breathing = math.sin(elapsed * 25.0) * .025 if elapsed > .34 else 0.0
        zoom += breathing

        # The image overshoots in alternating directions so the face lands
        # with a physical jolt instead of simply scaling in the centre.
        shake = max(0.0, 1.0 - elapsed / .52)
        jitter_x = round(math.sin(elapsed * 74.0) * 7.0 * shake)
        jitter_y = round(math.sin(elapsed * 91.0 + 1.8) * 4.0 * shake)
        width = round(480 * zoom)
        height = round(270 * zoom)
        frame = pygame.transform.smoothscale(self.scare, (width, height))
        # Drop the face a little as it lands so the eyes remain in frame while
        # the mouth still crowds the lower half of the screen.
        frame_rect = frame.get_rect(center=(240 + jitter_x, 145 + jitter_y))
        surface.blit(frame, frame_rect)

        # Blood-red eye reflections appear only after the mouth has landed.
        # They are drawn in the same transformed coordinate space as the face.
        if elapsed > .22:
            eye_layer = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
            eye_alpha = round(25 + 105 * min(1.0, (elapsed - .22) / .28))
            pulse = 1.0 + .14 * math.sin(elapsed * 31.0)
            eye_radius = max(2, round(7 * zoom * pulse))
            for eye_x in (.337, .664):
                point = (
                    round(frame_rect.left + width * eye_x),
                    round(frame_rect.top + height * .207),
                )
                pygame.draw.circle(eye_layer, (178, 20, 24, eye_alpha // 3), point, eye_radius * 2)
                pygame.draw.circle(eye_layer, (220, 37, 35, eye_alpha), point, eye_radius)
                pygame.draw.circle(eye_layer, (255, 214, 190, min(220, eye_alpha + 45)),
                                   (point[0] - max(1, eye_radius // 3), point[1] - max(1, eye_radius // 3)),
                                   max(1, eye_radius // 3))
            surface.blit(eye_layer, (0, 0))

        # The first impact is a cold flash, then the room falls into blood
        # red.  The final darkening preserves the silhouette for a beat.
        if elapsed < .12:
            flash = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
            flash.fill((205, 224, 219, round(105 * (1.0 - elapsed / .12))))
            surface.blit(flash, (0, 0))
        red_alpha = round(22 + 36 * min(1.0, max(0.0, (elapsed - .28) / .55)))
        red = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        red.fill((105, 0, 8, red_alpha))
        surface.blit(red, (0, 0))

        # Four restrained edge scratches sell the impact without covering the
        # asset's mouth and eyes with a decorative frame.
        if elapsed > .42:
            scratch = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
            strength = round(70 * min(1.0, (elapsed - .42) / .25))
            pygame.draw.line(scratch, (221, 187, 157, strength), (0, 30), (72, 0), 1)
            pygame.draw.line(scratch, (221, 187, 157, strength), (480, 235), (418, 270), 1)
            pygame.draw.line(scratch, (130, 28, 32, strength), (0, 230), (54, 270), 2)
            pygame.draw.line(scratch, (130, 28, 32, strength), (480, 42), (446, 0), 2)
            surface.blit(scratch, (0, 0))
