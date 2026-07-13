"""Home/tutorial scene before the formal Moon Palace courtyard."""

from __future__ import annotations

import pygame

import config
from core.event_bus import DIALOG_ACTIVE_CHANGED, SHOW_DIALOG, EventBus
from core.game_state import GameState
from utils import palette
from utils.assets import load_image
from utils.pixel_art import draw_double_rect, draw_filled_rect
from world.sign_board import BASIC_RULES


HOME_PLAYER_START_X = 472
HOME_PLAYER_START_Y = 458


class HomeTutorialScene:
    """Playable arrival area that teaches movement, interaction, and facing rules."""

    SIGN_DIALOG_LINES = [
        "月宫把你记成凌霄来使；想回到地球，必须按它的规条活到门开。",
        "四条规条已经刻入手册：树、兔、池水，以及会流泪的月桂。",
        *[f"规条：{rule_text}" for rule_text in BASIC_RULES.values()],
        "方法：不要让角色正面朝向正在捣药的玉兔。",
        "操作：用 W/A/S/D 或方向键转身、绕开；Tab 可以随时打开规则手册。",
        "读完所有规条后，月宫大门便会开启。",
    ]

    def __init__(self, event_bus: EventBus) -> None:
        self.event_bus = event_bus
        self.sign_read = False
        self.rules_briefing_complete = False
        # 保留旧存档字段兼容性；练习步骤已经移除。
        self.practice_done = True
        self.event_bus.subscribe(DIALOG_ACTIVE_CHANGED, self._on_dialog_active_changed)
        self.sign_rect = pygame.Rect(423, 295, 116, 38)
        self.sign_interaction_rect = self.sign_rect.inflate(46, 34)
        self.shadow_rect = pygame.Rect(710, 270, 34, 48)
        self.rabbit_enclosure_rect = pygame.Rect(666, 214, 152, 112)
        self.left_cliff_rect = pygame.Rect(0, 166, 72, config.MAP_HEIGHT - 166)
        self.right_cliff_rect = pygame.Rect(888, 166, 72, config.MAP_HEIGHT - 166)
        self.left_lantern_rect = pygame.Rect(101, 185, 34, 58)
        self.right_lantern_rect = pygame.Rect(825, 185, 34, 58)
        self.gate_trigger_rect = pygame.Rect(398, 96, 164, 36)
        self.altar_rect = pygame.Rect(402, 436, 156, 72)

    @property
    def gate_open(self) -> bool:
        """Return whether the Moon Palace gate can be entered."""
        return self.sign_read and self.rules_briefing_complete

    def apply_save_data(self, data: dict) -> None:
        """Restore partial tutorial progress from save data."""
        tutorial_data = data.get("home_tutorial", data)
        self.sign_read = bool(tutorial_data.get("sign_read", False))
        self.rules_briefing_complete = bool(tutorial_data.get("rules_briefing_complete", self.sign_read))
        self.practice_done = True

    def collect_save_data(self) -> dict:
        """Return partial tutorial progress for save data."""
        return {
            "sign_read": self.sign_read,
            "rules_briefing_complete": self.rules_briefing_complete,
            "practice_done": True,
        }

    def basic_rule_lines(self) -> list[str]:
        """Return the base rules shown before the practice prompt."""
        return list(BASIC_RULES.values())

    def read_sign(self, game_state: GameState) -> bool:
        """Read the home sign, discover base rules, and show operation guidance."""
        first_read = not self.sign_read
        self.sign_read = True
        if first_read:
            self.rules_briefing_complete = False
        for rule_id, rule_text in BASIC_RULES.items():
            game_state.add_known_rule(rule_id, rule_text)
        self.event_bus.emit(
            SHOW_DIALOG,
            speaker_id="home_sign",
            lines=list(self.SIGN_DIALOG_LINES),
        )
        return first_read

    def is_gate_entered(self, player_rect: pygame.Rect) -> bool:
        """Return True when the opened gate trigger is reached."""
        return self.gate_open and self.gate_trigger_rect.colliderect(player_rect)

    def update(self, dt: float, input_manager, player, game_state: GameState) -> None:
        """Handle sign interaction."""
        _ = dt
        if input_manager.was_pressed(config.ACTION_INTERACT) and self.sign_interaction_rect.colliderect(player.rect):
            self.read_sign(game_state)

    def draw(self, surface: pygame.Surface, camera_offset: tuple[int, int] = (0, 0)) -> None:
        """Draw the home/tutorial map and state markers."""
        background_path = (
            "sprites/moonspace/home_tutorial_bg_open.png"
            if self.gate_open
            else "sprites/moonspace/home_tutorial_bg.png"
        )
        try:
            background = load_image(background_path)
        except (FileNotFoundError, pygame.error):
            background = None

        if background is not None:
            surface.blit(background, camera_offset)
        else:
            self._draw_fallback(surface, camera_offset)

    def get_collision_rects(self) -> list[pygame.Rect]:
        """Return solid props and a sealed north façade with only the open gate corridor."""
        collisions = [
            self.sign_rect.copy(),
            self.rabbit_enclosure_rect.copy(),
            self.left_cliff_rect.copy(),
            self.right_cliff_rect.copy(),
            self.left_lantern_rect.copy(),
            self.right_lantern_rect.copy(),
        ]
        wall_bottom = 166
        if not self.gate_open:
            collisions.append(pygame.Rect(0, 0, config.MAP_WIDTH, wall_bottom))
        else:
            collisions.extend(
                [
                    pygame.Rect(0, 0, self.gate_trigger_rect.left, wall_bottom),
                    pygame.Rect(
                        self.gate_trigger_rect.right,
                        0,
                        config.MAP_WIDTH - self.gate_trigger_rect.right,
                        wall_bottom,
                    ),
                    pygame.Rect(
                        self.gate_trigger_rect.left,
                        0,
                        self.gate_trigger_rect.width,
                        self.gate_trigger_rect.top,
                    ),
                ]
            )
        return collisions

    def reset_player_to_spawn(self, player) -> None:
        """Place the shared player object at the arrival altar."""
        player.position.xy = (HOME_PLAYER_START_X, HOME_PLAYER_START_Y)
        player.rect.topleft = (HOME_PLAYER_START_X, HOME_PLAYER_START_Y)
        player.facing = "up"

    def _draw_fallback(self, surface: pygame.Surface, camera_offset: tuple[int, int]) -> None:
        surface.fill(palette.NIGHT_BLACK)
        ox, oy = camera_offset
        for y in range(0, config.MAP_HEIGHT, config.TILE_SIZE):
            for x in range(0, config.MAP_WIDTH, config.TILE_SIZE):
                color = palette.GROUND_DARK if (x // 16 + y // 16) % 2 else palette.GROUND_MID
                draw_filled_rect(surface, (x + ox, y + oy, 16, 16), color)

        altar = self.altar_rect.move(camera_offset)
        draw_double_rect(surface, altar, palette.MOON_WHITE, palette.DEEP_BLUE)
        draw_filled_rect(surface, self.sign_rect.move(camera_offset), palette.WOOD_BROWN)
        draw_double_rect(surface, self.shadow_rect.move(camera_offset), palette.MOON_WHITE, palette.DEEP_BLUE)

    def _on_dialog_active_changed(self, **payload) -> None:
        """Open the gate only after the full rules dialog is closed."""
        if payload.get("active", True):
            return
        if payload.get("speaker_id") == "home_sign" and self.sign_read:
            self.rules_briefing_complete = True
