"""Pygame 游戏主循环基础。"""

from __future__ import annotations

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
from core.event_bus import DIALOG_CHOICE_SELECTED, GLOBAL_EVENT_BUS, SHOW_DIALOG, TREE_BLEEDING, VIOLATION_CHANGED
from core.game_state import GameState
from core.input_manager import InputManager
from core.rule_engine import RuleEngine
from core.save_manager import SaveManager
from effects.distortion import DistortionEffect
from entities.player import Player
from entities.wugang import Wugang
from entities.yutu import Yutu
from ui.death_screen import DeathScreen
from ui.dialog_box import DialogBox
from ui.ending_cg import EndingCG
from ui.envoy_register import EnvoyRegister
from ui.main_menu import MENU_DELETE_SAVE, MENU_LOAD_GAME, MENU_NEW_GAME, MENU_QUIT, MainMenu
from ui.opening_cg import OpeningCG
from ui.rule_book import RuleBook
from ui.broken_jade import BrokenJadeView
from ui.scene_transition import SceneTransition
from ui.save_menu import SAVE_MODE_DELETE, SAVE_MODE_LOAD, SAVE_MODE_NEW, SaveMenu
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


class Game:
    """MoonSpace 主游戏对象，负责主循环、实体更新、规则检测和基础渲染。"""

    MODE_MAIN_MENU = "main_menu"
    MODE_SAVE_MENU = "save_menu"
    MODE_OPENING = "opening"
    MODE_HOME = "home"
    MODE_TRANSITION = "transition"
    MODE_PLAYING = "playing"
    MODE_GUANGHAN = "guanghan"
    MODE_ENDING_CG = "ending_cg"

    DEFAULT_MAINLINE = {
        "wugang_checked": False,
        "yutu_checked": False,
        "wugang_polluted": False,
        "yutu_polluted": False,
        "report_completed": False,
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
        self.fullscreen = False
        self.display_surface = self._set_display_mode(self.fullscreen)
        self.game_surface = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        self.running = True

        self.input_manager = InputManager()
        self.event_bus = GLOBAL_EVENT_BUS
        self.event_bus.clear()
        self.audio = AudioManager(self.event_bus)
        self.game_state = GameState(self.event_bus)
        self.rule_engine = RuleEngine(self.game_state)
        register_demo_rules(self.rule_engine)

        self.save_manager = SaveManager()
        self.main_menu = MainMenu()
        self.save_menu = SaveMenu(self.save_manager)
        self.opening_cg = OpeningCG(self.audio)
        self.ending_cg = EndingCG(self.audio)
        self.envoy_register = EnvoyRegister()
        self.scene_transition = SceneTransition()
        self.mode = self.MODE_MAIN_MENU
        self.pending_save_mode = SAVE_MODE_LOAD
        self.current_slot_id: int | None = None
        self.current_save_data: dict | None = None
        self.mainline = dict(self.DEFAULT_MAINLINE)
        self.exit_confirm_open = False
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
        # 记录台与验牒分别位于桌前两侧，侧面也保留可接近的窄入口。
        self.guanghan_records_rect = pygame.Rect(180, 404, 64, 26)
        self.guanghan_records_side_rect = pygame.Rect(132, 372, 52, 58)
        self.guanghan_register_rect = pygame.Rect(252, 404, 64, 26)
        self.guanghan_register_side_rect = pygame.Rect(308, 372, 52, 58)
        # 复命点在北侧台阶前的地面；玩家不能站到王座、台阶或帷幕立面上。
        self.guanghan_report_rect = pygame.Rect(410, 244, 140, 56)
        # 南门交互区位于门楼前的地面边缘，进入后会回到前院，不穿过门楼立面。
        self.guanghan_exit_rect = pygame.Rect(420, 450, 120, 40)
        self.courtyard_south_exit_rect = pygame.Rect(420, 380, 120, 40)
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
        self.pound_table = PoundTable(740, 302)
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
        self.distortion = DistortionEffect(self.event_bus)
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
            if self.mode in (self.MODE_HOME, self.MODE_TRANSITION, self.MODE_PLAYING, self.MODE_GUANGHAN):
                self._save_current_slot()
            self.running = False

    def update(self, dt: float) -> None:
        """按当前流程状态更新存档菜单、开场 CG 或正式游戏。"""
        if self.mode == self.MODE_MAIN_MENU:
            action = self.main_menu.update(dt, self.input_manager)
            self._handle_main_menu_action(action)
            return

        if self.mode == self.MODE_SAVE_MENU:
            selected_slot = self.save_menu.update(dt, self.input_manager)
            if self.save_menu.back_requested:
                self.mode = self.MODE_MAIN_MENU
            elif selected_slot is not None:
                self._start_slot(selected_slot, force_new=self.pending_save_mode == SAVE_MODE_NEW)
            return

        if self.mode == self.MODE_OPENING:
            if self.opening_cg.update(dt, self.input_manager):
                self._finish_opening()
            return

        if self.mode == self.MODE_ENDING_CG:
            if self.ending_cg.update(dt, self.input_manager):
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

        self._update_playing(dt)

    def _update_home(self, dt: float) -> None:
        """更新穿越后、正式入宫前的 home 教程场景。"""
        if self._update_exit_confirm():
            self.distortion.update(dt)
            return

        if self.dialog_box.active:
            was_rules_briefing_complete = self.home_tutorial.rules_briefing_complete
            self.dialog_box.update(dt, self.input_manager)
            if self.home_tutorial.rules_briefing_complete != was_rules_briefing_complete:
                self._save_current_slot()
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

        if (
            self.home_tutorial.sign_read != was_sign_read
            or self.home_tutorial.rules_briefing_complete != was_rules_briefing_complete
        ):
            self._save_current_slot()

        if self.home_tutorial.is_gate_entered(self.player.rect):
            self._finish_home_tutorial()

        self.distortion.update(dt)

    def _update_guanghan(self, dt: float) -> None:
        """更新广寒宫内殿基础状态。"""
        self._chang_e_time += dt
        if self.envoy_register.active:
            if self.envoy_register.update(self.input_manager, dt):
                self._save_current_slot()
            self.distortion.update(dt)
            return
        if self._update_exit_confirm():
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
        self._update_return_countdown(dt)
        self.distortion.update(dt)
    def _update_playing(self, dt: float) -> None:
        """更新正式游玩状态。"""
        if self._update_exit_confirm():
            self.distortion.update(dt)
            return

        if self.death_screen.active:
            if self.death_screen.update(dt, self.input_manager):
                self._reset_after_death()
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
            if self.mainline.get("pending_pool_ending") and self.moon_pool.rect.colliderect(
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
        elif self.mode == self.MODE_SAVE_MENU:
            self.save_menu.draw(self.game_surface)
        elif self.mode == self.MODE_OPENING:
            self.opening_cg.draw(self.game_surface)
        elif self.mode == self.MODE_TRANSITION:
            self.scene_transition.draw(self.game_surface)
        elif self.mode == self.MODE_HOME:
            self._draw_home()
        elif self.mode == self.MODE_GUANGHAN:
            self._draw_guanghan()
        elif self.mode == self.MODE_ENDING_CG:
            self.ending_cg.draw(self.game_surface)
        else:
            self._draw_playing()

        self._draw_exit_confirm(self.game_surface)

        target_rect = self._scaled_game_rect(self.display_surface.get_size())
        scaled = pygame.transform.scale(
            self.game_surface,
            target_rect.size,
        )
        self.display_surface.fill(palette.BLACK)
        self.display_surface.blit(scaled, target_rect)
        pygame.display.flip()

    def _set_display_mode(self, fullscreen: bool) -> pygame.Surface:
        """应用窗口或全屏显示模式，并返回当前显示表面。"""
        if fullscreen:
            surface = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        else:
            surface = pygame.display.set_mode(self.windowed_size)
        pygame.display.set_caption(config.WINDOW_TITLE)
        return surface

    def _toggle_fullscreen(self) -> None:
        """在普通窗口和无标题栏全屏之间切换。"""
        self.fullscreen = not self.fullscreen
        self.display_surface = self._set_display_mode(self.fullscreen)

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

    def _scene_world_size(self, mode: str | None = None) -> tuple[int, int]:
        """返回当前剧情场景的独立世界尺寸。"""
        scene = mode or self.mode
        if scene == self.MODE_PLAYING:
            return config.COURTYARD_WIDTH, config.COURTYARD_HEIGHT
        if scene == self.MODE_GUANGHAN:
            return config.GUANGHAN_WIDTH, config.GUANGHAN_HEIGHT
        return config.MAP_WIDTH, config.MAP_HEIGHT

    def _camera_offset(self) -> tuple[int, int]:
        """返回跟随玩家且被大地图边界限制的世界偏移。"""
        world_width, world_height = self._scene_world_size()
        camera_x = self.player.rect.centerx - config.SCREEN_WIDTH // 2
        if self.mode == self.MODE_GUANGHAN:
            # 内殿纵深大于视口；把来使放在画面下方，保留北侧帷幕和复命人物。
            camera_y = self.player.rect.centery - int(config.SCREEN_HEIGHT * 0.8)
        else:
            camera_y = self.player.rect.centery - config.SCREEN_HEIGHT // 2
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
        depth_items = [(self.laurel_tree.get_collision_rect().bottom, self.laurel_tree.draw)]
        depth_items.extend((npc.get_collision_rect().bottom, npc.draw) for npc in self.npcs)
        depth_items.append(
            (
                self.player.rect.bottom,
                self.player.draw,
            )
        )
        for _, draw_item in sorted(depth_items, key=lambda item: item[0]):
            draw_item(self.game_surface, camera_offset)
        self.pound_table.draw_front(self.game_surface, camera_offset)
        self.distortion.draw_overlay(self.game_surface)
        self._draw_interaction_hint(self.game_surface)
        self._draw_status_ui(self.game_surface)
        self.rule_book.draw(self.game_surface)
        self.dialog_box.draw(self.game_surface)
        self.death_screen.draw(self.game_surface)
        self.broken_jade_view.draw(self.game_surface)

    def _draw_guanghan(self) -> None:
        """绘制广寒宫内殿场景和当前 UI 层。"""
        camera_offset = self._camera_offset()
        if self._draw_guanghan_background(camera_offset):
            self._draw_guanghan_actors(camera_offset)
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
        """绘制内殿独立物件；嫦娥使用现有透明 16 帧素材站在北侧帷幕后。"""
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

        frame_index = int(self._chang_e_time * 2.0) % 16
        frame = self._chang_e_frames[frame_index]
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
            text = "E 验牒身份"
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
        """身份登记可从桌前右侧或登记台右侧接近。"""
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
            pygame.Rect(330, 92, 300, 86),
            pygame.Rect(350, 178, 260, 62),
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

        caption = self.pending_report_dialog[2] if self.pending_report_dialog else "来使递上两份职司记录。"
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
        self.distortion.draw_overlay(self.game_surface)
        self._draw_home_hint(self.game_surface, camera_offset)
        self._draw_home_status_ui(self.game_surface)
        self.rule_book.draw(self.game_surface)
        self.dialog_box.draw(self.game_surface)

    def _handle_main_menu_action(self, action: str | None) -> None:
        """处理主菜单动作。"""
        if action == MENU_NEW_GAME:
            self.pending_save_mode = SAVE_MODE_NEW
            self.save_menu.open(SAVE_MODE_NEW)
            self.mode = self.MODE_SAVE_MENU
        elif action == MENU_LOAD_GAME:
            self.pending_save_mode = SAVE_MODE_LOAD
            self.save_menu.open(SAVE_MODE_LOAD)
            self.mode = self.MODE_SAVE_MENU
        elif action == MENU_DELETE_SAVE:
            self.pending_save_mode = SAVE_MODE_DELETE
            self.save_menu.open(SAVE_MODE_DELETE)
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
            self.exit_confirm_open = False
            self.mode = self.MODE_HOME
        elif scene == self.MODE_GUANGHAN:
            self.exit_confirm_open = False
            self.mode = self.MODE_GUANGHAN
            self.audio.play_ambient()
        else:
            self._enter_courtyard()

    def _finish_opening(self) -> None:
        """开场播放完或跳过后进入游戏并保存已看状态。"""
        if self.current_save_data is None:
            return
        self.current_save_data["opening_seen"] = True
        self._enter_home()
        self._save_current_slot(opening_seen=True)

    def _enter_home(self) -> None:
        """进入穿越后的 home 教程地图。"""
        self.exit_confirm_open = False
        self.mode = self.MODE_HOME
        self.home_tutorial.reset_player_to_spawn(self.player)

    def _enter_courtyard(self, *, reset_player: bool = False) -> None:
        """进入现有月宫前院正式游戏区。"""
        self.exit_confirm_open = False
        self.mode = self.MODE_PLAYING
        self.audio.play_ambient()
        if reset_player:
            spawn_x, spawn_y = config.COURTYARD_SOUTH_SPAWN
            self.player = Player(spawn_x - config.PLAYER_SIZE[0] // 2, spawn_y - config.PLAYER_SIZE[1])
            self.player.facing = "up"
            self._setup_rule_zones()

    def _finish_home_tutorial(self) -> None:
        """完成 home 教程并播放月门转场。"""
        self._save_current_slot(
            home_tutorial_done=True,
            home_tutorial=self.home_tutorial.collect_save_data(),
            player={
                "x": config.PLAYER_START_X,
                "y": config.PLAYER_START_Y,
                "facing": "down",
            },
        )
        self.mode = self.MODE_TRANSITION
        self.scene_transition.start(
            self._complete_home_transition,
            "月门正在核验来使身份",
            on_found=self.audio.play_transition_found,
        )

    def _complete_home_transition(self) -> None:
        """转场停顿结束后进入月宫前院。"""
        self._enter_courtyard(reset_player=True)
        self._save_current_slot(
            home_tutorial_done=True,
            home_tutorial=self.home_tutorial.collect_save_data(),
        )

    def _update_transition(self, dt: float) -> None:
        """推进场景转场，满进度停顿后执行切场景回调。"""
        if self._update_exit_confirm():
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
        self.exit_confirm_open = False
        self.report_staging_active = False
        self.report_staging_timer = 0.0
        self.pending_report_dialog = None
        self.palace_wall.set_horror_level(self.game_state.violation_count)
        self.distortion.restore_violation_count(self.game_state.violation_count)
        self._setup_rule_zones()

    def _migrate_save_data(self, data: dict) -> dict:
        """兼容早期平铺字段，并把已离宫存档的旧倒计时收束为稳定状态。"""
        migrated = dict(data)

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
            "return_countdown_active",
            "return_departed_on_time",
            "pending_pool_ending",
            "ending",
        ):
            if key not in mainline and key in migrated:
                mainline[key] = migrated[key]

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

        # 旧版本离殿后仍保留 active=true；显式 scene 已在前院或月谷时，
        # 将其解释为“已经及时离宫”，避免旧倒计时在新版本重新复活。
        scene = migrated.get("scene")
        if (
            scene in (self.MODE_HOME, self.MODE_PLAYING)
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
        self.opening_cg.active = False
        self.ending_cg.active = False
        self.scene_transition.active = False
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
        if self.mode in (self.MODE_HOME, self.MODE_PLAYING, self.MODE_GUANGHAN):
            return self.mode
        if self.mode == self.MODE_TRANSITION:
            return self.MODE_PLAYING
        previous_scene = previous_data.get("scene")
        if previous_scene in (self.MODE_HOME, self.MODE_PLAYING, self.MODE_GUANGHAN):
            return previous_scene
        return self.MODE_HOME if not previous_data.get("home_tutorial_done", False) else self.MODE_PLAYING

    def _saved_scene(self, data: dict) -> str:
        """读取显式场景；旧存档根据教程和复命状态做保守迁移。"""
        scene = data.get("scene")
        valid_scenes = (self.MODE_HOME, self.MODE_PLAYING, self.MODE_GUANGHAN)
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

    def _update_exit_confirm(self) -> bool:
        """Handle the in-game save-and-exit confirmation overlay."""
        if not self.exit_confirm_open:
            if self.input_manager.was_pressed(config.ACTION_QUIT):
                self.exit_confirm_open = True
                self._save_current_slot()
                return True
            return False

        if self.input_manager.was_pressed(config.ACTION_QUIT) or self.input_manager.was_pressed(config.ACTION_RESTART):
            self._save_current_slot()
            self.running = False
            return True

        if self.input_manager.was_pressed(config.ACTION_INTERACT):
            self.exit_confirm_open = False
            return True

        return True

    def _draw_exit_confirm(self, surface: pygame.Surface) -> None:
        """Draw the save-and-exit confirmation overlay."""
        if not self.exit_confirm_open:
            return

        shade = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT), pygame.SRCALPHA)
        shade.fill((0, 0, 0, 118))
        surface.blit(shade, (0, 0))

        panel = pygame.Rect(58, 72, 204, 72)
        draw_filled_rect(surface, panel, palette.BLACK)
        draw_double_rect(surface, panel, palette.MOON_WHITE, palette.DARK_BLOOD)
        render_text(surface, "已自动存档", panel.x + 14, panel.y + 12, 14, palette.MOON_WHITE)
        render_text(surface, "E 继续游戏", panel.x + 14, panel.y + 34, 12, palette.PALE_MOON)
        render_text(surface, "Esc / R 保存并退出", panel.x + 14, panel.y + 50, 12, palette.MOON_WHITE)

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
        if self.mode != self.MODE_GUANGHAN:
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
            trigger_type="inside",
            cooldown=1.5,
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

        staring_reflection = not self.player.is_moving() and self._player_faces_pool()
        pool_target = self.player.rect if staring_reflection else pygame.Rect(-9999, -9999, 1, 1)
        if self.pool_reflection_zone.update(dt, pool_target):
            self.moon_pool.flash_reflection()
            self.rule_engine.check_rule(
                RULE_POOL_REFLECTION,
                {"staring_reflection": True},
            )
            if not self.mainline.get("broken_jade_obtained", False) and not self.game_state.is_dead():
                self.mainline["broken_jade_obtained"] = True
                self.broken_jade_view.acquire()
                self.rule_book.set_broken_jade_obtained(True)
                self._save_current_slot()

        if self.yutu_eye_zone.update(dt, self.player.rect):
            self.rule_engine.check_rule(
                RULE_NO_EYE_CONTACT,
                {
                    "yutu_pounding": self.yutu.is_pounding and self._is_player_in_yutu_front_arc(),
                    "facing_yutu": is_facing_rect(self.player.rect, self.player.facing, self.yutu.rect),
                },
            )

        if self.palace_run_zone.update(dt, self.player.rect):
            self.rule_engine.check_pseudo_rule(
                PSEUDO_RULE_YUTU_WATCH,
                {
                    "running_near_palace": self.input_manager.is_pressed(config.ACTION_RUN)
                    and self.player.is_moving()
                },
            )

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
            self.event_bus.emit(
                SHOW_DIALOG,
                speaker_id="palace_gate",
                lines=[
                    "宫门里的月光没有让路。",
                    "验职未齐，广寒宫不受复命。",
                ],
            )
            return True

        self._enter_guanghan()
        return True

    def _office_checks_complete(self) -> bool:
        """两项职司检查均完成时，宫门才会开启。"""
        return bool(self.mainline["wugang_checked"] and self.mainline["yutu_checked"])

    def _enter_guanghan(self) -> None:
        """进入广寒宫内殿。"""
        self.exit_confirm_open = False
        self.mode = self.MODE_GUANGHAN
        self.report_started = False
        self.player.rect.midbottom = config.GUANGHAN_SOUTH_SPAWN
        self.player.position.xy = self.player.rect.topleft
        self.player.facing = "up"
        self._save_current_slot()

    def _begin_guanghan_report(self) -> None:
        """玩家主动靠近嫦娥后才开始复命，保留入殿探索窗口。"""
        if not self._office_checks_complete():
            self.event_bus.emit(
                SHOW_DIALOG,
                speaker_id="change",
                lines=["两项职司尚未验明，来使不可复命。"],
            )
            return
        self.report_started = True
        if self.mainline["wugang_polluted"] or self.mainline["yutu_polluted"]:
            self._start_polluted_report()
        else:
            self._start_normal_report()
        self._save_current_slot()

    def _start_polluted_report(self) -> None:
        """污染状态下正常复命，但只留下池边异常的待触发结局。"""
        wugang_polluted = self.mainline.get("wugang_polluted", False)
        yutu_polluted = self.mainline.get("yutu_polluted", False)
        self.mainline["report_completed"] = False
        self.mainline["return_departed_on_time"] = False
        self.mainline["return_countdown_active"] = False
        self.mainline["return_countdown_remaining"] = 0.0
        self.mainline["pending_pool_ending"] = ""
        if wugang_polluted and yutu_polluted:
            self.mainline["pending_pool_ending"] = "be_double"
            caption = "两份记录在月光中叠成同一处污痕。"
            lines = [
                "嫦娥隔着帘影听完复命。",
                "吴刚、玉兔二职，皆已验毕。",
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

    def _emit_report_audio_cues(self) -> None:
        """Trigger report shot cues once, including when a frame skips a boundary."""
        for boundary, key in self.REPORT_AUDIO_CUES:
            token = f"report:{boundary}:{key}"
            if self.report_staging_timer >= boundary and token not in self._report_audio_cues_played:
                self._report_audio_cues_played.add(token)
                self.audio.play_cg_cue(key, token=token)

    def _try_trigger_pending_pool_ending(self) -> bool:
        """污染复命结束后，离殿触发池边异常 BE。"""
        pending_ending = self.mainline.get("pending_pool_ending", "")
        if not pending_ending or self.mainline.get("ending"):
            return False

        self.mainline["pending_pool_ending"] = ""
        self.mainline["ending"] = pending_ending
        self.moon_pool.flash_reflection(2.0)
        self.dialog_box.active = False
        self.ending_cg.start(pending_ending)
        self.audio.stop_ambient()
        self.mode = self.MODE_ENDING_CG
        self._save_current_slot()
        return True

    def _try_leave_guanghan_after_report(self) -> bool:
        """正常复命后离开内殿，先回到广寒宫广场。"""
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
            # 离宫这一刻就是候月流程的终点；之后任何场景都不得再更新或显示它。
            self.mainline["return_departed_on_time"] = True
            self.mainline["return_countdown_active"] = False
            self.mainline["return_countdown_remaining"] = 0.0

        self.mode = self.MODE_PLAYING
        self.exit_confirm_open = False
        self.dialog_box.active = False
        self.player.rect.midbottom = config.COURTYARD_NORTH_SPAWN
        self.player.position.xy = self.player.rect.topleft
        self.player.facing = "down"
        self._save_current_slot()
        return True

    def _leave_courtyard_to_home(self) -> None:
        """从广场南门返回月谷，保持两道门的空间顺序。"""
        if self.mainline.get("pending_pool_ending"):
            self._show_courtyard_exit_blocked_for_pool()
            return
        if not self.mainline.get("return_departed_on_time", False):
            self.event_bus.emit(
                SHOW_DIALOG,
                speaker_id="courtyard_gate",
                lines=[
                    "复命未毕，南门的月光不通。",
                    "先入广寒宫复命，再返月谷。",
                ],
            )
            return
        self.mode = self.MODE_HOME
        self.exit_confirm_open = False
        self.dialog_box.active = False
        self.player.rect.midtop = (
            self.home_tutorial.gate_trigger_rect.centerx,
            self.home_tutorial.gate_trigger_rect.bottom + 8,
        )
        self.player.position.xy = self.player.rect.topleft
        self.player.facing = "down"
        self._save_current_slot()

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
        if self.mode != self.MODE_GUANGHAN or self.mainline.get("return_departed_on_time", False):
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
        self.audio.stop_ambient()
        self.mode = self.MODE_ENDING_CG
        self._save_current_slot()
        return True
    def _trigger_change_ending(self) -> None:
        """候月倒计时归零后，触发取代嫦娥 BE。"""
        if self.mainline.get("ending"):
            return
        self.mainline["return_countdown_active"] = False
        self.mainline["return_countdown_remaining"] = 0.0
        self.mainline["ending"] = "be_change"
        self.dialog_box.active = False
        self.ending_cg.start("be_change")
        self.audio.stop_ambient()
        self.mode = self.MODE_ENDING_CG
        self._save_current_slot()
    def _start_normal_report(self) -> None:
        """无污染时完成正常复命，并启动候月倒计时。"""
        self.mainline["report_completed"] = True
        self.mainline["return_departed_on_time"] = False
        self.mainline["return_countdown_active"] = True
        self.mainline["return_countdown_remaining"] = 60.0
        self.mainline["pending_pool_ending"] = ""
        self._start_report_staging(
            "change",
            [
                "嫦娥没有看你，她看着你身后的月光。",
                "吴刚斧声未绝，玉兔杵声未停。",
                "来使的记录，月宫收下了。",
                "复命既毕，使者可候月落。",
                "待这一轮月光尽了，归路自会显明。",
            ],
            "两份职司记录被月光托起，递入广寒宫深处。",
        )
    def _try_complete_wugang_check(self) -> bool:
        """月桂流血时，允许来使通过对话选项完成伐桂检查。"""
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
                {"id": "wugang_overstep", "text": "替斧声续记一响。"},
                {"id": "wugang_record", "text": "只记录，不执斧。"},
            ],
            choice_context="wugang_check",
        )
        return True

    def _try_handle_yutu_check(self) -> bool:
        """从玉兔身后完成捣药检查；正面接触只记普通违规。"""
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
                {"id": "yutu_overstep", "text": "近闻药香，确认药成。"},
                {"id": "yutu_record", "text": "只记录药色/杵声。"},
            ],
            choice_context="yutu_check",
        )
        return True

    def _is_player_in_yutu_front_arc(self) -> bool:
        """玉兔大图面朝左，左侧才是正面/对视危险区。"""
        vertical_distance = abs(self.player.rect.centery - self.yutu.rect.centery)
        return self.player.rect.centerx <= self.yutu.rect.left and vertical_distance <= 20

    def _is_player_behind_yutu(self) -> bool:
        """除左侧正面对视区外，上、下和右后方都允许完成检查。"""
        return not self._is_player_in_yutu_front_arc()

    def _on_dialog_choice_selected(self, speaker_id: str, choice_id: str, **payload) -> None:
        """处理主线对话选项结果。"""
        _ = speaker_id, payload
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
            ]
        self.event_bus.emit(SHOW_DIALOG, speaker_id="wugang", lines=lines)
        self._save_current_slot()

    def _complete_yutu_check(self, polluted: bool) -> None:
        """写入玉兔检查结果并播放对应反馈。"""
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
            ]
        self.event_bus.emit(SHOW_DIALOG, speaker_id="yutu", lines=lines)
        self._save_current_slot()

    def _get_collision_rects(self) -> list[pygame.Rect]:
        """收集地图、世界物体和 NPC 碰撞。"""
        rects = [obj.get_collision_rect() for obj in self.world_objects]
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
        if self.mainline.get("pending_pool_ending") and self.moon_pool.rect.colliderect(
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
        self._save_current_slot()

    def _on_violation_changed(self, **payload) -> None:
        """违规后自动保存，让存档记录月宫识别进度。"""
        count = int(payload.get("count", self.game_state.violation_count))
        self.palace_wall.set_horror_level(count)
        self._save_current_slot()

    def _reset_after_death(self) -> None:
        """死亡后重启当前 Demo 场景的关键状态。"""
        self.death_screen.active = False
        self.death_screen.fade_timer = 0.0
        self.audio.stop_cg_sounds()
        self.player = Player(config.PLAYER_START_X, config.PLAYER_START_Y)
        self.laurel_tree.set_bleeding(False)
        self.palace_wall.set_horror_level(0)
        self.moon_pool.reflection_flash_timer = 0.0
        self.distortion.reset()
        self.rule_book.close()
        self.dialog_box.active = False
        self.exit_confirm_open = False
        self._tree_bleeding_check_cooldown = 0.0
        self._tree_was_bleeding = False
        self._tree_safe_exit_grace = 0.0
        self._setup_rule_zones()
        self._save_current_slot()







