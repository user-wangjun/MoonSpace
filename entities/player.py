"""玩家实体：移动、朝向、动画和基础碰撞。"""

from __future__ import annotations

import pygame

import config
from core.input_manager import InputManager
from utils import palette
from utils.assets import load_sprite_grid
from utils.pixel_art import draw_pixel_data


class Player:
    """玩家角色，使用 AABB 碰撞和代码像素绘制保持逻辑简单可测。"""

    VALID_FACINGS = {"up", "down", "left", "right"}
    REFLECTION_FACING = {"up": "down", "down": "up", "left": "right", "right": "left"}

    def __init__(self, x: float = config.PLAYER_START_X, y: float = config.PLAYER_START_Y) -> None:
        self.position = pygame.Vector2(x, y)
        self.velocity = pygame.Vector2(0, 0)
        self.rect = pygame.Rect(int(x), int(y), *config.PLAYER_SIZE)
        self.facing = "down"
        self.anim_state = "idle"
        self.current_frame = 0
        self._animation_timer = 0.0
        self._interact_timer = 0.0
        self._normalized_sprite_cache: dict[tuple[str, int], pygame.Surface] = {}

    def update(
        self,
        dt: float,
        input_manager: InputManager,
        collision_rects: list[pygame.Rect] | tuple[pygame.Rect, ...],
        world_size: tuple[int, int] = (config.MAP_WIDTH, config.MAP_HEIGHT),
    ) -> None:
        """读取输入、更新动画并执行按轴分离的矩形碰撞。"""
        dt = max(0.0, dt)
        if self._interact_timer > 0:
            self._interact_timer = max(0.0, self._interact_timer - dt)

        direction = self._get_input_direction(input_manager)
        speed = (
            config.PLAYER_RUN_SPEED
            if input_manager.is_pressed(config.ACTION_RUN)
            else config.PLAYER_WALK_SPEED
        )
        self.velocity = direction * speed

        if direction.length_squared() > 0:
            self._update_facing(direction)
            self.anim_state = "walk" if self._interact_timer <= 0 else "interact"
        elif self._interact_timer > 0:
            self.anim_state = "interact"
        else:
            self.anim_state = "idle"

        self._move_and_collide(dt, collision_rects)
        self._clamp_to_world(world_size)
        if not self.is_moving() and self._interact_timer <= 0:
            self.anim_state = "idle"
        self._update_animation(dt)

    def draw(
        self,
        surface: pygame.Surface,
        camera_offset: tuple[int, int] = (0, 0),
        *,
        alpha: int = 255,
    ) -> None:
        """绘制伪装使者，优先使用项目大尺寸 PNG 精灵。"""
        x = int(self.rect.x + camera_offset[0])
        y = int(self.rect.y + camera_offset[1])
        try:
            sprite = self.get_current_sprite()
        except (FileNotFoundError, pygame.error, ValueError):
            sprite = None

        if sprite is not None:
            if alpha < 255:
                sprite = sprite.copy()
                sprite.set_alpha(alpha)
            surface.blit(sprite, (self.rect.centerx + camera_offset[0] - sprite.get_width() // 2, self.rect.bottom + camera_offset[1] - sprite.get_height()))
            return

        draw_pixel_data(
            surface,
            self._pixel_frame(),
            {
                "H": palette.SKIN_PALE,
                "R": palette.PLAYER_ROBE,
                "D": palette.DEEP_BLUE,
                "M": palette.MOON_WHITE,
                "G": palette.PALE_MOON,
                "K": palette.BLACK,
            },
            x,
            y,
        )

    def is_moving(self) -> bool:
        """返回玩家当前是否有非零速度。"""
        return self.velocity.length_squared() > 0

    def trigger_interact_animation(self) -> None:
        """触发短交互动画，供 NPC 或告示牌交互时调用。"""
        self._interact_timer = 0.35
        self.anim_state = "interact"
        self.current_frame = 0
        self._animation_timer = 0.0

    def get_current_sprite(self, facing_override: str | None = None) -> pygame.Surface:
        """返回当前 PNG 帧；倒影可指定异常朝向而不修改玩家状态。"""
        if facing_override is not None and facing_override not in self.VALID_FACINGS:
            raise ValueError(f"invalid facing override: {facing_override}")
        return self._sprite_frame(facing_override)

    def get_reflection_sprite(self) -> pygame.Surface:
        """返回朝向观察者的镜像源帧，随后由水面执行垂直翻转。"""
        return self.get_current_sprite(self.REFLECTION_FACING[self.facing])

    def _get_input_direction(self, input_manager: InputManager) -> pygame.Vector2:
        """把输入动作转换成归一化方向，避免斜向移动更快。"""
        direction = pygame.Vector2(0, 0)
        if input_manager.is_pressed(config.ACTION_MOVE_UP):
            direction.y -= 1
        if input_manager.is_pressed(config.ACTION_MOVE_DOWN):
            direction.y += 1
        if input_manager.is_pressed(config.ACTION_MOVE_LEFT):
            direction.x -= 1
        if input_manager.is_pressed(config.ACTION_MOVE_RIGHT):
            direction.x += 1

        if direction.length_squared() > 0:
            direction = direction.normalize()
        return direction

    def _update_facing(self, direction: pygame.Vector2) -> None:
        """根据主方向更新朝向，朝向后续会参与规则判定。"""
        if abs(direction.x) > abs(direction.y):
            self.facing = "right" if direction.x > 0 else "left"
        elif direction.y != 0:
            self.facing = "down" if direction.y > 0 else "up"

    def _move_and_collide(
        self,
        dt: float,
        collision_rects: list[pygame.Rect] | tuple[pygame.Rect, ...],
    ) -> None:
        """按 X/Y 轴分离移动，并用扫掠检测避免低帧率时穿墙。"""
        for axis in ("x", "y"):
            old_rect = self.get_collision_rect()
            intended = getattr(self.position, axis) + getattr(self.velocity, axis) * dt
            setattr(self.position, axis, intended)
            setattr(self.rect, axis, round(intended))
            blocked = self._resolve_axis_collision(collision_rects, axis, old_rect)
            resolved = getattr(self.rect, axis)
            if blocked or resolved != round(intended):
                setattr(self.position, axis, float(resolved))
                setattr(self.velocity, axis, 0.0)

    def get_collision_rect(self) -> pygame.Rect:
        """脚底占地与显示/存档矩形分离，头身可以遮挡背景物体。"""
        footprint = pygame.Rect(0, 0, self.rect.width, 10)
        footprint.midbottom = self.rect.midbottom
        return footprint

    def _resolve_axis_collision(
        self,
        collision_rects: list[pygame.Rect] | tuple[pygame.Rect, ...],
        axis: str,
        old_rect: pygame.Rect,
    ) -> bool:
        """解决当前轴碰撞；即使一步跨过障碍，也会停在障碍边缘。"""
        blocked = False
        footprint = self.get_collision_rect()
        for obstacle in collision_rects:
            if axis == "x":
                overlaps_y = footprint.bottom > obstacle.top and footprint.top < obstacle.bottom
                if not overlaps_y:
                    continue
                if self.velocity.x > 0 and old_rect.right <= obstacle.left <= footprint.right:
                    footprint.right = obstacle.left
                    blocked = True
                elif self.velocity.x < 0 and footprint.left <= obstacle.right <= old_rect.left:
                    footprint.left = obstacle.right
                    blocked = True
                elif footprint.colliderect(obstacle):
                    if self.velocity.x > 0:
                        footprint.right = obstacle.left
                        blocked = True
                    elif self.velocity.x < 0:
                        footprint.left = obstacle.right
                        blocked = True
            else:
                overlaps_x = footprint.right > obstacle.left and footprint.left < obstacle.right
                if not overlaps_x:
                    continue
                if self.velocity.y > 0 and old_rect.bottom <= obstacle.top <= footprint.bottom:
                    footprint.bottom = obstacle.top
                    blocked = True
                elif self.velocity.y < 0 and footprint.top <= obstacle.bottom <= old_rect.top:
                    footprint.top = obstacle.bottom
                    blocked = True
                elif footprint.colliderect(obstacle):
                    if self.velocity.y > 0:
                        footprint.bottom = obstacle.top
                        blocked = True
                    elif self.velocity.y < 0:
                        footprint.top = obstacle.bottom
                        blocked = True

        self.rect.midbottom = footprint.midbottom
        return blocked

    def _clamp_to_world(self, world_size: tuple[int, int] = (config.MAP_WIDTH, config.MAP_HEIGHT)) -> None:
        """限制玩家不离开地图边界。"""
        for axis, limit in (("x", world_size[0] - self.rect.width), ("y", world_size[1] - self.rect.height)):
            value = getattr(self.position, axis)
            clamped = max(0.0, min(float(limit), value))
            if clamped != value:
                setattr(self.position, axis, clamped)
                setattr(self.velocity, axis, 0.0)
            setattr(self.rect, axis, round(clamped))

    def _update_animation(self, dt: float) -> None:
        """根据动画状态推进帧号。"""
        fps_by_state = {
            "idle": config.IDLE_ANIMATION_FPS,
            "walk": config.WALK_ANIMATION_FPS,
            "interact": config.INTERACT_ANIMATION_FPS,
        }
        frame_count_by_state = {"idle": 2, "walk": 4, "interact": 2}
        fps = fps_by_state[self.anim_state]
        frame_count = frame_count_by_state[self.anim_state]

        self._animation_timer += dt
        frame_duration = 1.0 / fps
        while self._animation_timer >= frame_duration:
            self._animation_timer -= frame_duration
            self.current_frame = (self.current_frame + 1) % frame_count

    def _pixel_frame(self) -> list[str]:
        """返回 16×24 伪装使者像素帧，保持碰撞尺寸稳定。"""
        raised = self.anim_state == "interact" and self.current_frame % 2 == 1
        step = self.anim_state == "walk" and self.current_frame % 2 == 1
        breathe = self.anim_state == "idle" and self.current_frame % 2 == 1

        if self.facing == "up":
            face_row = "     KHHHHK     "
            hair_row = "     KKKKKK     "
        elif self.facing == "left":
            face_row = "     KHHHMK     "
            hair_row = "     KKKKK      "
        elif self.facing == "right":
            face_row = "     KMHHHK     "
            hair_row = "      KKKKK     "
        else:
            face_row = "     KHMHMK     "
            hair_row = "     KKKKKK     "

        left_arm = "M" if raised else "R"
        right_arm = "R" if raised else "M"
        robe_mid = "RRRRRR" if not breathe else "RRRRR "
        left_foot = "D" if step else "R"
        right_foot = "R" if step else "D"

        rows = [
            "                ",
            "      KKKK      ",
            hair_row,
            face_row,
            "      HHHH      ",
            "      GGGG      ",
            f"    {left_arm}{robe_mid}{right_arm}    ",
            "   MRRRRRRM     ",
            "   RRGGGRRR     ",
            "   RRRDRRRR     ",
            "    RRRRRR      ",
            "    RRRRRR      ",
            "    RRRRRR      ",
            "    RRGGRR      ",
            "    RRRRRR      ",
            "    RRRRRR      ",
            "    RRRRRR      ",
            "    RRRRRR      ",
            "    RRRRRR      ",
            "    MRRRRM      ",
            f"    {left_foot}RRR{right_foot}       ",
            f"    {left_foot}   {right_foot}       ",
            "                ",
            "                ",
        ]
        return [row[:16].ljust(16) for row in rows]

    def _sprite_frame(self, facing_override: str | None = None) -> pygame.Surface:
        """返回当前朝向和动画状态对应的 PNG 精灵帧。"""
        facing = facing_override or self.facing
        try:
            rows = load_sprite_grid("sprites/moonspace/player_envoy_large.png", 42, 62, 4, 4)
        except (FileNotFoundError, pygame.error, ValueError):
            raise FileNotFoundError("player_envoy_large.png is unavailable") from None

        row = {"down": 0, "up": 1, "left": 2, "right": 3}[facing]
        col = self.current_frame % 4 if self.anim_state == "walk" else 0
        if self.anim_state == "interact":
            col = 1
        cache_key = (facing, col)
        if cache_key not in self._normalized_sprite_cache:
            # The authored canvas may change; the on-screen body remains 60px
            # high with a stable foot anchor in every direction and walk phase.
            target_height = 60
            normalized_row = self._normalize_sprite_row(rows[row], target_height)
            self._normalized_sprite_cache.update(
                {(facing, index): frame for index, frame in enumerate(normalized_row)}
            )
        return self._normalized_sprite_cache[cache_key]

    @staticmethod
    def _normalize_sprite_row(row: list[pygame.Surface], target_height: int) -> list[pygame.Surface]:
        """统一精灵表各动画帧的可见身高和脚底锚点。"""
        normalized_row = []
        for frame in row:
            bounds = frame.get_bounding_rect(min_alpha=1)
            if bounds.width <= 0 or bounds.height <= 0:
                normalized_row.append(frame.copy())
                continue

            content = frame.subsurface(bounds).copy()
            target_width = max(1, round(content.get_width() * target_height / bounds.height))
            content = pygame.transform.smoothscale(content, (target_width, target_height))
            normalized = pygame.Surface(frame.get_size(), pygame.SRCALPHA)
            normalized.blit(
                content,
                (
                    (frame.get_width() - target_width) // 2,
                    frame.get_height() - target_height,
                ),
            )
            normalized_row.append(normalized)
        return normalized_row
