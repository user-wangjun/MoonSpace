"""Pygame 游戏主循环基础。"""

from __future__ import annotations

from collections.abc import Callable
from copy import deepcopy

import pygame

import config
from core.audio import AudioManager
from core.demo_rules import (
    PSEUDO_RULE_YUTU_WATCH,
    RULE_BOW_TO_TREE,
    RULE_NO_EYE_CONTACT,
    RULE_POOL_REFLECTION,
    is_facing_rect,
    register_demo_rules,
)
from core.event_bus import (
    DIALOG_CHOICE_SELECTED,
    GLOBAL_EVENT_BUS,
    PLAYER_DIED,
    SHOW_DIALOG,
    TREE_BLEEDING,
    VIOLATION_CHANGED,
)
from core.game_state import GameState
from core.input_manager import InputManager
from core.rule_engine import RuleEngine
from core.save_manager import SaveManager
from core.settings_manager import SettingsManager
from core.vibration import VIBRATION_TRANSITION_FOUND, VibrationManager
from effects.distortion import DistortionEffect
from entities.player import Player
from entities.wugang import Wugang
from entities.yutu import Yutu
from ui.death_screen import DeathScreen
from ui.dialog_box import DialogBox
from ui.ending_cg import EndingCG
from ui.envoy_register import EnvoyRegister
from ui.main_menu import MENU_DELETE_SAVE, MENU_LOAD_GAME, MENU_NEW_GAME, MENU_QUIT, MENU_SETTINGS, MainMenu
from ui.opening_cg import OpeningCG
from ui.rule_book import RuleBook
from ui.broken_jade import BrokenJadeView
from ui.scene_transition import SceneTransition
from ui.pause_menu import PAUSE_LOAD, PAUSE_MAIN_MENU, PAUSE_RESUME, PAUSE_SAVE, PAUSE_SETTINGS, PauseMenu
from ui.save_menu import SAVE_MODE_DELETE, SAVE_MODE_LOAD, SAVE_MODE_NEW, SAVE_MODE_SAVE, SaveMenu
from ui.settings_menu import SETTINGS_BACK, SettingsMenu
from utils import palette
from utils.assets import load_image
from utils.font import render_text
from utils.pixel_art import draw_double_rect, draw_filled_rect, draw_rect
from world.laurel_tree import LaurelTree
from world.moon_pool import MoonPool
from world.palace_wall import PalaceWall
from world.pound_table import PoundTable
from world.home_tutorial_scene import HomeTutorialScene
from world.tile_map import TileMap
from world.trigger_zone import CircularTriggerZone, TriggerZone
from world.repair_hall import RepairHall
from world.repair_door import RepairDoor
from world.sign_board import BASIC_RULES
from world.scenery import HALL_LANTERNS, draw_scenery_foreground


class Game:
    """MoonSpace 主游戏对象，负责主循环、实体更新、规则检测和基础渲染。"""

    MODE_MAIN_MENU = "main_menu"
    MODE_SAVE_MENU = "save_menu"
    MODE_SETTINGS = "settings"
    MODE_PAUSE = "pause"
    MODE_OPENING = "opening"
    MODE_HOME = "home"
    MODE_TRANSITION = "transition"
    MODE_PLAYING = "playing"
    MODE_GUANGHAN = "guanghan"
    MODE_REPAIR = "repair_hall"
    MODE_ENDING_CG = "ending_cg"

    DEFAULT_MAINLINE = {
        "wugang_checked": False,
        "yutu_checked": False,
        "repair_checked": False,
        "repair_door_open": False,
        "wugang_polluted": False,
        "yutu_polluted": False,
        "report_completed": False,
        "handoff_completed": False,
        "return_countdown_active": False,
        "return_countdown_remaining": 0.0,
        "return_departed_on_time": False,
        "pending_pool_ending": "",
        "ending": "",
        "broken_jade_obtained": False,
    }
    REPORT_STAGING_ASSETS = (
        "report_01_enter_hall.png",
        "report_02_walk_forward.png",
        "report_03_stop_before_chang_e.png",
        "report_04_formal_bow.png",
        "report_05_present_records.png",
        "report_06_chang_e_receives_records.png",
        "report_07_records_on_desk.png",
    )
    REPORT_SHOT_DURATION = 1.2
    REPORT_STAGING_DURATION = 8.4
    REPORT_AUDIO_CUES = (
        (0.0, "cg_palace_transition"),
        (4.8, "cg_wugang_axe"),
        (6.0, "cg_yutu_pestle"),
    )
    # 透明图集单帧的实际 Alpha 高度约为主角的 1.5～1.6 倍；
    # 以 100×100 绘制，避免按整张图集留白直接放大成近 2 倍身高。
    CHANG_E_WORLD_FRAME_SIZE = (100, 100)

    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption(config.WINDOW_TITLE)
        self.windowed_size = (config.WINDOW_WIDTH, config.WINDOW_HEIGHT)
        self.fullscreen = True
        self.display_surface = self._set_display_mode(self.fullscreen)
        self.game_surface = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        self.running = True

        self.input_manager = InputManager()
        self.event_bus = GLOBAL_EVENT_BUS
        self.event_bus.clear()
        self.settings_manager = SettingsManager()
        self.audio = AudioManager(self.event_bus, settings=self.settings_manager.values)
        self.vibration = VibrationManager(
            self.event_bus,
            enabled=self.settings_manager.values.get("vibration_enabled", True),
        )
        self.game_state = GameState(self.event_bus)
        self.rule_engine = RuleEngine(self.game_state)
        register_demo_rules(self.rule_engine)

        self.save_manager = SaveManager()
        self.main_menu = MainMenu()
        self.save_menu = SaveMenu(self.save_manager)
        self.pause_menu = PauseMenu()
        self.opening_cg = OpeningCG(self.audio)
        self.ending_cg = EndingCG(self.audio)
        self.envoy_register = EnvoyRegister()
        self.scene_transition = SceneTransition()
        self._transition_target_scene: str | None = None
        self.mode = self.MODE_MAIN_MENU
        self.pending_save_mode = SAVE_MODE_LOAD
        self.save_menu_return_mode = self.MODE_MAIN_MENU
        self.settings_return_mode = self.MODE_MAIN_MENU
        self.pause_return_mode: str | None = None
        self.overlay_audio_mode = self.MODE_MAIN_MENU
        self.current_slot_id: int | None = None
        self.current_save_data: dict | None = None
        self.mainline = dict(self.DEFAULT_MAINLINE)
        self.repair_hall = RepairHall()
        self.repair_door = RepairDoor()
        self.checkpoint_notice = 0.0
        self.report_staging_active = False
        self.report_staging_timer = 0.0
        self.report_staging_duration = self.REPORT_STAGING_DURATION
        self.pending_report_dialog: tuple[str, list[str], str] | None = None
        self.report_started = False
        self._report_audio_cues_played: set[str] = set()
        # 广寒宫唯一可行走背景是俯视帷幕图；交互点按该图的地面、台阶和南门重新校准。
        # 正面王座图仍保留为 CG 候选，不参与世界坐标或碰撞。
        self.guanghan_register_desk_rect = pygame.Rect(160, 300, 180, 96)
        self.guanghan_register_collision_rect = pygame.Rect(170, 316, 160, 80)
        # 旧卷与姓名登记分别位于桌前两侧，侧面也保留可接近的窄入口。
        self.guanghan_records_rect = pygame.Rect(180, 404, 64, 26)
        self.guanghan_records_side_rect = pygame.Rect(132, 372, 52, 58)
        self.guanghan_register_rect = pygame.Rect(252, 404, 64, 26)
        self.guanghan_register_side_rect = pygame.Rect(308, 372, 52, 58)
        # 复命点在北侧台阶前的地面；玩家不能站到王座、台阶或帷幕立面上。
        self.guanghan_report_rect = pygame.Rect(410, 244, 140, 56)
        # 南门交互区位于门楼前的地面边缘，进入后会回到前院，不穿过门楼立面。
        self.guanghan_exit_rect = pygame.Rect(420, 450, 120, 40)
        self.courtyard_south_exit_rect = pygame.Rect(420, 380, 120, 40)
        # The approved world map remains the closed-screen 960x720 layout.
        # The open-throne artwork is a frontal CG master and is not a world map.
        self.guanghan_walkable_background = "sprites/moonspace/backgrounds/guanghan_hall_curtain.png"
        self.guanghan_cg_background = "sprites/moonspace/backgrounds/guanghan_hall.png"
        self.chang_e_sheet_path = "sprites/moonspace/sheets/chang_e_16frames_transparent.png"
        self._chang_e_frames: list[pygame.Surface] | None = None
        self._chang_e_time = 0.0

        self.tile_map = TileMap()
        self.player = Player(config.PLAYER_START_X, config.PLAYER_START_Y)
        self.home_tutorial = HomeTutorialScene(self.event_bus)
        self.palace_wall = PalaceWall()
        self.palace_entry_rect = self.palace_wall.get_entry_rect()
        self.laurel_tree = LaurelTree(72, 196)
        self.moon_pool = MoonPool(480, 300)
        # 月池本体必须保持硬碰撞；污染结局从池沿触发，不能要求玩家
        # 先穿进水面再按交互键。
        self.moon_pool_interaction_rect = self.moon_pool.rect.inflate(24, 24)
        self.pound_table = PoundTable(700, 302)
        self.world_objects = [
            self.palace_wall,
            self.moon_pool,
            self.laurel_tree,
            self.pound_table,
        ]
        self.wugang = Wugang(self.event_bus, 248, 320)
        self.yutu = Yutu(self.event_bus, 700, 300)
        self.npcs = [self.wugang, self.yutu]
        self.dialog_box = DialogBox(self.event_bus)
        self.rule_book = RuleBook(self.event_bus, self.game_state)
        self.broken_jade_view = BrokenJadeView()
        self.death_screen = DeathScreen(self.event_bus, self.game_state, self.audio)
        self.distortion = DistortionEffect(
            self.event_bus,
            shake_enabled=bool(self.settings_manager.values.get("vibration_enabled", True)),
        )
        self.settings_menu = SettingsMenu(
            self.settings_manager,
            self.audio,
            self.vibration,
            self.distortion,
        )
        self.event_bus.subscribe(TREE_BLEEDING, self._on_tree_bleeding)
        self.event_bus.subscribe(VIOLATION_CHANGED, self._on_violation_changed)
        self.event_bus.subscribe(DIALOG_CHOICE_SELECTED, self._on_dialog_choice_selected)

        self._setup_rule_zones()
        self._tree_bleeding_check_cooldown = 0.0
        self._tree_was_bleeding = False
        self._tree_safe_exit_grace = 0.0

    def run(self) -> None:
        """运行固定 60 FPS 主循环，退出后释放 Pygame。"""
        while self.running:
            dt = self.clock.tick(config.FPS) / 1000.0
            self._handle_events()
            self.update(dt)
            self.draw()

        pygame.quit()

    def _handle_events(self) -> None:
        """处理窗口关闭和键盘事件。"""
        self.input_manager.begin_frame()
        for event in pygame.event.get():
            self.input_manager.process_event(event)

        if self.input_manager.fullscreen_toggle_requested:
            self._toggle_fullscreen()

        if self.input_manager.quit_requested:
            self.running = False

    def update(self, dt: float) -> None:
        """按当前流程状态更新存档菜单、开场 CG 或正式游戏。"""
        # Keep route music state-driven. A transition deliberately keeps its
        # current BGM until the target scene is committed, so a same-track
        # scene change never restarts the loop.
        self.audio.update(dt)
        self._sync_audio_for_mode()
        self.checkpoint_notice = max(0.0, self.checkpoint_notice - dt)

        if self.mode == self.MODE_MAIN_MENU:
            action = self.main_menu.update(dt, self.input_manager)
            self._handle_main_menu_action(action)
            return

        if self.mode == self.MODE_SETTINGS:
            action = self.settings_menu.update(dt, self.input_manager)
            if action == SETTINGS_BACK:
                self._close_settings()
            return

        if self.mode == self.MODE_PAUSE:
            self._update_pause(dt)
            return

        if self.mode == self.MODE_SAVE_MENU:
            selected_slot = self.save_menu.update(dt, self.input_manager)
            if self.save_menu.back_requested:
                self.mode = self.save_menu_return_mode
                self.save_menu.back_requested = False
            elif selected_slot is not None:
                if self.pending_save_mode == SAVE_MODE_SAVE:
                    self._save_game_to_slot(selected_slot)
                else:
                    self._start_slot(selected_slot, force_new=self.pending_save_mode == SAVE_MODE_NEW)
            return

        if self.mode == self.MODE_OPENING:
            if self.opening_cg.update(dt, self.input_manager):
                self._finish_opening()
            return

        if self.mode == self.MODE_ENDING_CG:
            if self.ending_cg.update(dt, self.input_manager):
                self.audio.stop_bgm(immediate=True)
                self.mode = self.MODE_MAIN_MENU
            return

        if self.mode == self.MODE_TRANSITION:
            self._update_transition(dt)
            return

        if self.mode == self.MODE_HOME:
            self._update_home(dt)
            return

        if self.mode == self.MODE_GUANGHAN:
            self._update_guanghan(dt)
            return

        if self.mode == self.MODE_REPAIR:
            self._update_repair_hall(dt)
            return

        self._update_playing(dt)

    def _update_home(self, dt: float) -> None:
        """更新穿越后、正式入宫前的 home 教程场景。"""
        if self._try_open_pause():
            return

        if self.dialog_box.active:
            was_rules_briefing_complete = self.home_tutorial.rules_briefing_complete
            self.dialog_box.update(dt, self.input_manager)
            if self.home_tutorial.rules_briefing_complete != was_rules_briefing_complete:
                self._save_checkpoint("rules_read")
            self.distortion.update(dt)
            return

        self.rule_book.update(dt, self.input_manager)
        if self.rule_book.is_open:
            self.distortion.update(dt)
            return

        if self._try_trigger_he_return():
            self.distortion.update(dt)
            return

        was_sign_read = self.home_tutorial.sign_read
        was_rules_briefing_complete = self.home_tutorial.rules_briefing_complete
        if self.input_manager.was_pressed(config.ACTION_INTERACT):
            self.player.trigger_interact_animation()
        self.home_tutorial.update(dt, self.input_manager, self.player, self.game_state)

        if not self.dialog_box.active:
            self.player.update(dt, self.input_manager, self.home_tutorial.get_collision_rects())

        if self.home_tutorial.rules_briefing_complete and not was_rules_briefing_complete:
            self._save_checkpoint("rules_read")

        if self.home_tutorial.is_gate_entered(self.player.rect):
            self._finish_home_tutorial()

        self.distortion.update(dt)

    def _enter_repair_hall(self) -> None:
        """自由进入偏殿，不创建挑战前存档。"""
        self.mode = self.MODE_REPAIR
        self.dialog_box.active = False
        self.repair_hall.reset(bool(self.mainline.get("repair_checked")))
        self.player.rect.midbottom = RepairHall.SPAWN
        self.player.position.xy = self.player.rect.topleft
        self.player.facing = "up"
        self.audio.sync_for_game_state(self.mode, self.mainline)

    def _begin_repair_trial(self) -> None:
        trial = self.repair_hall.trial
        if trial.phase != "idle":
            return
        trial.brief()
        for note_id, text in RepairHall.NOTES.items():
            self.game_state.add_known_rule(note_id, text)
        self.event_bus.emit(SHOW_DIALOG, speaker_id="repairman", lines=list(RepairHall.INTRO))

    def _observe_repair_piece(self) -> None:
        self.repair_hall.trial.record_observation()
        note = self.repair_hall.observe_piece()
        if note is not None:
            self.game_state.add_known_rule(*note)

    def _submit_repair_piece(self) -> None:
        result = self.repair_hall.trial.submit()
        if result in ("death", "sealing"):
            self.repair_hall.choose_piece = False
            self.dialog_box.active = False
            self.rule_book.close()
            self.audio.stop_repair_sounds()

    def _update_repair_hall(self, dt: float) -> None:
        hall, inputs = self.repair_hall, self.input_manager
        trial = hall.trial
        # Clock runs before every interaction, including inspection/dialogue/book overlays.
        result = trial.tick(dt)
        if result == "restore":
            self._reset_after_death()
            return
        if result == "completed":
            self.mainline["repair_checked"] = True
            # Reaching a completed hall also proves the entrance has been
            # opened, including legacy saves that entered the hall directly.
            self.mainline["repair_door_open"] = True
            self.audio.stop_repair_sounds()
            self._save_checkpoint("repair_completed")
            hall.say("已记：旧月裂片验明，修月封存已毕。", 5.0)
        if trial.phase == "death":
            self.dialog_box.active = False
            self.rule_book.close()
            if "silenced" not in hall.sounds_played:
                self.audio.stop_repair_sounds()
            hall.sounds_played.add("silenced")
            if trial.elapsed >= .24 and "scare" not in hall.sounds_played:
                hall.sounds_played.add("scare")
                self.audio.play_spatial("repair_scare", gain=1.0)
            return
        if trial.phase == "sealing":
            if trial.elapsed >= 2.8 and "box" not in hall.sounds_played:
                hall.sounds_played.add("box")
                self.audio.play_spatial("repair_chisel", gain=.85)
            return
        hall.update_ambience(max(0.0, dt), self.player.rect, self.audio)
        if self.dialog_box.active:
            self.dialog_box.update(dt, inputs)
            if not self.dialog_box.active and trial.phase == "briefing":
                trial.start()
            return
        if trial.phase == "briefing":
            trial.start()
        book_was_open = self.rule_book.is_open
        self.rule_book.update(dt, inputs)
        if book_was_open or self.rule_book.is_open:
            trial.end_rotation()
            return
        if hall.choose_piece:
            if inputs.was_key_pressed(pygame.K_a) or inputs.was_key_pressed(pygame.K_LEFT):
                hall.piece_cursor = (hall.piece_cursor - 1) % 3
            if inputs.was_key_pressed(pygame.K_d) or inputs.was_key_pressed(pygame.K_RIGHT):
                hall.piece_cursor = (hall.piece_cursor + 1) % 3
            if inputs.was_pressed(config.ACTION_QUIT):
                hall.choose_piece = False
            elif inputs.was_pressed(config.ACTION_INTERACT):
                trial.pick_up(hall.piece_order[hall.piece_cursor])
                hall.choose_piece = False
                return
        if trial.inspecting:
            mouse_position = self._game_mouse_position()
            if (inputs.was_mouse_pressed(1) and mouse_position is not None
                    and hall.INSPECTION_DRAG_ZONE.collidepoint(mouse_position)):
                trial.begin_rotation()
            if trial.dragging and inputs.mouse_button_down(1):
                mouse_motion = self._game_mouse_motion()
                trial.drag_rotation(mouse_motion.x, mouse_motion.y)
            if inputs.was_mouse_released(1):
                trial.end_rotation()
            self._observe_repair_piece()
            if inputs.was_pressed(config.ACTION_INTERACT) or inputs.was_pressed(config.ACTION_QUIT):
                trial.end_rotation()
                trial.inspecting = False
                hall.say("", 0.0)
            return
        if self._try_open_pause():
            return
        if inputs.was_pressed(config.ACTION_INTERACT):
            target = hall.nearby(self.player.rect)
            if target == "exit":
                if trial.phase == "active":
                    hall.say("验片未毕，守月人挡住了归路。封期仍在走。")
                else:
                    self.audio.stop_repair_sounds()
                    self.mode = self.MODE_PLAYING
                    self.player.rect.midbottom = RepairHall.COURTYARD_RETURN
                    self.player.position.xy = self.player.rect.topleft
                    self.player.facing = "right"
                    # Keep the completed task checkpoint, but move its
                    # recoverable location to the actual courtyard exit.
                    self._save_current_slot()
                return
            if target == "table":
                if trial.phase == "idle":
                    self._begin_repair_trial()
                elif trial.phase == "active":
                    hall.choose_piece = True
                    hall.piece_cursor = hall.slot_for_piece(trial.selected) if trial.selected is not None else 0
                else:
                    hall.say("今夜这一片，算是收好了。来使还有正事，去吧。")
                return
            if target == "tray":
                if trial.phase == "active" and trial.selected is not None:
                    self._submit_repair_piece()
                else:
                    hall.say("验盘空着。认定裂片后，在这里正式交片。")
                return
            if target == "statue":
                lines = ["血从石像嘴角的细缝渗出，流入擦得很干净的浅盘。",
                         "裂缝两端微微翘起。石像身上，还有几处已经补平的旧痕。",
                         "守月人没有抬头：盘子莫挪，挪了要滴到地上。"]
                self.game_state.add_known_rule("repair_statue", "渗血石像：" + "".join(lines))
                if trial.selected == 2:
                    lines.insert(2, "这道裂口的形状，像手里那片旧月。")
                    self.game_state.add_known_rule(
                        "repair_statue_match",
                        "石像裂口的形状，像月片·" + hall.selected_slot_name() + "上的崩口。",
                    )
                self.event_bus.emit(SHOW_DIALOG, speaker_id="toad_statue", lines=lines)
                return
            if trial.selected is not None:
                trial.in_light = hall.light_zone.colliderect(self.player.rect)
                trial.inspecting = True
                hall.say("", 0.0)
                self._observe_repair_piece()
                return
        self.player.update(dt, inputs, hall.collisions(), RepairHall.SIZE)
        trial.in_light = hall.light_zone.colliderect(self.player.rect)
        self.distortion.update(dt)

    def _draw_repair_hall(self) -> None:
        offset = self._camera_offset()
        self.repair_hall.draw(
            self.game_surface, self.player, offset,
            show_hints=not (self.dialog_box.active or self.rule_book.is_open),
        )
        if self.repair_hall.trial.phase not in ("death", "sealing"):
            self.rule_book.draw(self.game_surface)
            self.dialog_box.draw(self.game_surface)
            if self.repair_hall.trial.phase == "active":
                self.repair_hall.draw_timer(self.game_surface)

    def _draw_repair_entrance(self, surface, offset) -> None:
        self.repair_door.draw_world(surface, RepairHall.COURTYARD_ENTRY, offset, self.player.rect)

    def _update_repair_door(self, dt):
        result = self.repair_door.update(
            dt,
            self.input_manager,
            can_turn=self.repair_door.LEFT_ZONE.colliderect(self.player.rect),
            tree_bleeding=self.laurel_tree.bleeding,
        )
        if result == "opened":
            self.mainline["repair_door_open"] = True
            # Opening the entrance is a safe, non-event save. It records the
            # current courtyard position without inventing a task checkpoint.
            self._save_current_slot()
            self.audio.play_spatial("cg_palace_transition", gain=.6)
            self.audio.play_spatial("repair_drip", gain=.45)
        elif result == "enter":
            self._enter_repair_hall()
        elif result == "aligned":
            self.audio.play_spatial("repair_drip", gain=.35)
        elif result == "turned":
            self.audio.play_spatial("repair_chisel", gain=.3, pan=-.3)
        return result

    def _update_guanghan(self, dt: float) -> None:
        """更新广寒宫内殿基础状态。"""
        if self._try_open_pause():
            return
        # 复命后的候月倒计时是流程时间，不因打开登记页、规则手册或复命字幕而暂停。
        if self._update_return_countdown(dt):
            self.distortion.update(dt)
            return
        if self.envoy_register.active:
            if self.envoy_register.update(self.input_manager, dt):
                self._save_checkpoint("envoy_registered")
            self.distortion.update(dt)
            return
        if self.report_staging_active:
            self._update_report_staging(dt)
            self.distortion.update(dt)
            return
        if self.dialog_box.active:
            was_dialog_active = self.dialog_box.active
            self.dialog_box.update(dt, self.input_manager)
            self._mark_handoff_completed_if_closed(was_dialog_active)
            self.distortion.update(dt)
            return
        self.rule_book.update(dt, self.input_manager)
        if self.rule_book.is_open:
            self.distortion.update(dt)
            return
        if self.input_manager.was_pressed(config.ACTION_INTERACT):
            self.player.trigger_interact_animation()
            if self._player_in_guanghan_records_zone():
                self.envoy_register.open_records()
                self.distortion.update(dt)
                return
            if self._player_in_guanghan_register_zone():
                self.envoy_register.open_register()
                self.distortion.update(dt)
                return
            if self.guanghan_report_rect.colliderect(self.player.rect) and not self.report_started:
                self._begin_guanghan_report()
                self.distortion.update(dt)
                return
            if self.guanghan_exit_rect.colliderect(self.player.rect) and self._try_leave_guanghan_after_report():
                self.distortion.update(dt)
                return
        self.player.update(
            dt,
            self.input_manager,
            self._guanghan_collision_rects(),
            (config.GUANGHAN_WIDTH, config.GUANGHAN_HEIGHT),
        )
        self.distortion.update(dt)

    def _update_playing(self, dt: float) -> None:
        """更新正式游玩状态。"""
        if self._try_open_pause():
            return

        if self.death_screen.active:
            if self.death_screen.update(dt, self.input_manager):
                self._reset_after_death()
            self.distortion.update(dt)
            return

        if self.game_state.is_dead():
            # Keep a manually restored or externally supplied dead state on
            # the same death sequence as the normal add_violation event.
            self.event_bus.emit(
                PLAYER_DIED,
                count=self.game_state.violation_count,
                rule_id="dead_state",
            )
            self.distortion.update(dt)
            return

        # 离开广寒宫后计时仍在前院继续，规则手册、对话和道具界面也不能暂停它。
        if self._update_return_countdown(dt):
            self.distortion.update(dt)
            return

        if self.broken_jade_view.active:
            self.broken_jade_view.update(self.input_manager)
            self.distortion.update(dt)
            return

        for world_object in self.world_objects:
            world_object.update(dt)
        for npc in self.npcs:
            npc.update(dt, self.player.rect)

        if self.repair_door.active:
            result = self._update_repair_door(dt)
            # The entrance mechanism is a live courtyard activity. The player
            # can leave the left toad to escape Laurel's forbidden radius, but
            # the angle hold only advances while they are back at the control.
            # This is what makes the existing proximity rule part of the
            # puzzle instead of a decorative status message.
            if self.mode != self.MODE_PLAYING or not self.repair_door.active:
                self.distortion.update(dt)
                return
            if not self.dialog_box.active:
                self.player.update(
                    dt,
                    self.input_manager,
                    self._get_collision_rects(),
                    (config.COURTYARD_WIDTH, config.COURTYARD_HEIGHT),
                )
                self._update_rule_checks(dt)
            self.distortion.update(dt)
            return

        if self.report_staging_active:
            self._update_report_staging(dt)
            self.distortion.update(dt)
            return
        if self.dialog_box.active:
            self.dialog_box.update(dt, self.input_manager)
            self.distortion.update(dt)
            return

        self.rule_book.update(dt, self.input_manager)
        if self.rule_book.is_open:
            self.distortion.update(dt)
            return

        if self.input_manager.was_pressed(config.ACTION_INTERACT):
            self.player.trigger_interact_animation()
            if self.repair_door.RIGHT_ZONE.colliderect(self.player.rect):
                return
            if self.repair_door.LEFT_ZONE.colliderect(self.player.rect):
                if not self.repair_door.unlocked:
                    self.repair_door.active = True
                return
            if RepairHall.COURTYARD_ENTRY.colliderect(self.player.rect):
                if self.mainline.get("report_completed") or self.mainline.get("pending_pool_ending"):
                    self.event_bus.emit(SHOW_DIALOG, speaker_id="repairman",
                                        lines=["旧月已经封存。来使复命既毕，不必重验。"])
                elif self.repair_door.unlocked:
                    self._enter_repair_hall()
                else:
                    self.event_bus.emit(SHOW_DIALOG, speaker_id="courtyard_gate",
                                        lines=["两尊托灯石蟾分立门旁，右蟾朝着门内。", "左侧石座下露出一道转槽，像是要把它转到与右蟾同向。"])
                return
            if self.mainline.get("pending_pool_ending") and self.moon_pool_interaction_rect.colliderect(
                self.player.rect
            ):
                self._try_trigger_pending_pool_ending()
                self.distortion.update(dt)
                return
            if self.courtyard_south_exit_rect.colliderect(self.player.rect):
                self._leave_courtyard_to_home()
                self.distortion.update(dt)
                return
            if self.palace_entry_rect.colliderect(self.player.rect):
                if self._check_palace_entry():
                    self.distortion.update(dt)
                    return
            else:
                for npc in self.npcs:
                    if npc is self.wugang:
                        if self._try_complete_wugang_check():
                            break
                        # 未出现月桂异像时，吴刚不提供普通对话入口。
                        continue
                    if npc is self.yutu and self._try_handle_yutu_check():
                        break
                    if npc.interact():
                        break

        if self.game_state.is_dead():
            # A violation callback may emit PLAYER_DIED while the interaction
            # loop is still on the stack. Stop this frame before movement,
            # dialogue callbacks, or any later task progression can run.
            self.distortion.update(dt)
            return

        if not self.dialog_box.active:
            self.player.update(
                dt,
                self.input_manager,
                self._get_collision_rects(),
                (config.COURTYARD_WIDTH, config.COURTYARD_HEIGHT),
            )
            self._update_rule_checks(dt)

        self.distortion.update(dt)

    def draw(self) -> None:
        """绘制当前流程状态，并等比缩放到当前显示区域。"""
        if self.mode == self.MODE_MAIN_MENU:
            self.main_menu.draw(self.game_surface)
        elif self.mode == self.MODE_SETTINGS:
            self._draw_settings_background()
            self.settings_menu.draw(self.game_surface)
        elif self.mode == self.MODE_PAUSE:
            self._draw_gameplay_context(self.pause_return_mode)
            self.pause_menu.draw(self.game_surface)
        elif self.mode == self.MODE_SAVE_MENU:
            if self.save_menu_return_mode == self.MODE_PAUSE:
                self._draw_gameplay_context(self.overlay_audio_mode)
                self.save_menu.draw(self.game_surface, overlay=True)
            else:
                self.save_menu.draw(self.game_surface)
        elif self.mode == self.MODE_OPENING:
            self.opening_cg.draw(self.game_surface)
        elif self.mode == self.MODE_TRANSITION:
            self.scene_transition.draw(self.game_surface)
        elif self.mode == self.MODE_HOME:
            self._draw_home()
        elif self.mode == self.MODE_GUANGHAN:
            self._draw_guanghan()
        elif self.mode == self.MODE_REPAIR:
            self._draw_repair_hall()
        elif self.mode == self.MODE_ENDING_CG:
            self.ending_cg.draw(self.game_surface)
        else:
            self._draw_playing()

        show_checkpoint = self.checkpoint_notice > 0 and self.mode in (
            self.MODE_HOME, self.MODE_PLAYING, self.MODE_REPAIR, self.MODE_GUANGHAN)
        if self.mode == self.MODE_REPAIR:
            show_checkpoint = show_checkpoint and self.repair_hall.trial.phase in ("idle", "complete")
        if show_checkpoint and not self.repair_door.active:
            draw_filled_rect(self.game_surface, (340, 246, 132, 18), palette.BLACK)
            render_text(self.game_surface, "事件完成 · 已存档", 346, 249, 11, palette.PALE_MOON)

        target_rect = self._scaled_game_rect(self.display_surface.get_size())
        scaled = pygame.transform.scale(
            self.game_surface,
            target_rect.size,
        )
        self.display_surface.fill(palette.BLACK)
        display_rect = target_rect
        if self.mode == self.MODE_TRANSITION:
            scale = target_rect.width / config.SCREEN_WIDTH
            display_rect = target_rect.move(
                round(self.distortion.camera_offset.x * scale),
                round(self.distortion.camera_offset.y * scale),
            )
        self.display_surface.blit(scaled, display_rect)
        pygame.display.flip()

    def _set_display_mode(self, fullscreen: bool) -> pygame.Surface:
        """应用窗口或全屏显示模式，并返回当前显示表面。"""
        if fullscreen:
            surface = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        else:
            surface = pygame.display.set_mode(self.windowed_size, pygame.RESIZABLE)
        pygame.display.set_caption(config.WINDOW_TITLE)
        return surface

    def _toggle_fullscreen(self) -> None:
        """在普通窗口和无标题栏全屏之间切换。"""
        if not self.fullscreen:
            self.windowed_size = self.display_surface.get_size()
        fullscreen = not self.fullscreen
        self.display_surface = self._set_display_mode(fullscreen)
        self.fullscreen = fullscreen

    @staticmethod
    def _scaled_game_rect(display_size: tuple[int, int]) -> pygame.Rect:
        """返回游戏画面在显示区域内的最大等比居中矩形。"""
        display_width, display_height = display_size
        scale = min(
            display_width / config.SCREEN_WIDTH,
            display_height / config.SCREEN_HEIGHT,
        )
        scaled_width = max(1, int(config.SCREEN_WIDTH * scale))
        scaled_height = max(1, int(config.SCREEN_HEIGHT * scale))
        x = (display_width - scaled_width) // 2
        y = (display_height - scaled_height) // 2
        return pygame.Rect(x, y, scaled_width, scaled_height)

    def _game_mouse_position(self) -> pygame.Vector2 | None:
        """Map the display mouse position into the fixed 480×270 game surface."""
        position = self.input_manager.mouse_position
        if position is None:
            return None
        target = self._scaled_game_rect(self.display_surface.get_size())
        if not target.collidepoint(position):
            return None
        return pygame.Vector2(
            (position[0] - target.x) * config.SCREEN_WIDTH / target.width,
            (position[1] - target.y) * config.SCREEN_HEIGHT / target.height,
        )

    def _game_mouse_motion(self) -> pygame.Vector2:
        """Map per-frame display mouse motion into fixed game-surface pixels."""
        target = self._scaled_game_rect(self.display_surface.get_size())
        return pygame.Vector2(
            self.input_manager.mouse_motion.x * config.SCREEN_WIDTH / target.width,
            self.input_manager.mouse_motion.y * config.SCREEN_HEIGHT / target.height,
        )

    def _scene_world_size(self, mode: str | None = None) -> tuple[int, int]:
        """返回当前剧情场景的独立世界尺寸。"""
        scene = mode or self.mode
        if scene == self.MODE_PLAYING:
            return config.COURTYARD_WIDTH, config.COURTYARD_HEIGHT
        if scene == self.MODE_GUANGHAN:
            return config.GUANGHAN_WIDTH, config.GUANGHAN_HEIGHT
        if scene == self.MODE_REPAIR:
            return RepairHall.SIZE
        return config.MAP_WIDTH, config.MAP_HEIGHT

    def _camera_offset(self) -> tuple[int, int]:
        """返回跟随玩家且被大地图边界限制的世界偏移。"""
        world_width, world_height = self._scene_world_size()
        camera_x = self.player.rect.centerx - config.SCREEN_WIDTH // 2
        if self.mode in (self.MODE_GUANGHAN, self.MODE_REPAIR):
            # 内殿纵深大于视口；把来使放在画面下方，保留北侧帷幕和复命人物。
            camera_y = self.player.rect.centery - int(config.SCREEN_HEIGHT * 0.8)
        else:
            camera_y = self.player.rect.centery - config.SCREEN_HEIGHT // 2
        if self.mode == self.MODE_REPAIR:
            camera_y = min(60, camera_y)
        camera_x = max(0, min(world_width - config.SCREEN_WIDTH, camera_x))
        camera_y = max(0, min(world_height - config.SCREEN_HEIGHT, camera_y))
        distortion_x = round(self.distortion.camera_offset.x)
        distortion_y = round(self.distortion.camera_offset.y)
        return (-camera_x + distortion_x, -camera_y + distortion_y)

    def _draw_playing(self) -> None:
        """绘制地图、世界物体、NPC、玩家、特效和 UI。"""
        self.game_surface.fill(palette.NIGHT_BLACK)
        camera_offset = self._camera_offset()
        self.palace_wall.set_gate_open(self._office_checks_complete())
        self.palace_wall.draw(self.game_surface, camera_offset)
        self._draw_repair_entrance(self.game_surface, camera_offset)
        self._draw_palace_entry_marker(self.game_surface, camera_offset)
        show_pool_reflection = self._player_faces_pool()
        reflection_sprite = None
        anomaly_sprite = None
        if show_pool_reflection:
            try:
                reflection_sprite = self.player.get_reflection_sprite()
                anomaly_sprite = reflection_sprite
            except (FileNotFoundError, pygame.error, ValueError):
                pass
        self.moon_pool.draw(
            self.game_surface,
            camera_offset,
            reflection_sprite=reflection_sprite,
            anomaly_sprite=anomaly_sprite,
            observer_center=self.player.rect.center,
            show_reflection=show_pool_reflection,
            show_pollution=bool(
                self.mainline.get("pending_pool_ending")
                or self.mainline.get("wugang_polluted")
                or self.mainline.get("yutu_polluted")
            ),
        )
        # The mortar is a static prop: draw its rear before depth sorting and
        # its front rim after the body/hand overlay to prevent repetition.
        self.pound_table.draw_back(self.game_surface, camera_offset)
        depth_items = [
            (self.laurel_tree.get_collision_rect().bottom, self.laurel_tree.draw),
            (self.pound_table.get_collision_rect().bottom, self.pound_table.draw_front),
        ]
        depth_items.extend((npc.get_collision_rect().bottom, npc.draw) for npc in self.npcs)
        depth_items.append(
            (
                self.player.rect.bottom,
                self.player.draw,
            )
        )
        for _, draw_item in sorted(depth_items, key=lambda item: item[0]):
            draw_item(self.game_surface, camera_offset)
        self.distortion.draw_overlay(self.game_surface)
        self._draw_interaction_hint(self.game_surface)
        self._draw_status_ui(self.game_surface)
        bleed_remaining = (
            max(0.0, self.laurel_tree.BLEED_DURATION - self.laurel_tree.bleed_time)
            if self.laurel_tree.bleeding else 0.0
        )
        self.repair_door.draw_active_hint(
            self.game_surface,
            tree_bleeding=self.laurel_tree.bleeding,
            bleed_remaining=bleed_remaining,
            can_turn=self.repair_door.LEFT_ZONE.colliderect(self.player.rect),
        )
        self._draw_return_countdown_hud(self.game_surface)
        self.rule_book.draw(self.game_surface)
        self.dialog_box.draw(self.game_surface)
        self.death_screen.draw(self.game_surface)
        self.broken_jade_view.draw(self.game_surface)

    def _draw_guanghan(self) -> None:
        """绘制广寒宫内殿场景和当前 UI 层。"""
        camera_offset = self._camera_offset()
        if self._draw_guanghan_background(camera_offset):
            self._draw_guanghan_actors(camera_offset)
            draw_scenery_foreground(
                self.game_surface, load_image(self.guanghan_walkable_background),
                HALL_LANTERNS, camera_offset, self.player.rect.bottom,
            )
        else:
            self.game_surface.fill(palette.BLACK)
            draw_filled_rect(self.game_surface, (0, 0, config.SCREEN_WIDTH, config.SCREEN_HEIGHT), palette.NIGHT_BLACK)
            draw_double_rect(self.game_surface, pygame.Rect(74, 38, 332, 166), palette.MOON_WHITE, palette.DEEP_BLUE)
            render_text(self.game_surface, "广寒宫内殿", 184, 78, 18, palette.PALE_MOON)
            render_text(self.game_surface, "复命流程尚未开启", 168, 112, 14, palette.MOON_WHITE)
        self._draw_return_countdown_hud(self.game_surface)
        if self.report_staging_active:
            self._draw_report_staging(self.game_surface)
        self.rule_book.draw(self.game_surface)
        self.dialog_box.draw(self.game_surface)
        self.envoy_register.draw(self.game_surface)

    def _draw_guanghan_background(self, camera_offset: tuple[int, int] = (0, 0)) -> bool:
        """绘制唯一可行走的俯视广寒宫背景；正面图不进入世界坐标系。"""
        try:
            background = load_image(self.guanghan_walkable_background)
        except (FileNotFoundError, pygame.error):
            return False
        hall_size = (config.GUANGHAN_WIDTH, config.GUANGHAN_HEIGHT)
        if background.get_size() != hall_size:
            # 世界图尺寸不匹配时宁可回退，也不把正面构图非等比拉伸成地图。
            return False
        self.game_surface.blit(background, camera_offset)
        return True

    def _draw_guanghan_actors(self, camera_offset: tuple[int, int]) -> None:
        """绘制内殿独立物件；嫦娥保持静止，避免世界层持续播放站立动作。"""
        self._draw_guanghan_chang_e(camera_offset)
        desk_sprite = self._get_guanghan_register_desk_sprite()
        desk_overlap = self.guanghan_register_desk_rect.colliderect(self.player.rect.inflate(8, 8))
        player_behind_desk = self.player.rect.bottom <= self.guanghan_register_desk_rect.bottom
        if not player_behind_desk:
            self._draw_guanghan_register_desk(camera_offset, desk_sprite)
        self.player.draw(self.game_surface, camera_offset)
        if player_behind_desk:
            self._draw_guanghan_register_desk(
                camera_offset,
                desk_sprite,
                alpha=150 if desk_overlap else 255,
            )
        self._draw_guanghan_interaction_hint()

    def _draw_guanghan_chang_e(self, camera_offset: tuple[int, int]) -> None:
        """绘制嫦娥的现有透明帧，不使用带绿幕的同名图集。"""
        if self._chang_e_frames is None:
            try:
                sheet = load_image(self.chang_e_sheet_path)
                sheet_width, sheet_height = sheet.get_size()
                frames = []
                for row in range(4):
                    for col in range(4):
                        left = round(col * sheet_width / 4)
                        top = round(row * sheet_height / 4)
                        right = round((col + 1) * sheet_width / 4)
                        bottom = round((row + 1) * sheet_height / 4)
                        frame = pygame.Surface((right - left, bottom - top), pygame.SRCALPHA)
                        frame.blit(sheet, (0, 0), pygame.Rect(left, top, right - left, bottom - top))
                        frames.append(frame)
                self._chang_e_frames = frames
            except (FileNotFoundError, pygame.error, ValueError):
                self._chang_e_frames = []
        if not self._chang_e_frames:
            return

        # 当前正式透明图集只有站立姿态；在正式坐姿资源接入前固定首帧，
        # 不让嫦娥在屏风前持续做与场景不符的动作。
        frame = self._chang_e_frames[0]
        # 图集帧带有留白；按实际 Alpha 高度收敛到主角约 1.5～1.6 倍。
        frame = pygame.transform.smoothscale(frame, self.CHANG_E_WORLD_FRAME_SIZE)
        destination = frame.get_rect(midbottom=(480 + camera_offset[0], 184 + camera_offset[1]))
        self.game_surface.blit(frame, destination)

    def _get_guanghan_register_desk_sprite(self) -> pygame.Surface | None:
        """返回按场景比例缩放后的登记台；较窄的玉简随桌面一起细化。"""
        try:
            desk_sprite = load_image("sprites/moonspace/props/registration_desk.png")
        except (FileNotFoundError, pygame.error):
            return None
        if desk_sprite.get_size() != self.guanghan_register_desk_rect.size:
            desk_sprite = pygame.transform.smoothscale(desk_sprite, self.guanghan_register_desk_rect.size)
        return desk_sprite

    def _draw_guanghan_register_desk(
        self,
        camera_offset: tuple[int, int],
        desk_sprite: pygame.Surface | None = None,
        *,
        alpha: int = 255,
    ) -> None:
        """绘制确认后的玉质登记台资源。"""
        desk_sprite = desk_sprite or self._get_guanghan_register_desk_sprite()
        if desk_sprite is None:
            return
        if alpha < 255:
            desk_sprite = desk_sprite.copy()
            desk_sprite.set_alpha(alpha)
        self.game_surface.blit(desk_sprite, self.guanghan_register_desk_rect.move(camera_offset))

    def _draw_guanghan_interaction_hint(self) -> None:
        if self.envoy_register.active or self.dialog_box.active or self.report_staging_active:
            return
        if self._player_in_guanghan_records_zone():
            text = "E 查看旧卷"
        elif self._player_in_guanghan_register_zone():
            text = "E 登记"
        elif self.guanghan_report_rect.colliderect(self.player.rect) and not self.report_started:
            text = "E 向嫦娥复命"
        elif self.guanghan_exit_rect.colliderect(self.player.rect):
            text = "E 离殿"
        else:
            return
        width = 100
        panel = pygame.Rect(config.SCREEN_WIDTH // 2 - width // 2, 242, width, 18)
        draw_filled_rect(self.game_surface, panel, palette.BLACK)
        draw_double_rect(self.game_surface, panel, palette.MOON_WHITE, palette.DEEP_BLUE)
        render_text(self.game_surface, text, panel.x + 8, panel.y + 3, 11, palette.MOON_WHITE)

    def _player_in_guanghan_records_zone(self) -> bool:
        """旧卷可从桌前左侧或登记台左侧接近。"""
        return any(
            rect.colliderect(self.player.rect)
            for rect in (self.guanghan_records_rect, self.guanghan_records_side_rect)
        )

    def _player_in_guanghan_register_zone(self) -> bool:
        """姓名登记可从桌前右侧或登记台右侧接近。"""
        return any(
            rect.colliderect(self.player.rect)
            for rect in (self.guanghan_register_rect, self.guanghan_register_side_rect)
        )

    def _guanghan_collision_rects(self) -> list[pygame.Rect]:
        """按俯视帷幕图阻挡高台、台阶、门楼立面和登记台。"""
        return [
            pygame.Rect(0, 0, config.GUANGHAN_WIDTH, 112),
            pygame.Rect(0, 0, 40, config.GUANGHAN_HEIGHT),
            pygame.Rect(config.GUANGHAN_WIDTH - 40, 0, 40, config.GUANGHAN_HEIGHT),
            pygame.Rect(0, config.GUANGHAN_HEIGHT - 4, config.GUANGHAN_WIDTH, 4),
            pygame.Rect(0, 480, self.guanghan_exit_rect.left, 240),
            pygame.Rect(
                self.guanghan_exit_rect.right,
                480,
                config.GUANGHAN_WIDTH - self.guanghan_exit_rect.right,
                240,
            ),
            pygame.Rect(self.guanghan_exit_rect.left, 480, self.guanghan_exit_rect.width, 240),
            pygame.Rect(348, 112, 244, 62),
            pygame.Rect(464, 172, 32, 12),
            *(pygame.Rect(prop.footprint) for prop in HALL_LANTERNS),
            self.guanghan_register_collision_rect.copy(),
        ]

    def _draw_report_staging(self, surface: pygame.Surface) -> None:
        """绘制复命 staging CG 和对应字幕。"""
        staging = None
        shot_index = self.report_shot_index_at(self.report_staging_timer)
        try:
            staging = load_image(f"sprites/moonspace/cg/{self.REPORT_STAGING_ASSETS[shot_index]}")
        except (FileNotFoundError, pygame.error):
            try:
                staging = load_image("sprites/moonspace/cg/report_staging.png")
            except (FileNotFoundError, pygame.error):
                staging = None

        if staging is not None:
            if staging.get_size() != surface.get_size():
                staging = pygame.transform.smoothscale(staging, surface.get_size())
            surface.blit(staging, (0, 0))
        else:
            shade = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT), pygame.SRCALPHA)
            shade.fill((*palette.BLACK, 170))
            surface.blit(shade, (0, 0))

        caption = self.pending_report_dialog[2] if self.pending_report_dialog else "来使呈上伐桂、捣药与修月查验。"
        panel = pygame.Surface((config.SCREEN_WIDTH, 34), pygame.SRCALPHA)
        panel.fill((*palette.BLACK, 182))
        # Keep the bottom 34 px as a dedicated safe band; the handoff props
        # in R5-R7 end above y=236, so the subtitle never covers them.
        surface.blit(panel, (0, config.SCREEN_HEIGHT - 34))
        render_text(surface, caption, 22, config.SCREEN_HEIGHT - 24, 13, palette.PALE_MOON)
        render_text(surface, "E 跳过", 418, 10, 11, palette.ASH_GRAY)

    @classmethod
    def report_shot_index_at(cls, timer: float) -> int:
        """Return the fixed 1.2-second report shot for a timestamp."""
        return min(
            len(cls.REPORT_STAGING_ASSETS) - 1,
            max(0, int(max(0.0, timer) / cls.REPORT_SHOT_DURATION)),
        )

    def _draw_home(self) -> None:
        """绘制 home 教程地图、玩家和轻量操作提示。"""
        self.game_surface.fill(palette.NIGHT_BLACK)
        camera_offset = self._camera_offset()
        self.home_tutorial.draw(self.game_surface, camera_offset)
        self.player.draw(self.game_surface, camera_offset)
        self.home_tutorial.draw_foreground(self.game_surface, camera_offset, self.player.rect.bottom)
        self.distortion.draw_overlay(self.game_surface)
        self._draw_home_hint(self.game_surface, camera_offset)
        self._draw_home_status_ui(self.game_surface)
        self.rule_book.draw(self.game_surface)
        self.dialog_box.draw(self.game_surface)

    def _draw_gameplay_context(self, scene_mode: str | None) -> None:
        """在暂停/设置/存档覆盖层下绘制被冻结的可玩场景。"""
        scene = scene_mode if scene_mode in (self.MODE_HOME, self.MODE_PLAYING, self.MODE_GUANGHAN, self.MODE_REPAIR) else None
        if scene is None:
            self.game_surface.fill(palette.NIGHT_BLACK)
            return

        current_mode = self.mode
        self.mode = scene
        try:
            if scene == self.MODE_HOME:
                self._draw_home()
            elif scene == self.MODE_GUANGHAN:
                self._draw_guanghan()
            elif scene == self.MODE_REPAIR:
                self._draw_repair_hall()
            else:
                self._draw_playing()
        finally:
            self.mode = current_mode

    def _draw_settings_background(self) -> None:
        """设置界面复用主菜单或暂停时的场景背景。"""
        if self.settings_return_mode == self.MODE_MAIN_MENU:
            self.main_menu.draw(self.game_surface)
        else:
            self._draw_gameplay_context(self.overlay_audio_mode)

    def _sync_audio_for_mode(self) -> None:
        """让覆盖层沿用来源场景的 BGM，不因打开 UI 触发换曲。"""
        if self.mode in (self.MODE_PAUSE, self.MODE_SETTINGS, self.MODE_SAVE_MENU):
            route_mode = self.overlay_audio_mode
        else:
            route_mode = self.mode
        if route_mode == self.MODE_TRANSITION:
            return
        self.audio.sync_for_game_state(route_mode, self.mainline)

    def _has_active_game_context(self) -> bool:
        """判断菜单叠层下是否仍有可恢复的游戏场景。"""
        if self.mode in (self.MODE_HOME, self.MODE_PLAYING, self.MODE_GUANGHAN, self.MODE_REPAIR, self.MODE_TRANSITION, self.MODE_PAUSE):
            return True
        return self.mode in (self.MODE_SETTINGS, self.MODE_SAVE_MENU) and self.overlay_audio_mode in (
            self.MODE_HOME,
            self.MODE_PLAYING,
            self.MODE_GUANGHAN,
            self.MODE_REPAIR,
        )

    def _higher_priority_ui_active(self) -> bool:
        """暂停键不能抢占 CG、对话、登记、规则书、死亡等活动 UI。"""
        return bool(
            self.dialog_box.active
            or self.rule_book.is_open
            or self.broken_jade_view.active
            or self.envoy_register.active
            or self.report_staging_active
            or self.death_screen.active
            or self.game_state.is_dead()
            or self.repair_door.active
        )

    def _try_open_pause(self) -> bool:
        """在可玩场景的最低 UI 优先级处响应 Esc。"""
        if self.mode not in (self.MODE_HOME, self.MODE_PLAYING, self.MODE_GUANGHAN, self.MODE_REPAIR):
            return False
        if self._higher_priority_ui_active() or not self.input_manager.was_pressed(config.ACTION_QUIT):
            return False
        self.pause_return_mode = self.mode
        self.overlay_audio_mode = self.mode
        self.pause_menu.open()
        self.mode = self.MODE_PAUSE
        return True

    def _update_pause(self, dt: float) -> None:
        """暂停菜单只推进菜单本身；底层游戏逻辑和时钟保持不动。"""
        action = self.pause_menu.update(dt, self.input_manager)
        if action == PAUSE_RESUME:
            self.mode = self.pause_return_mode or self.MODE_PLAYING
        elif action == PAUSE_SAVE:
            self._open_save_menu_from_pause(SAVE_MODE_SAVE)
        elif action == PAUSE_LOAD:
            self._open_save_menu_from_pause(SAVE_MODE_LOAD)
        elif action == PAUSE_SETTINGS:
            self._open_settings(self.MODE_PAUSE)
        elif action == PAUSE_MAIN_MENU:
            self._return_to_main_menu_from_pause()

    def _open_settings(self, return_mode: str) -> None:
        """从主菜单或暂停菜单打开同一个设置实例。"""
        self.settings_return_mode = return_mode
        if return_mode == self.MODE_MAIN_MENU:
            self.overlay_audio_mode = self.MODE_MAIN_MENU
        else:
            self.overlay_audio_mode = self.pause_return_mode or self.MODE_PLAYING
        self.settings_menu.open()
        self.mode = self.MODE_SETTINGS

    def _close_settings(self) -> None:
        """按 Esc/返回键回到进入设置前的界面。"""
        if self.settings_return_mode == self.MODE_PAUSE:
            self.mode = self.MODE_PAUSE
        else:
            self.mode = self.MODE_MAIN_MENU

    def _open_save_menu_from_pause(self, mode: str) -> None:
        """从暂停菜单打开保存或读档页，并保留原场景音频上下文。"""
        self.pending_save_mode = mode
        self.save_menu_return_mode = self.MODE_PAUSE
        self.overlay_audio_mode = self.pause_return_mode or self.MODE_PLAYING
        self.save_menu.open(mode, back_destination="暂停菜单")
        self.mode = self.MODE_SAVE_MENU

    def _return_to_main_menu_from_pause(self) -> None:
        """返回菜单保留最近事件存档，不把未完成挑战写入槽位。"""
        self.audio.stop_repair_sounds()
        self.pause_return_mode = None
        self.save_menu_return_mode = self.MODE_MAIN_MENU
        self.settings_return_mode = self.MODE_MAIN_MENU
        self.overlay_audio_mode = self.MODE_MAIN_MENU
        self.mode = self.MODE_MAIN_MENU

    def _handle_main_menu_action(self, action: str | None) -> None:
        """处理主菜单动作。"""
        if action == MENU_NEW_GAME:
            self.pending_save_mode = SAVE_MODE_NEW
            self.save_menu_return_mode = self.MODE_MAIN_MENU
            self.overlay_audio_mode = self.MODE_MAIN_MENU
            self.save_menu.open(SAVE_MODE_NEW, back_destination="主菜单")
            self.mode = self.MODE_SAVE_MENU
        elif action == MENU_LOAD_GAME:
            self.pending_save_mode = SAVE_MODE_LOAD
            self.save_menu_return_mode = self.MODE_MAIN_MENU
            self.overlay_audio_mode = self.MODE_MAIN_MENU
            self.save_menu.open(SAVE_MODE_LOAD, back_destination="主菜单")
            self.mode = self.MODE_SAVE_MENU
        elif action == MENU_SETTINGS:
            self._open_settings(self.MODE_MAIN_MENU)
        elif action == MENU_DELETE_SAVE:
            self.pending_save_mode = SAVE_MODE_DELETE
            self.save_menu_return_mode = self.MODE_MAIN_MENU
            self.overlay_audio_mode = self.MODE_MAIN_MENU
            self.save_menu.open(SAVE_MODE_DELETE, back_destination="主菜单")
            self.mode = self.MODE_SAVE_MENU
        elif action == MENU_QUIT:
            self.running = False

    def _start_slot(self, slot_id: int, force_new: bool = False) -> None:
        """选择存档槽位后进入开场或正式游戏。"""
        self.current_slot_id = slot_id
        existing_save = None if force_new else self.save_manager.load(slot_id)
        if force_new:
            self.save_manager.delete(slot_id)
        self.current_save_data = existing_save or self.save_manager.default_save(slot_id)
        self._apply_save_data(self.current_save_data)

        if not self.current_save_data.get("opening_seen", False):
            self.opening_cg.start()
            self.mode = self.MODE_OPENING
            return

        ending_id = str(self.mainline.get("ending", ""))
        if ending_id:
            if ending_id in self.ending_cg.CAPTIONS_BY_ENDING:
                self.ending_cg.start(ending_id)
                self.mode = self.MODE_ENDING_CG
            else:
                self.mode = self.MODE_MAIN_MENU
            return

        scene = self._saved_scene(self.current_save_data)
        if scene == self.MODE_HOME:
            self.mode = self.MODE_HOME
            self.audio.sync_for_game_state(self.mode, self.mainline)
        elif scene == self.MODE_GUANGHAN:
            self.mode = self.MODE_GUANGHAN
            self.audio.sync_for_game_state(self.mode, self.mainline)
        elif scene == self.MODE_REPAIR:
            self.mode = self.MODE_REPAIR
            self.audio.sync_for_game_state(self.mode, self.mainline)
        else:
            self._enter_courtyard()

    def _finish_opening(self) -> None:
        """开场播放完或跳过后进入游戏并保存已看状态。"""
        if self.current_save_data is None:
            return
        self.current_save_data["opening_seen"] = True
        self._enter_home()
        self._save_checkpoint("arrival", opening_seen=True)

    def _enter_home(self) -> None:
        """进入穿越后的 home 教程地图。"""
        self.mode = self.MODE_HOME
        self.audio.sync_for_game_state(self.mode, self.mainline)
        self.home_tutorial.reset_player_to_spawn(self.player)

    def _enter_courtyard(self, *, reset_player: bool = False) -> None:
        """进入现有月宫前院正式游戏区。"""
        self.mode = self.MODE_PLAYING
        self.audio.sync_for_game_state(self.mode, self.mainline)
        if reset_player:
            spawn_x, spawn_y = config.COURTYARD_SOUTH_SPAWN
            self.player = Player(spawn_x - config.PLAYER_SIZE[0] // 2, spawn_y - config.PLAYER_SIZE[1])
            self.player.facing = "up"
            self._setup_rule_zones()

    def _finish_home_tutorial(self) -> None:
        """完成 home 教程并播放进入前院的月门转场。"""
        self._start_scene_transition(
            self.MODE_PLAYING,
            self._complete_home_transition,
            "月门正在核验来使身份",
        )

    def _complete_home_transition(self) -> None:
        """转场停顿结束后进入月宫前院。"""
        self._enter_courtyard(reset_player=True)
        self._save_checkpoint("entered_courtyard",
            home_tutorial_done=True,
            home_tutorial=self.home_tutorial.collect_save_data(),
        )

    def _start_scene_transition(
        self,
        target_scene: str,
        on_complete: Callable[[], None],
        caption: str,
    ) -> None:
        """在可玩场景之间统一播放一次转场动画。"""
        source_scene = self.mode
        self._transition_target_scene = target_scene
        self.mode = self.MODE_TRANSITION
        # 转场不是任务完成事件，退出或死亡均保留之前的存档点。
        self.scene_transition.start(
            lambda: self._complete_scene_transition(target_scene, on_complete),
            caption,
            on_found=self._play_transition_found,
        )

    def _play_transition_found(self) -> None:
        """同步播放转场发现音效和可选的手柄震动。"""
        self.audio.play_transition_found()
        self.vibration.trigger(VIBRATION_TRANSITION_FOUND)
        self.distortion.start_shake(4.0, 0.22)

    def _transition_player_state(self, target_scene: str, source_scene: str) -> dict[str, object]:
        """返回转场中断后可安全恢复的目标场景玩家状态。"""
        rect = pygame.Rect(0, 0, *config.PLAYER_SIZE)
        if target_scene == self.MODE_HOME:
            rect.midtop = (
                self.home_tutorial.gate_trigger_rect.centerx,
                self.home_tutorial.gate_trigger_rect.bottom + 8,
            )
            facing = "down"
        elif target_scene == self.MODE_GUANGHAN:
            rect.midbottom = config.GUANGHAN_SOUTH_SPAWN
            facing = "up"
        elif target_scene == self.MODE_PLAYING:
            spawn = (
                config.COURTYARD_NORTH_SPAWN
                if source_scene == self.MODE_GUANGHAN
                else config.COURTYARD_SOUTH_SPAWN
            )
            rect.midbottom = spawn
            facing = "down" if source_scene == self.MODE_GUANGHAN else "up"
        else:
            return {
                "x": self.player.rect.x,
                "y": self.player.rect.y,
                "facing": self.player.facing,
            }
        return {"x": rect.x, "y": rect.y, "facing": facing}

    def _complete_scene_transition(
        self,
        target_scene: str,
        on_complete: Callable[[], None],
    ) -> None:
        """转场结束时切换到目标场景，并确保目标存档场景可恢复。"""
        try:
            self.mode = target_scene
            on_complete()
        finally:
            self._transition_target_scene = None

    def _update_transition(self, dt: float) -> None:
        """推进场景转场，满进度停顿后执行切场景回调。"""
        # Update existing shake before advancing the screen-only transition so
        # a reveal callback that starts a new shake is not consumed by a large
        # catch-up dt in the same frame.
        self.distortion.update(dt)
        if self._transition_target_scene == self.MODE_PLAYING and self._update_return_countdown(dt):
            self.scene_transition.active = False
            self._transition_target_scene = None
            return
        self.scene_transition.update(dt)

    def _apply_save_data(self, data: dict) -> None:
        """把存档数据应用到当前游戏对象。"""
        data = self._migrate_save_data(data)
        self.current_save_data = data
        self._reset_runtime_state()
        player_data = data.get("player", {})
        self.player = Player(player_data.get("x", config.PLAYER_START_X), player_data.get("y", config.PLAYER_START_Y))
        self.player.facing = player_data.get("facing", "down")

        self.game_state.violation_count = data.get("violation_count", 0)
        self.game_state.known_rules = dict(data.get("known_rules", {}))
        self.rule_book.rules = dict(self.game_state.known_rules)
        self.home_tutorial.apply_save_data(data)
        self.mainline = dict(self.DEFAULT_MAINLINE)
        self.mainline.update(data.get("mainline", {}))
        self.repair_hall.reset(bool(self.mainline.get("repair_checked")))
        self.repair_door.reset(bool(self.mainline.get("repair_door_open") or self.mainline.get("repair_checked")))
        # 已读旧规条也同步新增的修月主线，不要求旧玩家重读告示牌。
        if self.home_tutorial.sign_read:
            self.game_state.known_rules.update(BASIC_RULES)
            self.rule_book.rules = dict(self.game_state.known_rules)
        self.broken_jade_view.acquired = bool(self.mainline.get("broken_jade_obtained", False))
        self.broken_jade_view.active = False
        self.rule_book.set_broken_jade_obtained(self.broken_jade_view.acquired)
        saved_scene = self._saved_scene(data)
        if saved_scene == self.MODE_PLAYING:
            self._move_player_outside_moon_pool()
        self.player._clamp_to_world(self._scene_world_size(saved_scene))
        self.report_started = bool(
            self.mainline.get("report_completed") or self.mainline.get("pending_pool_ending")
        )
        self.envoy_register.apply_save_data(data.get("envoy_register", {}))

        self.laurel_tree.set_bleeding(data.get("laurel_tree", {}).get("bleeding", False))
        self.wugang.chop_count = data.get("wugang", {}).get("chop_count", 0)
        self.yutu.is_pounding = data.get("yutu", {}).get("is_pounding", True)
        self.dialog_box.active = False
        self.rule_book.close()
        self.death_screen.active = self.game_state.is_dead()
        self.death_screen.fade_timer = 0.0
        self.report_staging_active = False
        self.report_staging_timer = 0.0
        self.pending_report_dialog = None
        self.palace_wall.set_horror_level(self.game_state.violation_count)
        self.distortion.restore_violation_count(self.game_state.violation_count)
        self._setup_rule_zones()

    def _migrate_save_data(self, data: dict) -> dict:
        """兼容早期平铺字段，并把已离宫存档的旧倒计时收束为稳定状态。"""
        migrated = deepcopy(data)

        envoy_register = migrated.get("envoy_register")
        if not isinstance(envoy_register, dict):
            envoy_register = {}
        if "registered" not in envoy_register and "envoy_registered" in migrated:
            envoy_register["registered"] = migrated["envoy_registered"]
        if "name" not in envoy_register and "envoy_name" in migrated:
            envoy_register["name"] = migrated["envoy_name"]
        migrated["envoy_register"] = envoy_register

        mainline = migrated.get("mainline")
        if not isinstance(mainline, dict):
            mainline = {}
        for key in (
            "report_completed",
            "handoff_completed",
            "return_countdown_active",
            "return_departed_on_time",
            "pending_pool_ending",
            "ending",
        ):
            if key not in mainline and key in migrated:
                mainline[key] = migrated[key]

        if "repair_checked" not in mainline:
            # 先迁移旧版平铺复命字段，再判断是否需要补做新增主线。
            mainline["repair_checked"] = bool(mainline.get("report_completed")
                                               or mainline.get("pending_pool_ending")
                                               or mainline.get("ending"))
        if (migrated.get("scene") == self.MODE_GUANGHAN and not mainline.get("repair_checked")
                and not mainline.get("report_completed") and not mainline.get("pending_pool_ending")):
            migrated["scene"] = self.MODE_PLAYING
            rect = pygame.Rect(0, 0, *config.PLAYER_SIZE)
            rect.midbottom = config.COURTYARD_NORTH_SPAWN
            migrated["player"] = {"x": rect.x, "y": rect.y, "facing": "down"}

        if "handoff_completed" not in mainline:
            # Old saves cannot resume the transient Chang'e dialogue. Once a
            # report had been recorded, restore the route after the handoff
            # so its BGM does not fall back to exploration.
            mainline["handoff_completed"] = bool(
                mainline.get("report_completed")
                or mainline.get("pending_pool_ending")
                or mainline.get("ending")
            )

        if "return_countdown_remaining" not in mainline:
            if "return_countdown" in mainline:
                mainline["return_countdown_remaining"] = mainline["return_countdown"]
            elif "return_countdown" in migrated:
                mainline["return_countdown_remaining"] = migrated["return_countdown"]
        if "return_countdown_remaining" not in mainline:
            mainline["return_countdown_remaining"] = 0.0
        if "return_countdown_active" not in mainline:
            mainline["return_countdown_active"] = bool(
                mainline.get("report_completed") and float(mainline["return_countdown_remaining"]) > 0
            )
        if "return_departed_on_time" not in mainline:
            mainline["return_departed_on_time"] = bool(
                migrated.get("return_to_moon_valley_before_timer", False)
            )

        # 旧版本在月谷仍保留 active=true 时，将其解释为已经及时离宫；
        # 前院存档则保留倒计时，因为现在计时会持续到真正离开前院。
        scene = migrated.get("scene")
        if (
            scene == self.MODE_HOME
            and mainline.get("report_completed")
            and mainline.get("return_countdown_active")
            and not mainline.get("pending_pool_ending")
        ):
            mainline["return_departed_on_time"] = True
        if mainline.get("return_departed_on_time"):
            mainline["return_countdown_active"] = False
            mainline["return_countdown_remaining"] = 0.0

        # 旧版本把双污染结局写成 be_laurel_mixed；运行时规范名改为
        # be_double，但保留旧存档的可读性和继续播放能力。
        for key in ("pending_pool_ending", "ending"):
            if mainline.get(key) == "be_laurel_mixed":
                mainline[key] = "be_double"

        migrated["mainline"] = mainline
        return migrated

    def _reset_runtime_state(self) -> None:
        """切换槽位时清除不会写入存档的动画、交互和音频状态。"""
        self.audio.stop_ambient()
        self.audio.stop_cg_sounds()
        self.audio.stop_repair_sounds()
        self.repair_hall.reset()
        self.repair_door.reset()
        self.checkpoint_notice = 0.0
        self.opening_cg.active = False
        self.ending_cg.active = False
        self.scene_transition.active = False
        self._transition_target_scene = None
        self.wugang.player_in_range = False
        self.wugang.dialog_active = False
        self.wugang._timer = 0.0
        self.wugang.resting_timer = 0.0
        self.wugang.anim_state = "chop"
        self.wugang.current_frame = 0
        self.yutu.player_in_range = False
        self.yutu.dialog_active = False
        self.yutu._timer = 0.0
        self.yutu.current_frame = 0
        self.moon_pool._time = 0.0
        self.moon_pool.reflection_flash_timer = 0.0
        self.moon_pool.gaze_progress = 0.0
        self.laurel_tree._time = 0.0
        self.palace_wall._time = 0.0
        self._chang_e_time = 0.0

    def _move_player_outside_moon_pool(self) -> None:
        """迁移旧存档中落在中央月池碰撞区里的玩家。"""
        if not self.player.rect.colliderect(self.moon_pool.rect):
            return
        self.player.rect.midtop = (self.moon_pool.rect.centerx, self.moon_pool.rect.bottom + 12)
        self.player.position.xy = self.player.rect.topleft

    def _collect_save_data(self, **overrides) -> dict:
        """收集当前可保存状态。"""
        data = dict(self.current_save_data or {})
        data.update(
            {
                "opening_seen": data.get("opening_seen", False),
                "home_tutorial_done": data.get("home_tutorial_done", False),
                "scene": self._current_save_scene(data),
                "home_tutorial": self.home_tutorial.collect_save_data(),
                "mainline": dict(self.mainline),
                "envoy_register": self.envoy_register.collect_save_data(),
                "player": {
                    "x": self.player.rect.x,
                    "y": self.player.rect.y,
                    "facing": self.player.facing,
                },
                "violation_count": self.game_state.violation_count,
                "known_rules": dict(self.game_state.known_rules),
                "laurel_tree": {"bleeding": self.laurel_tree.bleeding},
                "wugang": {"chop_count": self.wugang.chop_count},
                "yutu": {"is_pounding": self.yutu.is_pounding},
            }
        )
        data.update(overrides)
        return data

    def _current_save_scene(self, previous_data: dict) -> str:
        """把临时 UI/转场模式归一化为可恢复的剧情场景。"""
        if self.mode in (self.MODE_HOME, self.MODE_PLAYING, self.MODE_GUANGHAN, self.MODE_REPAIR):
            return self.mode
        if self.mode in (self.MODE_PAUSE, self.MODE_SETTINGS, self.MODE_SAVE_MENU):
            if self.overlay_audio_mode in (self.MODE_HOME, self.MODE_PLAYING, self.MODE_GUANGHAN, self.MODE_REPAIR):
                return self.overlay_audio_mode
        if self.mode == self.MODE_TRANSITION:
            if self._transition_target_scene in (
                self.MODE_HOME,
                self.MODE_PLAYING,
                self.MODE_GUANGHAN,
            ):
                return self._transition_target_scene
            return self.MODE_PLAYING
        previous_scene = previous_data.get("scene")
        if previous_scene in (self.MODE_HOME, self.MODE_PLAYING, self.MODE_GUANGHAN, self.MODE_REPAIR):
            return previous_scene
        return self.MODE_HOME if not previous_data.get("home_tutorial_done", False) else self.MODE_PLAYING

    def _saved_scene(self, data: dict) -> str:
        """读取显式场景；旧存档根据教程和复命状态做保守迁移。"""
        scene = data.get("scene")
        valid_scenes = (self.MODE_HOME, self.MODE_PLAYING, self.MODE_GUANGHAN, self.MODE_REPAIR)
        if scene in valid_scenes:
            return scene
        if not data.get("home_tutorial_done", False):
            return self.MODE_HOME
        mainline = data.get("mainline", {})
        if mainline.get("pending_pool_ending") or mainline.get("return_countdown_active"):
            return self.MODE_GUANGHAN
        return self.MODE_PLAYING

    def _save_current_slot(self, **overrides) -> None:
        """保存当前槽位；未选择槽位时静默跳过。"""
        if self.current_slot_id is None:
            return
        self.current_save_data = self.save_manager.save(
            self.current_slot_id,
            self._collect_save_data(**overrides),
        )
        self.save_menu.refresh()

    def _save_checkpoint(self, checkpoint_id: str, **overrides) -> None:
        """每个完成事件只保存一次；挑战的临时状态永远不序列化。"""
        completed = list((self.current_save_data or {}).get("checkpoint_events", []))
        if checkpoint_id in completed:
            return
        completed.append(checkpoint_id)
        self._save_current_slot(checkpoint_id=checkpoint_id, checkpoint_events=completed,
                                checkpoint_version=1, **overrides)
        self.checkpoint_notice = 3.0

    def _save_game_to_slot(self, slot_id: int) -> None:
        """手动保存复制最近事件存档，不能在限时任务中制造额外检查点。"""
        payload = deepcopy(self.current_save_data or self.save_manager.default_save(slot_id))
        self.current_slot_id = slot_id
        self.current_save_data = self.save_manager.save(slot_id, payload)
        self.save_menu.refresh()
        self.save_menu.show_message(f"槽位 {slot_id} 已保存最近事件")

    def _draw_home_hint(self, surface: pygame.Surface, camera_offset: tuple[int, int]) -> None:
        """绘制 home 场景中的 E 交互提示。"""
        if self.dialog_box.active or self.rule_book.is_open:
            return
        if not self.home_tutorial.sign_interaction_rect.colliderect(self.player.rect):
            return

        rect = self.home_tutorial.sign_rect.move(camera_offset)
        hint_rect = pygame.Rect(rect.centerx - 19, rect.y - 19, 38, 16)
        draw_filled_rect(surface, hint_rect, palette.BLACK)
        draw_double_rect(surface, hint_rect, palette.MOON_WHITE, palette.DEEP_BLUE)
        render_text(surface, "E", hint_rect.x + 15, hint_rect.y + 2, 11, palette.MOON_WHITE)

    def _draw_home_status_ui(self, surface: pygame.Surface) -> None:
        """绘制 home 场景的明确操作提示。"""
        if self.dialog_box.active:
            return
        if not self.home_tutorial.sign_read:
            text = "E/空格 读取告示牌"
        elif not self.home_tutorial.rules_briefing_complete:
            text = "读完全部规条后开启月宫门"
        else:
            text = "月宫门已开，向上进入"

        draw_filled_rect(surface, (4, config.SCREEN_HEIGHT - 22, 210, 16), palette.BLACK)
        draw_rect(surface, 4, config.SCREEN_HEIGHT - 22, 210, 16, palette.DEEP_BLUE)
        render_text(surface, text, 8, config.SCREEN_HEIGHT - 18, 12, palette.MOON_WHITE)

    def _draw_return_countdown_hud(self, surface: pygame.Surface) -> None:
        """绘制复命后的候月倒计时，保持文案有误导性但不直说逃离。"""
        if self.mode not in (self.MODE_GUANGHAN, self.MODE_PLAYING):
            return
        if not self.mainline.get("return_countdown_active", False):
            return
        remaining = max(0, int(float(self.mainline.get("return_countdown_remaining", 0.0))))
        minutes = remaining // 60
        seconds = remaining % 60
        text = f"候月 {minutes:02d}:{seconds:02d}"
        panel = pygame.Rect(config.SCREEN_WIDTH - 118, 8, 110, 22)
        draw_filled_rect(surface, panel, palette.BLACK)
        draw_double_rect(surface, panel, palette.MOON_WHITE, palette.DARK_BLOOD)
        render_text(surface, text, panel.x + 12, panel.y + 5, 13, palette.PALE_MOON)

    def _setup_rule_zones(self) -> None:
        """创建 Demo 规则触发区。"""
        self.moon_pool.gaze_progress = 0.0
        tree_rule_center, tree_rule_radius = self.laurel_tree.get_rule_circle()
        self.tree_bow_zone = CircularTriggerZone(
            tree_rule_center,
            tree_rule_radius,
            RULE_BOW_TO_TREE,
            trigger_type="enter",
            cooldown=2.0,
        )
        self.pool_reflection_zone = TriggerZone(
            self.moon_pool.reflection_rect,
            RULE_POOL_REFLECTION,
            trigger_type="stay",
            cooldown=1.2,
            required_stay=2.5,
        )
        self.yutu_eye_zone = TriggerZone(
            self.yutu.interaction_rect.inflate(12, 12),
            RULE_NO_EYE_CONTACT,
            trigger_type="stay",
            cooldown=1.5,
            required_stay=0.65,
        )
        self.palace_run_zone = TriggerZone(
            pygame.Rect(0, self.palace_wall.get_collision_rect().bottom, config.COURTYARD_WIDTH, 40),
            PSEUDO_RULE_YUTU_WATCH,
            trigger_type="stay",
            cooldown=1.2,
            required_stay=0.65,
        )

    def _update_rule_checks(self, dt: float) -> None:
        """执行基础 Demo 规则检测并通过 RuleEngine 记录违规。"""
        if self.game_state.is_dead():
            return

        if self.laurel_tree.bleeding:
            # 流血自修窗口允许安全靠近；结束后留一秒撤离宽限。
            self.tree_bow_zone.reset()
            self._tree_was_bleeding = True
            self._tree_safe_exit_grace = 0.0
        elif self._tree_was_bleeding:
            self._tree_was_bleeding = False
            self._tree_safe_exit_grace = 1.0
            self.tree_bow_zone.reset()
        elif self._tree_safe_exit_grace > 0.0:
            self._tree_safe_exit_grace = max(0.0, self._tree_safe_exit_grace - dt)
            self.tree_bow_zone.reset()
        elif self.tree_bow_zone.update(dt, self.player.rect):
            self.rule_engine.check_rule(RULE_BOW_TO_TREE, {"too_close": True})
            if self.game_state.is_dead():
                return

        staring_reflection = not self.player.is_moving() and self._player_faces_pool()
        pool_target = self.player.rect if staring_reflection else pygame.Rect(-9999, -9999, 1, 1)
        pool_triggered = self.pool_reflection_zone.update(dt, pool_target)
        self.moon_pool.gaze_progress = self.pool_reflection_zone.stay_progress
        if pool_triggered:
            self.moon_pool.flash_reflection()
            first_broken_jade_acquisition = not self.mainline.get("broken_jade_obtained", False)
            if first_broken_jade_acquisition:
                # Commit the collectible before the rule check emits the
                # third-violation death event.  The death flow can therefore
                # never erase the acquisition from the save payload.
                self.mainline["broken_jade_obtained"] = True
                self.broken_jade_view.acquire()
                self.rule_book.set_broken_jade_obtained(True)
            self.rule_engine.check_rule(
                RULE_POOL_REFLECTION,
                {"staring_reflection": True},
            )
            if first_broken_jade_acquisition:
                # Collection is a checkpoint, but a third-violation snapshot must
                # never reload dead or immediately gaze into the same pool again.
                safe_rect = self.player.rect.copy()
                safe_rect.midtop = (self.moon_pool.rect.centerx, self.moon_pool.rect.bottom + 12)
                self._save_checkpoint("broken_jade_obtained",
                    violation_count=min(self.game_state.violation_count, 2),
                    player={"x": safe_rect.x, "y": safe_rect.y, "facing": "down"})
            if self.game_state.is_dead():
                # Death owns input/update flow from this point onward; the
                # acquisition state remains committed and the pickup overlay
                # stays observable until the death restart closes it.
                return

        eye_contact = (
            self.yutu.is_pounding
            and self._is_player_in_yutu_front_arc()
            and is_facing_rect(self.player.rect, self.player.facing, self.yutu.get_collision_rect())
        )
        eye_target = self.player.rect if eye_contact else pygame.Rect(-9999, -9999, 1, 1)
        if self.yutu_eye_zone.update(dt, eye_target):
            self.rule_engine.check_rule(
                RULE_NO_EYE_CONTACT,
                {
                    "yutu_pounding": True,
                    "facing_yutu": True,
                },
            )
            if self.game_state.is_dead():
                return

        running = self.input_manager.is_pressed(config.ACTION_RUN) and self.player.is_moving()
        run_target = self.player.rect if running else pygame.Rect(-9999, -9999, 1, 1)
        if self.palace_run_zone.update(dt, run_target):
            self.rule_engine.check_pseudo_rule(
                PSEUDO_RULE_YUTU_WATCH,
                {
                    "running_near_palace": True
                },
            )
            if self.game_state.is_dead():
                return

        self._check_tree_bleeding_rule(dt)

    def _player_faces_pool(self) -> bool:
        """玩家处于倒影区并朝向月池时显示实时倒影。"""
        return self.moon_pool.reflection_rect.colliderect(self.player.rect) and is_facing_rect(
            self.player.rect,
            self.player.facing,
            self.moon_pool.rect,
        )

    def _check_tree_bleeding_rule(self, dt: float) -> None:
        """月桂流血时处于 10 秒自修复窗口，不再伤害主角。"""
        _ = dt
        return

    def _check_palace_entry(self) -> bool:
        """站到广寒宫门前时，根据职司检查进度决定是否入殿。"""
        if self.game_state.is_dead():
            return False
        if not self.palace_entry_rect.colliderect(self.player.rect):
            return False

        if self.mainline.get("pending_pool_ending"):
            self.event_bus.emit(
                SHOW_DIALOG,
                speaker_id="palace_gate",
                lines=[
                    "池水尚未照验，广寒宫不再收回这份复命。",
                    "先去月池完成裁决，南门暂不通往月谷。",
                ],
            )
            return True

        if self.mainline.get("return_departed_on_time"):
            self.event_bus.emit(
                SHOW_DIALOG,
                speaker_id="palace_gate",
                lines=[
                    "复命既毕，来使不得重入广寒宫。",
                    "请回月谷祭坛，归路正在等你。",
                ],
            )
            return True

        if not self._office_checks_complete():
            missing = [name for key, name in (("wugang_checked", "吴刚伐桂"),
                       ("yutu_checked", "玉兔捣药"), ("repair_checked", "偏殿修月"))
                       if not self.mainline.get(key)]
            self.event_bus.emit(
                SHOW_DIALOG,
                speaker_id="palace_gate",
                lines=[
                    "宫门里的月光没有让路。",
                    "验职未齐，广寒宫不受复命。",
                    "尚缺：" + "、".join(missing) + "。",
                ],
            )
            return True

        self._start_scene_transition(
            self.MODE_GUANGHAN,
            self._enter_guanghan,
            "广寒宫正在核验来使记录",
        )
        return True

    def _office_checks_complete(self) -> bool:
        """伐桂、捣药、修月三项均完成时，广寒宫才接受复命。"""
        return not self.game_state.is_dead() and bool(
            self.mainline["wugang_checked"] and self.mainline["yutu_checked"] and self.mainline["repair_checked"]
        )

    def _enter_guanghan(self) -> None:
        """进入广寒宫内殿。"""
        self.mode = self.MODE_GUANGHAN
        self.audio.sync_for_game_state(self.mode, self.mainline)
        self.report_started = False
        self.player.rect.midbottom = config.GUANGHAN_SOUTH_SPAWN
        self.player.position.xy = self.player.rect.topleft
        self.player.facing = "up"

    def _begin_guanghan_report(self) -> None:
        """玩家主动靠近嫦娥后才开始复命，保留入殿探索窗口。"""
        if self.game_state.is_dead():
            return
        if not self._office_checks_complete():
            self.event_bus.emit(
                SHOW_DIALOG,
                speaker_id="change",
                lines=["伐桂、捣药、修月三项尚未验齐，来使不可复命。"],
            )
            return
        self.report_started = True
        if self.mainline["wugang_polluted"] or self.mainline["yutu_polluted"]:
            self._start_polluted_report()
        else:
            self._start_normal_report()

    def _start_polluted_report(self) -> None:
        """污染状态下正常复命，但只留下池边异常的待触发结局。"""
        if self.game_state.is_dead():
            return
        wugang_polluted = self.mainline.get("wugang_polluted", False)
        yutu_polluted = self.mainline.get("yutu_polluted", False)
        self.mainline["report_completed"] = False
        self.mainline["handoff_completed"] = False
        self.mainline["return_departed_on_time"] = False
        self.mainline["return_countdown_active"] = False
        self.mainline["return_countdown_remaining"] = 0.0
        self.mainline["pending_pool_ending"] = ""
        if wugang_polluted and yutu_polluted:
            self.mainline["pending_pool_ending"] = "be_double"
            caption = "两份记录在月光中叠成同一处污痕。"
            lines = [
                "嫦娥隔着帘影听完复命。",
                "伐桂、捣药、修月三职，皆已验毕。",
                "使者可返月谷。只是月光会先照见使者自己。",
                "出去吧，池水会替月宫收下多余的记录。",
            ]
        elif wugang_polluted:
            self.mainline["pending_pool_ending"] = "be_wugang"
            caption = "伐桂记录递上时，纸边渗出一线木色。"
            lines = [
                "嫦娥没有追问伐桂的细节。",
                "使者已验过吴刚，月宫也会验使者。",
                "出去吧。到池边照一照，便知道斧声该归在哪里。",
            ]
        else:
            self.mainline["pending_pool_ending"] = "be_yutu"
            caption = "捣药记录递上时，药雾先落进影子里。"
            lines = [
                "嫦娥没有追问捣药的细节。",
                "使者已验过玉兔，月宫也会验使者。",
                "出去吧。到池边照一照，便知道药香该归在哪里。",
            ]
        self._start_report_staging("change", lines, caption)

    def _start_report_staging(self, speaker_id: str, lines: list[str], caption: str) -> None:
        """进入复命 CG 过场，结束后再打开正式复命对话。"""
        self.dialog_box.active = False
        self.report_staging_active = True
        self.report_staging_timer = 0.0
        self.pending_report_dialog = (speaker_id, list(lines), caption)
        self._report_audio_cues_played.clear()
        self.audio.begin_cg_cycle()
        self._emit_report_audio_cues()

    def _update_report_staging(self, dt: float) -> None:
        """推进或跳过复命 staging CG。"""
        if not self.report_staging_active:
            return
        self.report_staging_timer = min(
            self.report_staging_duration,
            self.report_staging_timer + max(0.0, dt),
        )
        self._emit_report_audio_cues()
        if self.input_manager.was_pressed(config.ACTION_INTERACT) or self.report_staging_timer >= self.report_staging_duration - 1e-6:
            self._finish_report_staging()

    def _finish_report_staging(self) -> None:
        """复命 staging 结束后打开排队的嫦娥对话。"""
        if not self.pending_report_dialog:
            self.report_staging_active = False
            return
        speaker_id, lines, _caption = self.pending_report_dialog
        self.report_staging_active = False
        self.report_staging_timer = 0.0
        self.pending_report_dialog = None
        self._report_audio_cues_played.clear()
        self.audio.stop_cg_sounds()
        self.event_bus.emit(SHOW_DIALOG, speaker_id=speaker_id, lines=lines)

    def _mark_handoff_completed_if_closed(self, was_dialog_active: bool) -> None:
        """Mark the Chang'e handoff only after its final dialogue line closes."""
        if not was_dialog_active or self.dialog_box.active:
            return
        if self.report_staging_active or not self.report_started:
            return
        if self.mainline.get("handoff_completed"):
            return
        if self.dialog_box.speaker_id != "change":
            return
        self.mainline["handoff_completed"] = True
        self._save_checkpoint("report_completed")

    def _emit_report_audio_cues(self) -> None:
        """Trigger report shot cues once, including when a frame skips a boundary."""
        for boundary, key in self.REPORT_AUDIO_CUES:
            token = f"report:{boundary}:{key}"
            if self.report_staging_timer >= boundary and token not in self._report_audio_cues_played:
                self._report_audio_cues_played.add(token)
                self.audio.play_cg_cue(key, token=token)

    def _try_trigger_pending_pool_ending(self) -> bool:
        """污染复命结束后，离殿触发池边异常 BE。"""
        if self.game_state.is_dead():
            return False
        pending_ending = self.mainline.get("pending_pool_ending", "")
        if not pending_ending or self.mainline.get("ending"):
            return False

        self.mainline["pending_pool_ending"] = ""
        self.mainline["ending"] = pending_ending
        self.moon_pool.flash_reflection(2.0)
        self.dialog_box.active = False
        self.ending_cg.start(pending_ending)
        self.audio.stop_legacy_ambient()
        self.mode = self.MODE_ENDING_CG
        return True

    def _try_leave_guanghan_after_report(self) -> bool:
        """正常复命后离开内殿，先回到广寒宫广场。"""
        if self.game_state.is_dead():
            return False
        if self.mainline.get("ending"):
            return False
        has_pending_pool_ending = bool(self.mainline.get("pending_pool_ending"))
        if not has_pending_pool_ending:
            if not self.mainline.get("report_completed", False):
                return False
            if not self.mainline.get("return_countdown_active", False):
                return False
            if float(self.mainline.get("return_countdown_remaining", 0.0)) <= 0.0:
                return False
            # 这里只是离开内殿，候月计时要继续覆盖前院和真正离宫的路程。

        self._start_scene_transition(
            self.MODE_PLAYING,
            self._complete_guanghan_departure,
            "宫门正在放回来使",
        )
        return True

    def _complete_guanghan_departure(self) -> None:
        """转场结束后把来使放回广寒宫前院。"""
        self.dialog_box.active = False
        self.player.rect.midbottom = config.COURTYARD_NORTH_SPAWN
        self.player.position.xy = self.player.rect.topleft
        self.player.facing = "down"

    def _leave_courtyard_to_home(self) -> None:
        """从广场南门返回月谷，保持两道门的空间顺序。"""
        if self.game_state.is_dead():
            return
        if self.mainline.get("pending_pool_ending"):
            self._show_courtyard_exit_blocked_for_pool()
            return
        if not self.mainline.get("return_departed_on_time", False):
            if (
                self.mainline.get("return_countdown_active", False)
                and float(self.mainline.get("return_countdown_remaining", 0.0)) > 0.0
            ):
                # 南门才是离开月宫的时点；在这里确认离宫并停止候月计时。
                self.mainline["return_departed_on_time"] = True
                self.mainline["return_countdown_active"] = False
                self.mainline["return_countdown_remaining"] = 0.0
                self._save_checkpoint("departed_palace")
            else:
                self.event_bus.emit(
                    SHOW_DIALOG,
                    speaker_id="courtyard_gate",
                    lines=[
                        "复命未毕，南门的月光不通。",
                        "先入广寒宫复命，再返月谷。",
                    ],
                )
                return
        self._start_scene_transition(
            self.MODE_HOME,
            self._complete_courtyard_home_return,
            "月谷的归路正在显形",
        )

    def _complete_courtyard_home_return(self) -> None:
        """转场结束后把来使送回月谷南门。"""
        self.dialog_box.active = False
        self.player.rect.midtop = (
            self.home_tutorial.gate_trigger_rect.centerx,
            self.home_tutorial.gate_trigger_rect.bottom + 8,
        )
        self.player.position.xy = self.player.rect.topleft
        self.player.facing = "down"

    def _show_courtyard_exit_blocked_for_pool(self) -> None:
        """污染复命待裁决时，明确告知玩家必须去月池。"""
        self.event_bus.emit(
            SHOW_DIALOG,
            speaker_id="courtyard_gate",
            lines=[
                "月池尚未照验，南门被月光封住。",
                "先去月池完成裁决，来使不得返月谷。",
            ],
        )

    def _update_return_countdown(self, dt: float) -> bool:
        """推进复命后的候月倒计时；归零时触发嫦娥 BE。"""
        if self.game_state.is_dead():
            return False
        countdown_scene_active = self.mode in (self.MODE_GUANGHAN, self.MODE_PLAYING)
        if self.mode == self.MODE_TRANSITION:
            countdown_scene_active = self._transition_target_scene == self.MODE_PLAYING
        if not countdown_scene_active or self.mainline.get("return_departed_on_time", False):
            return False
        if not self.mainline.get("return_countdown_active", False):
            return False
        remaining = float(self.mainline.get("return_countdown_remaining", 0.0))
        self.mainline["return_countdown_remaining"] = max(0.0, remaining - dt)
        if self.mainline["return_countdown_remaining"] <= 0.0:
            self._trigger_change_ending()
            return True
        return False

    def _try_trigger_he_return(self) -> bool:
        """完成清白复命、及时离宫并回到月谷祭坛后触发 HE。"""
        if self.game_state.is_dead():
            return False
        if self.mainline.get("ending"):
            return False
        if not self.mainline.get("report_completed", False):
            return False
        if self.mainline.get("wugang_polluted") or self.mainline.get("yutu_polluted"):
            return False
        if self.mainline.get("pending_pool_ending"):
            return False
        if not self.mainline.get("return_departed_on_time", False):
            return False
        if self.mode != self.MODE_HOME or not self.home_tutorial.altar_rect.colliderect(self.player.rect):
            return False

        self.mainline["return_countdown_active"] = False
        self.mainline["return_countdown_remaining"] = 0.0
        self.mainline["ending"] = "he_return_earth"
        self.dialog_box.active = False
        self.ending_cg.start("he_return_earth")
        self.audio.stop_legacy_ambient()
        self.mode = self.MODE_ENDING_CG
        self._save_checkpoint("returned_earth")
        return True
    def _trigger_change_ending(self) -> None:
        """候月倒计时归零后，触发取代嫦娥 BE。"""
        if self.game_state.is_dead():
            return
        if self.mainline.get("ending"):
            return
        self.mainline["return_countdown_active"] = False
        self.mainline["return_countdown_remaining"] = 0.0
        self.mainline["ending"] = "be_change"
        self.dialog_box.active = False
        self.rule_book.close()
        self.envoy_register.close()
        self.report_staging_active = False
        self.report_staging_timer = 0.0
        self.pending_report_dialog = None
        self._report_audio_cues_played.clear()
        self.scene_transition.active = False
        self._transition_target_scene = None
        self.ending_cg.start("be_change")
        self.audio.stop_legacy_ambient()
        self.mode = self.MODE_ENDING_CG
    def _start_normal_report(self) -> None:
        """无污染时完成正常复命，并启动候月倒计时。"""
        if self.game_state.is_dead():
            return
        self.mainline["report_completed"] = True
        self.mainline["handoff_completed"] = False
        self.mainline["return_departed_on_time"] = False
        self.mainline["return_countdown_active"] = True
        self.mainline["return_countdown_remaining"] = 60.0
        self.mainline["pending_pool_ending"] = ""
        self._start_report_staging(
            "change",
            [
                "嫦娥没有看你，她看着你身后的月光。",
                "吴刚斧声未绝，玉兔杵声未停。",
                "偏殿旧月已封，三项查验俱全。",
                "来使的记录，月宫收下了。",
                "复命既毕，使者可候月落。",
                "待这一轮月光尽了，归路自会显明。",
            ],
            "两份职司记录与修月封验一并呈入广寒宫。",
        )
    def _try_complete_wugang_check(self) -> bool:
        """月桂流血时，允许来使通过对话选项完成伐桂检查。"""
        if self.game_state.is_dead():
            return False
        if self.wugang.dialog_active or not self.wugang.player_in_range:
            return False
        if not self.laurel_tree.bleeding:
            return False
        if self.mainline.get("wugang_checked", False):
            self.event_bus.emit(
                SHOW_DIALOG,
                speaker_id="wugang",
                lines=["伐桂职司已经记入来使簿。", "吴刚重新举斧，月桂的血色没有退去。"],
            )
            return True

        self.event_bus.emit(
            SHOW_DIALOG,
            speaker_id="wugang",
            lines=[
                "吴刚停了一息，斧刃上的月光像冷铁。",
                "来使，看清楚。斧未绝，桂未亡。",
                "来使簿在你手中翻到伐桂一页。",
            ],
            choices=[
                {"id": "wugang_overstep", "text": "落闻斧鸣，载其木痕"},
                {"id": "wugang_record", "text": "视桂泣血，载其斫桂"},
            ],
            choice_context="wugang_check",
        )
        return True

    def _try_handle_yutu_check(self) -> bool:
        """从玉兔身后完成捣药检查；正面接触只记普通违规。"""
        if self.game_state.is_dead():
            return False
        if self.yutu.dialog_active or not self.yutu.player_in_range:
            return False

        if self._is_player_in_yutu_front_arc():
            self.game_state.add_violation(RULE_NO_EYE_CONTACT)
            if not self.game_state.is_dead():
                self.event_bus.emit(
                    SHOW_DIALOG,
                    speaker_id="yutu",
                    lines=[
                        "玉兔的药杵骤然停住，红眼正对着来使。",
                        "方向错了。绕到身后，只记录杵声与药色。",
                    ],
                )
            return True

        if not self._is_player_behind_yutu():
            return False

        if self.mainline.get("yutu_checked", False):
            self.event_bus.emit(
                SHOW_DIALOG,
                speaker_id="yutu",
                lines=["捣药职司已经记入来使簿。", "玉兔的药杵仍按原来的节奏落下。"],
            )
            return True

        self.event_bus.emit(
            SHOW_DIALOG,
            speaker_id="yutu",
            lines=[
                "玉兔的耳尖动了一下，药杵仍按同一节奏落下。",
                "来使站在那里就好。药不认脸，只认手。",
                "来使簿在你手中翻到捣药一页。",
            ],
            choices=[
                {"id": "yutu_overstep", "text": "闻嗅药香，记其丹成"},
                {"id": "yutu_record", "text": "睹其落杵，记其药色"},
            ],
            choice_context="yutu_check",
        )
        return True

    def _is_player_in_yutu_front_arc(self) -> bool:
        """玉兔大图面朝左，左侧才是正面/对视危险区。"""
        body = self.yutu.get_collision_rect()
        vertical_distance = abs(self.player.rect.centery - body.centery)
        return self.player.rect.centerx <= body.left and vertical_distance <= 16

    def _is_player_behind_yutu(self) -> bool:
        """除左侧正面对视区外，上、下和右后方都允许完成检查。"""
        return not self._is_player_in_yutu_front_arc()

    def _on_dialog_choice_selected(self, speaker_id: str, choice_id: str, **payload) -> None:
        """处理主线对话选项结果。"""
        _ = speaker_id, payload
        if self.game_state.is_dead():
            return
        if choice_id == "wugang_record":
            self._complete_wugang_check(polluted=False)
        elif choice_id == "wugang_overstep":
            self._complete_wugang_check(polluted=True)
        elif choice_id == "yutu_record":
            self._complete_yutu_check(polluted=False)
        elif choice_id == "yutu_overstep":
            self._complete_yutu_check(polluted=True)

    def _complete_wugang_check(self, polluted: bool) -> None:
        """写入吴刚检查结果并播放对应反馈。"""
        if self.game_state.is_dead():
            return
        self.mainline["wugang_checked"] = True
        if polluted:
            self.mainline["wugang_polluted"] = True
            lines = [
                "你替斧声续记一响。",
                "吴刚没有阻止，只是把斧柄从你影子里抽回去。",
                "已记：伐桂职司仍续。",
                "伐桂记录边缘渗出木色。",
            ]
        else:
            lines = [
                "你只记录，不执斧。",
                "吴刚低声笑了一下，像斧刃擦过树皮。",
                "已记：伐桂职司仍续。斧声未绝，月桂未亡。",
                "三验俱全，去广寒宫复命吧。" if self._office_checks_complete()
                else "三验未齐时，宫门不会放行。照着告示，将余下的差事办完。",
            ]
        self.event_bus.emit(SHOW_DIALOG, speaker_id="wugang", lines=lines)
        self._save_checkpoint("wugang_completed")

    def _complete_yutu_check(self, polluted: bool) -> None:
        """写入玉兔检查结果并播放对应反馈。"""
        if self.game_state.is_dead():
            return
        self.mainline["yutu_checked"] = True
        if polluted:
            self.mainline["yutu_polluted"] = True
            lines = [
                "你近闻药香，替玉兔确认药成。",
                "药雾没有进入口鼻，却先在影子的眼眶里沉下去。",
                "已记：捣药职司仍续。",
                "药簿记录边缘泛白。",
            ]
        else:
            lines = [
                "你只记录药色与杵声，没有替它确认药成。",
                "玉兔没有回头，药臼里传出一声很轻的空响。",
                "已记：捣药职司仍续。杵声未停，药未由来使试验。",
                "伐桂、捣药、修月俱验，才算来使的差事办全。",
            ]
        self.event_bus.emit(SHOW_DIALOG, speaker_id="yutu", lines=lines)
        self._save_checkpoint("yutu_completed")

    def _get_collision_rects(self) -> list[pygame.Rect]:
        """收集地图、世界物体和 NPC 碰撞。"""
        rects = [obj.get_collision_rect() for obj in self.world_objects]
        rects.extend(self.repair_door.collision_rects())
        rects.extend(npc.get_collision_rect() for npc in self.npcs)
        # 南门正常路线保留中央交互口；污染待裁决时整段南墙封闭，必须去月池。
        if self.mainline.get("pending_pool_ending"):
            rects.append(pygame.Rect(0, 420, config.COURTYARD_WIDTH, config.COURTYARD_HEIGHT - 420))
        else:
            rects.extend(
                [
                    pygame.Rect(
                        0,
                        420,
                        self.courtyard_south_exit_rect.left,
                        config.COURTYARD_HEIGHT - 420,
                    ),
                    pygame.Rect(
                        self.courtyard_south_exit_rect.right,
                        420,
                        config.COURTYARD_WIDTH - self.courtyard_south_exit_rect.right,
                        config.COURTYARD_HEIGHT - 420,
                    ),
                    pygame.Rect(
                        self.courtyard_south_exit_rect.left,
                        420,
                        self.courtyard_south_exit_rect.width,
                        config.COURTYARD_HEIGHT - 420,
                    ),
                ]
            )
        return rects

    def _draw_palace_entry_marker(self, surface: pygame.Surface, camera_offset: tuple[int, int]) -> None:
        """玩家接近时显示轻量宫门标签，不遮挡门体。"""
        rect = self.palace_entry_rect.move(camera_offset)
        nearby = self.player.rect.inflate(144, 96).colliderect(self.palace_entry_rect)
        if nearby and not self.palace_entry_rect.colliderect(self.player.rect):
            label_rect = pygame.Rect(rect.centerx - 42, rect.y - 17, 84, 13)
            draw_filled_rect(surface, label_rect, palette.BLACK)
            draw_rect(surface, label_rect.x, label_rect.y, label_rect.width, label_rect.height, palette.DEEP_BLUE)
            render_text(surface, "广寒宫内殿", label_rect.x + 10, label_rect.y + 2, 11, palette.PALE_MOON)

    def _draw_interaction_hint(self, surface: pygame.Surface) -> None:
        """绘制可交互目标附近的临时 E 提示。"""
        hint_rect = self._interaction_hint_rect()
        if hint_rect is None:
            return

        draw_filled_rect(surface, hint_rect, palette.BLACK)
        draw_double_rect(surface, hint_rect, palette.MOON_WHITE, palette.DARK_BLOOD)
        x = hint_rect.x + 12
        y = hint_rect.y + 3
        draw_filled_rect(surface, (x, y, 6, 1), palette.MOON_WHITE)
        draw_filled_rect(surface, (x, y + 2, 5, 1), palette.MOON_WHITE)
        draw_filled_rect(surface, (x, y + 4, 6, 1), palette.MOON_WHITE)
        draw_filled_rect(surface, (x, y, 1, 5), palette.MOON_WHITE)

    def _interaction_hint_rect(self) -> pygame.Rect | None:
        """计算门或 NPC 的 E 提示位置，门提示严格居中。"""
        if self.dialog_box.active or self.rule_book.is_open or self.death_screen.active:
            return None

        camera_x, camera_y = self._camera_offset()
        if self.courtyard_south_exit_rect.colliderect(self.player.rect):
            hint_rect = pygame.Rect(0, 0, 32, 10)
            hint_rect.midbottom = (
                self.courtyard_south_exit_rect.centerx + camera_x,
                self.courtyard_south_exit_rect.top + camera_y - 3,
            )
            return hint_rect
        if self.mainline.get("pending_pool_ending") and self.moon_pool_interaction_rect.colliderect(
            self.player.rect
        ):
            hint_rect = pygame.Rect(0, 0, 32, 10)
            hint_rect.midbottom = (
                self.moon_pool.rect.centerx + camera_x,
                self.moon_pool.visual_rect.top + camera_y - 3,
            )
            return hint_rect
        if self.palace_entry_rect.colliderect(self.player.rect):
            center_x = self.palace_entry_rect.centerx
            hint_rect = pygame.Rect(0, 0, 32, 10)
            hint_rect.midbottom = (
                center_x + camera_x,
                self.palace_entry_rect.top + camera_y - 3,
            )
            return hint_rect

        anchor = None
        for npc in self.npcs:
            if npc.can_interact(self.player.rect):
                anchor = npc.get_interaction_hint_anchor()
                break

        if anchor is None:
            return None

        hint_rect = pygame.Rect(0, 0, 32, 10)
        hint_rect.midbottom = (anchor[0] + camera_x, anchor[1] + camera_y - 3)
        return hint_rect

    def _draw_status_ui(self, surface: pygame.Surface) -> None:
        """绘制轻量状态提示，显示违规次数和 Tab 操作。"""
        slot = self.current_slot_id or "-"
        text = f"槽位 {slot}  |  违规 {self.game_state.violation_count}/3  |  Tab 规则手册"
        draw_filled_rect(surface, (4, config.SCREEN_HEIGHT - 26, 300, 22), palette.BLACK)
        draw_rect(surface, 4, config.SCREEN_HEIGHT - 26, 300, 22, palette.DARK_BLOOD)
        if render_text(surface, text, 8, config.SCREEN_HEIGHT - 21, 12, palette.MOON_WHITE):
            return

        draw_filled_rect(surface, (8, config.SCREEN_HEIGHT - 14, 70, 3), palette.MOON_WHITE)

    def _on_tree_bleeding(self, **payload) -> None:
        """吴刚砍到关键次数后，让月桂树进入流血状态。"""
        _ = payload
        self.laurel_tree.set_bleeding(True)
        self.wugang.rest(self.laurel_tree.BLEED_DURATION)
        self._tree_bleeding_check_cooldown = 0.0
        self._tree_was_bleeding = True
        self._tree_safe_exit_grace = 0.0

    def _on_violation_changed(self, **payload) -> None:
        """违规只更新演出；不能覆盖最近的任务完成存档。"""
        count = int(payload.get("count", self.game_state.violation_count))
        self.palace_wall.set_horror_level(count)

    def _reset_after_death(self) -> None:
        """恢复最近完成事件的完整快照，死亡本身不写档。"""
        payload = deepcopy(self.current_save_data or self.save_manager.default_save(self.current_slot_id or 1))
        # 老版本曾把死亡状态自动写入磁盘；载入它时给出可继续的安全状态。
        if payload.get("violation_count", 0) >= 3:
            payload["violation_count"] = 0
        self._apply_save_data(payload)
        self.mode = self._saved_scene(self.current_save_data or payload)
        self.pause_return_mode = None
        self.audio.sync_for_game_state(self.mode, self.mainline)







