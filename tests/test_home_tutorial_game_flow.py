"""Home/tutorial 顶层流程测试。"""

from collections import deque

import pygame

import config
from core.game import Game
from utils import palette


class MemorySaveManager:
    def __init__(self, data=None):
        self.data = data
        self.saved_payloads = []

    def load(self, slot_id):
        _ = slot_id
        return self.data

    def default_save(self, slot_id):
        return {
            "slot_id": slot_id,
            "saved_at": "",
            "opening_seen": False,
            "home_tutorial_done": False,
            "home_tutorial": {"sign_read": False, "practice_done": False, "rules_briefing_complete": False},
            "player": {"x": 472, "y": 336, "facing": "down"},
            "violation_count": 0,
            "known_rules": {},
            "laurel_tree": {"bleeding": False},
            "wugang": {"chop_count": 0},
            "yutu": {"is_pounding": True},
        }

    def save(self, slot_id, data):
        payload = self.default_save(slot_id)
        payload.update(data)
        self.data = payload
        self.saved_payloads.append(payload)
        return payload

    def delete(self, slot_id):
        _ = slot_id
        self.data = None

    def list_slots(self):
        return []


def choose_current_dialog_option(game, index=0):
    game.dialog_box.current_index = len(game.dialog_box.lines) - 1
    game.dialog_box.selected_choice_index = index
    game.dialog_box.advance()


def finish_scene_transition(game):
    """推进一次完整的场景转场，保留首帧 reveal 停顿语义。"""
    assert game.mode == game.MODE_TRANSITION
    game._update_transition(
        game.scene_transition.LOAD_DURATION + game.scene_transition.REVEAL_HOLD + 0.1
    )
    assert game.mode == game.MODE_TRANSITION
    game._update_transition(game.scene_transition.REVEAL_HOLD)


def _guanghan_target_is_reachable(game, target: tuple[int, int]) -> bool:
    """在 8px 网格上验证从南门出生点能绕开台阶和登记台到达目标。"""
    collisions = game._guanghan_collision_rects()
    start = config.GUANGHAN_SOUTH_SPAWN
    queue = deque([start])
    visited = {start}

    def walkable(point: tuple[int, int]) -> bool:
        rect = pygame.Rect(0, 0, *config.PLAYER_SIZE)
        rect.midbottom = point
        return pygame.Rect(40, 112, config.GUANGHAN_WIDTH - 80, 408).contains(rect) and not any(
            rect.colliderect(obstacle) for obstacle in collisions
        )

    if not walkable(start):
        return False
    while queue:
        x, y = queue.popleft()
        if abs(x - target[0]) <= 8 and abs(y - target[1]) <= 8:
            return True
        for next_point in ((x - 8, y), (x + 8, y), (x, y - 8), (x, y + 8)):
            if next_point in visited or not walkable(next_point):
                continue
            visited.add(next_point)
            queue.append(next_point)
    return False


def test_finish_opening_enters_home_when_tutorial_not_done():
    game = Game()
    game.save_manager = MemorySaveManager()
    game.current_slot_id = 1
    game.current_save_data = game.save_manager.default_save(1)
    game._apply_save_data(game.current_save_data)

    game._finish_opening()

    assert game.mode == game.MODE_HOME
    assert game.current_save_data["opening_seen"] is True
    assert game.home_tutorial.sign_read is False


def test_start_slot_skips_home_when_tutorial_already_done():
    save_data = MemorySaveManager().default_save(1)
    save_data["opening_seen"] = True
    save_data["home_tutorial_done"] = True
    save_data["player"] = {"x": 123, "y": 234, "facing": "left"}
    game = Game()
    game.save_manager = MemorySaveManager(save_data)

    game._start_slot(1)

    assert game.mode == game.MODE_PLAYING
    assert game.player.rect.topleft == (123, 234)
    assert game.player.facing == "left"


def test_start_slot_replays_saved_ending_instead_of_entering_soft_locked_world():
    save_data = MemorySaveManager().default_save(1)
    save_data["opening_seen"] = True
    save_data["home_tutorial_done"] = True
    save_data["mainline"] = {"ending": "he_return_earth"}
    game = Game()
    game.save_manager = MemorySaveManager(save_data)

    game._start_slot(1)

    assert game.mode == game.MODE_ENDING_CG
    assert game.ending_cg.ending_id == "he_return_earth"
    assert game.ending_cg.active is True


def test_start_slot_restores_explicit_guanghan_scene_and_countdown():
    save_data = MemorySaveManager().default_save(1)
    save_data["opening_seen"] = True
    save_data["home_tutorial_done"] = True
    save_data["scene"] = "guanghan"
    save_data["mainline"] = {
        "report_completed": True,
        "return_countdown_active": True,
        "return_countdown_remaining": 23.5,
    }
    game = Game()
    game.save_manager = MemorySaveManager(save_data)

    game._start_slot(1)

    assert game.mode == game.MODE_GUANGHAN
    assert game.mainline["return_countdown_remaining"] == 23.5


def test_old_report_save_without_scene_restores_guanghan_conservatively():
    save_data = MemorySaveManager().default_save(1)
    save_data["opening_seen"] = True
    save_data["home_tutorial_done"] = True
    save_data["mainline"] = {
        "report_completed": True,
        "return_countdown_active": True,
        "return_countdown_remaining": 12.0,
    }
    game = Game()
    game.save_manager = MemorySaveManager(save_data)

    game._start_slot(1)

    assert game.mode == game.MODE_GUANGHAN


def test_collect_save_data_records_stable_scene_and_normalizes_transition():
    game = Game()
    game.current_save_data = {"home_tutorial_done": True}

    game.mode = game.MODE_HOME
    assert game._collect_save_data()["scene"] == "home"
    game.mode = game.MODE_PLAYING
    assert game._collect_save_data()["scene"] == "playing"
    game.mode = game.MODE_GUANGHAN
    assert game._collect_save_data()["scene"] == "guanghan"
    game.mode = game.MODE_TRANSITION
    assert game._collect_save_data()["scene"] == "playing"


def test_active_scene_transition_saves_its_target_scene():
    game = Game()
    game.current_save_data = {"home_tutorial_done": True, "scene": game.MODE_PLAYING}
    game.mode = game.MODE_PLAYING

    game._start_scene_transition(game.MODE_HOME, lambda: None, "返回月谷")

    assert game.mode == game.MODE_TRANSITION
    assert game._collect_save_data()["scene"] == game.MODE_HOME

    finish_scene_transition(game)

    assert game.mode == game.MODE_HOME
    assert game._transition_target_scene is None


def test_scene_transition_snapshot_uses_a_safe_spawn_for_the_target_scene():
    game = Game()
    game.save_manager = MemorySaveManager()
    game.current_slot_id = 1
    game.current_save_data = game.save_manager.default_save(1)
    game._apply_save_data(game.current_save_data)
    game.mode = game.MODE_PLAYING
    game.player.rect.topleft = (512, 188)
    game.player.position.xy = game.player.rect.topleft

    game._start_scene_transition(game.MODE_GUANGHAN, game._enter_guanghan, "进入广寒宫")

    saved = game.save_manager.saved_payloads[-1]
    hall_rect = pygame.Rect(0, 0, *config.PLAYER_SIZE)
    hall_rect.midbottom = config.GUANGHAN_SOUTH_SPAWN
    assert saved["scene"] == game.MODE_GUANGHAN
    assert saved["player"] == {"x": hall_rect.x, "y": hall_rect.y, "facing": "up"}

    game._update_transition(game.scene_transition.LOAD_DURATION + game.scene_transition.REVEAL_HOLD)
    game._update_transition(game.scene_transition.REVEAL_HOLD)
    assert game.mode == game.MODE_GUANGHAN
    assert game.player.rect.midbottom == config.GUANGHAN_SOUTH_SPAWN


def test_apply_save_data_resets_non_persistent_slot_runtime_state():
    game = Game()
    game.wugang.resting_timer = 8.0
    game.wugang._timer = 1.5
    game.wugang.anim_state = "rest"
    game.yutu._timer = 0.3
    game.yutu.current_frame = 7
    game.moon_pool.reflection_flash_timer = 2.0
    game.opening_cg.active = True
    game.ending_cg.active = True
    game.scene_transition.active = True

    game._apply_save_data(MemorySaveManager().default_save(1))

    assert game.wugang.resting_timer == 0.0
    assert game.wugang._timer == 0.0
    assert game.wugang.anim_state == "chop"
    assert game.yutu._timer == 0.0
    assert game.yutu.current_frame == 0
    assert game.moon_pool.reflection_flash_timer == 0.0
    assert game.opening_cg.active is False
    assert game.ending_cg.active is False
    assert game.scene_transition.active is False


def test_old_courtyard_save_inside_center_pool_is_moved_below_it():
    save_data = MemorySaveManager().default_save(1)
    save_data["scene"] = Game.MODE_PLAYING
    save_data["home_tutorial_done"] = True
    save_data["player"] = {"x": 472, "y": 336, "facing": "down"}
    game = Game()

    game._apply_save_data(save_data)

    assert not game.player.rect.colliderect(game.moon_pool.rect)
    assert game.player.rect.centerx == game.moon_pool.rect.centerx
    assert game.player.rect.top > game.moon_pool.rect.bottom


def test_palace_run_zone_stays_below_solid_wall():
    game = Game()

    assert game.palace_run_zone.rect.top >= game.palace_wall.get_collision_rect().bottom


def test_home_gate_entry_marks_tutorial_done_and_enters_courtyard():
    game = Game()
    game.save_manager = MemorySaveManager()
    game.current_slot_id = 1
    game.current_save_data = game.save_manager.default_save(1)
    game._apply_save_data(game.current_save_data)
    game.mode = game.MODE_HOME
    game.home_tutorial.sign_read = True
    game.home_tutorial.rules_briefing_complete = True
    game.home_tutorial.practice_done = True
    game.player.rect = game.home_tutorial.gate_trigger_rect.copy()
    game.player.position.xy = game.player.rect.topleft

    game._update_home(0.016)

    assert game.mode == game.MODE_TRANSITION
    assert game.scene_transition.active
    assert game.scene_transition.progress < 1.0

    game._update_transition(game.scene_transition.LOAD_DURATION + game.scene_transition.REVEAL_HOLD + 0.1)
    assert game.mode == game.MODE_TRANSITION

    game._update_transition(game.scene_transition.REVEAL_HOLD)

    assert game.mode == game.MODE_PLAYING
    assert game.current_save_data["home_tutorial_done"] is True
    assert game.save_manager.saved_payloads[-1]["home_tutorial_done"] is True
    assert game.player.rect.topleft == (game.player.position.x, game.player.position.y)
    assert game.player.rect.colliderect(pygame.Rect(0, 0, 1, 1)) is False


def test_home_gate_entry_saves_completion_before_transition_finishes():
    game = Game()
    game.save_manager = MemorySaveManager()
    game.current_slot_id = 1
    game.current_save_data = game.save_manager.default_save(1)
    game._apply_save_data(game.current_save_data)
    game.mode = game.MODE_HOME
    game.home_tutorial.sign_read = True
    game.home_tutorial.rules_briefing_complete = True
    game.home_tutorial.practice_done = True
    game.player.rect = game.home_tutorial.gate_trigger_rect.copy()
    game.player.position.xy = game.player.rect.topleft

    game._update_home(0.016)

    assert game.mode == game.MODE_TRANSITION
    assert game.current_save_data["home_tutorial_done"] is True
    assert game.current_save_data["player"]["x"] == config.PLAYER_START_X
    assert game.current_save_data["scene"] == game.MODE_PLAYING
    courtyard_rect = pygame.Rect(0, 0, *config.PLAYER_SIZE)
    courtyard_rect.midbottom = config.COURTYARD_SOUTH_SPAWN
    assert game.current_save_data["player"] == {
        "x": courtyard_rect.x,
        "y": courtyard_rect.y,
        "facing": "up",
    }


def test_game_applies_and_collects_mainline_progress():
    save_data = MemorySaveManager().default_save(1)
    save_data["mainline"] = {
        "wugang_checked": True,
        "yutu_checked": False,
        "wugang_polluted": True,
        "yutu_polluted": False,
        "report_completed": False,
        "return_countdown_active": True,
        "ending": "",
    }
    game = Game()

    game._apply_save_data(save_data)

    assert game.mainline["wugang_checked"] is True
    assert game.mainline["wugang_polluted"] is True
    assert game.mainline["return_countdown_active"] is True

    game.mainline["yutu_checked"] = True
    game.mainline["ending"] = "he_return_earth"
    collected = game._collect_save_data()

    assert collected["mainline"]["wugang_checked"] is True
    assert collected["mainline"]["yutu_checked"] is True
    assert collected["mainline"]["ending"] == "he_return_earth"

def test_wugang_check_requires_bleeding_laurel():
    game = Game()
    game.save_manager = MemorySaveManager()
    game.current_slot_id = 1
    game.current_save_data = game.save_manager.default_save(1)
    game._apply_save_data(game.current_save_data)
    game.mode = game.MODE_PLAYING
    game.player.rect.center = game.wugang.interaction_rect.center
    game.player.position.xy = game.player.rect.topleft
    game.laurel_tree.set_bleeding(False)
    game.input_manager._pressed_once.add(config.ACTION_INTERACT)

    game._update_playing(0.016)

    assert game.mainline["wugang_checked"] is False


def test_wugang_check_completes_when_laurel_bleeds():
    game = Game()
    game.save_manager = MemorySaveManager()
    game.current_slot_id = 1
    game.current_save_data = game.save_manager.default_save(1)
    game._apply_save_data(game.current_save_data)
    game.mode = game.MODE_PLAYING
    game.player.rect.center = game.wugang.interaction_rect.center
    game.player.position.xy = game.player.rect.topleft
    game.laurel_tree.set_bleeding(True)
    game.input_manager._pressed_once.add(config.ACTION_INTERACT)

    game._update_playing(0.016)

    assert game.mainline["wugang_checked"] is False
    assert game.dialog_box.active is True
    assert [choice["id"] for choice in game.dialog_box.choices] == ["wugang_overstep", "wugang_record"]
    assert [choice["text"] for choice in game.dialog_box.choices] == [
        "落闻斧鸣，载其木痕",
        "视桂泣血，载其斫桂",
    ]

    choose_current_dialog_option(game, 1)

    assert game.mainline["wugang_checked"] is True
    assert game.mainline["wugang_polluted"] is False
    assert game.save_manager.saved_payloads[-1]["mainline"]["wugang_checked"] is True
    assert game.dialog_box.active is True
    assert any("斧声未绝" in line for line in game.dialog_box.lines)


def test_wugang_has_no_normal_dialogue_before_laurel_bleeds():
    game = Game()
    game.mode = game.MODE_PLAYING
    game.player.rect.center = game.wugang.interaction_rect.center
    game.player.position.xy = game.player.rect.topleft
    game.input_manager._pressed_once.add(config.ACTION_INTERACT)

    game._update_playing(0.016)

    assert game.laurel_tree.bleeding is False
    assert game.dialog_box.active is False
    assert game.game_state.violation_count == 1


def test_wugang_run_interact_at_bleeding_laurel_causes_wugang_pollution():
    game = Game()
    game.save_manager = MemorySaveManager()
    game.current_slot_id = 1
    game.current_save_data = game.save_manager.default_save(1)
    game._apply_save_data(game.current_save_data)
    game.mode = game.MODE_PLAYING
    game.player.rect.center = game.wugang.interaction_rect.center
    game.player.position.xy = game.player.rect.topleft
    game.laurel_tree.set_bleeding(True)
    game.input_manager._pressed_once.add(config.ACTION_INTERACT)
    game.input_manager.is_pressed = lambda action: action == config.ACTION_RUN

    game._update_playing(0.016)

    assert game.mainline["wugang_checked"] is False
    assert [choice["id"] for choice in game.dialog_box.choices] == ["wugang_overstep", "wugang_record"]

    choose_current_dialog_option(game, 0)

    assert game.mainline["wugang_checked"] is True
    assert game.mainline["wugang_polluted"] is True
    assert game.save_manager.saved_payloads[-1]["mainline"]["wugang_polluted"] is True
    assert game.dialog_box.active is True
    assert any("续记一响" in line for line in game.dialog_box.lines)
    assert any("木色" in line for line in game.dialog_box.lines)


def test_yutu_check_completes_from_behind():
    game = Game()
    game.save_manager = MemorySaveManager()
    game.current_slot_id = 1
    game.current_save_data = game.save_manager.default_save(1)
    game._apply_save_data(game.current_save_data)
    game.mode = game.MODE_PLAYING
    game.player.rect.center = (game.yutu.interaction_rect.right - 5, game.yutu.rect.centery)
    game.player.position.xy = game.player.rect.topleft
    game.input_manager._pressed_once.add(config.ACTION_INTERACT)

    game._update_playing(0.016)

    assert game.mainline["yutu_checked"] is False
    assert game.dialog_box.active is True
    assert [choice["id"] for choice in game.dialog_box.choices] == ["yutu_overstep", "yutu_record"]
    assert [choice["text"] for choice in game.dialog_box.choices] == [
        "闻嗅药香，记其丹成",
        "睹其落杵，记其药色",
    ]

    choose_current_dialog_option(game, 1)

    assert game.mainline["yutu_checked"] is True
    assert game.mainline["yutu_polluted"] is False
    assert game.save_manager.saved_payloads[-1]["mainline"]["yutu_checked"] is True
    assert game.dialog_box.active is True
    assert any("杵声未停" in line for line in game.dialog_box.lines)


def test_yutu_check_can_start_from_above_without_front_violation():
    game = Game()
    game.mode = game.MODE_PLAYING
    game.player.rect.midbottom = (game.yutu.rect.centerx, game.yutu.rect.top - 2)
    game.player.position.xy = game.player.rect.topleft
    game.input_manager._pressed_once.add(config.ACTION_INTERACT)

    game._update_playing(0.016)

    assert game.game_state.violation_count == 0
    assert game.dialog_box.choice_context == "yutu_check"


def test_yutu_check_can_start_from_below_without_front_violation():
    game = Game()
    game.mode = game.MODE_PLAYING
    game.player.rect.midtop = (game.yutu.rect.centerx, game.yutu.rect.bottom + 2)
    game.player.position.xy = game.player.rect.topleft
    game.input_manager._pressed_once.add(config.ACTION_INTERACT)

    game._update_playing(0.016)

    assert game.game_state.violation_count == 0
    assert game.dialog_box.choice_context == "yutu_check"


def test_yutu_check_is_reachable_from_right_of_pound_table():
    game = Game()
    game.save_manager = MemorySaveManager()
    game.current_slot_id = 1
    game.current_save_data = game.save_manager.default_save(1)
    game._apply_save_data(game.current_save_data)
    game.mode = game.MODE_PLAYING
    game.player.rect.midleft = (game.pound_table.rect.right, game.yutu.rect.centery)
    game.player.position.xy = game.player.rect.topleft
    game.input_manager._pressed_once.add(config.ACTION_INTERACT)

    game._update_playing(0.016)

    assert game.yutu.player_in_range is True
    assert game.dialog_box.active is True
    assert game.dialog_box.choice_context == "yutu_check"


def test_yutu_run_interact_from_behind_causes_yutu_pollution():
    game = Game()
    game.save_manager = MemorySaveManager()
    game.current_slot_id = 1
    game.current_save_data = game.save_manager.default_save(1)
    game._apply_save_data(game.current_save_data)
    game.mode = game.MODE_PLAYING
    game.player.rect.center = (game.yutu.interaction_rect.right - 5, game.yutu.rect.centery)
    game.player.position.xy = game.player.rect.topleft
    game.input_manager._pressed_once.add(config.ACTION_INTERACT)
    game.input_manager.is_pressed = lambda action: action == config.ACTION_RUN

    game._update_playing(0.016)

    assert game.mainline["yutu_checked"] is False
    assert [choice["id"] for choice in game.dialog_box.choices] == ["yutu_overstep", "yutu_record"]

    choose_current_dialog_option(game, 0)

    assert game.mainline["yutu_checked"] is True
    assert game.mainline["yutu_polluted"] is True
    assert game.save_manager.saved_payloads[-1]["mainline"]["yutu_polluted"] is True
    assert game.dialog_box.active is True
    assert any("近闻药香" in line for line in game.dialog_box.lines)
    assert any("泛白" in line for line in game.dialog_box.lines)


def test_yutu_front_interaction_is_violation_not_pollution():
    game = Game()
    game.save_manager = MemorySaveManager()
    game.current_slot_id = 1
    game.current_save_data = game.save_manager.default_save(1)
    game._apply_save_data(game.current_save_data)
    game.mode = game.MODE_PLAYING
    game.player.rect.center = (game.yutu.interaction_rect.left + 5, game.yutu.rect.centery)
    game.player.position.xy = game.player.rect.topleft
    game.input_manager._pressed_once.add(config.ACTION_INTERACT)

    game._update_playing(0.016)

    assert game.mainline["yutu_checked"] is False
    assert game.mainline["yutu_polluted"] is False
    assert game.game_state.violation_count == 1
    assert game.save_manager.saved_payloads[-1]["violation_count"] == 1
    assert game.dialog_box.active is True
    assert any("绕到身后" in line for line in game.dialog_box.lines)


def test_yutu_back_arc_does_not_trigger_eye_contact_rule():
    game = Game()
    game.save_manager = MemorySaveManager()
    game.current_slot_id = 1
    game.current_save_data = game.save_manager.default_save(1)
    game._apply_save_data(game.current_save_data)
    game.mode = game.MODE_PLAYING
    game.yutu.is_pounding = True
    game.player.rect.center = (game.yutu.interaction_rect.right - 5, game.yutu.rect.centery)
    game.player.position.xy = game.player.rect.topleft
    game.player.facing = "left"

    game._update_rule_checks(0.016)

    assert game.game_state.violation_count == 0
    assert game.save_manager.saved_payloads == []

def test_guanghan_gate_blocks_until_office_checks_complete():
    game = Game()
    game.save_manager = MemorySaveManager()
    game.current_slot_id = 1
    game.current_save_data = game.save_manager.default_save(1)
    game._apply_save_data(game.current_save_data)
    game.mode = game.MODE_PLAYING
    game.player.rect.center = game.palace_entry_rect.center
    game.player.position.xy = game.player.rect.topleft
    game.input_manager._pressed_once.add(config.ACTION_INTERACT)

    game._update_playing(0.016)

    assert game.mode == game.MODE_PLAYING
    assert game.dialog_box.active is True
    assert any("验职未齐" in line for line in game.dialog_box.lines)


def test_guanghan_gate_enters_inner_hall_after_office_checks():
    game = Game()
    game.save_manager = MemorySaveManager()
    game.current_slot_id = 1
    game.current_save_data = game.save_manager.default_save(1)
    game._apply_save_data(game.current_save_data)
    game.mode = game.MODE_PLAYING
    game.mainline["wugang_checked"] = True
    game.mainline["yutu_checked"] = True
    game.player.rect.center = game.palace_entry_rect.center
    game.player.position.xy = game.player.rect.topleft
    game.input_manager._pressed_once.add(config.ACTION_INTERACT)

    game._update_playing(0.016)

    finish_scene_transition(game)
    assert game.mode == game.MODE_GUANGHAN
    assert game.save_manager.saved_payloads[-1]["mainline"]["wugang_checked"] is True
    assert game.save_manager.saved_payloads[-1]["mainline"]["yutu_checked"] is True


def test_guanghan_gate_visual_opens_only_after_both_office_checks():
    game = Game()

    game._draw_playing()
    assert game.palace_wall.gate_open is False

    game.mainline["wugang_checked"] = True
    game._draw_playing()
    assert game.palace_wall.gate_open is False

    game.mainline["yutu_checked"] = True
    game._draw_playing()
    assert game.palace_wall.gate_open is True


def test_guanghan_register_opens_from_front_of_desk():
    game = Game()
    game.mode = game.MODE_GUANGHAN
    game.report_started = False
    game.player.rect.center = game.guanghan_register_rect.center
    game.player.position.xy = game.player.rect.topleft
    game.input_manager._pressed_once.add(config.ACTION_INTERACT)

    game._update_guanghan(0.016)

    assert game.envoy_register.active is True
    assert game.envoy_register.mode == game.envoy_register.MODE_REGISTER
    assert game.guanghan_register_rect.bottom > game.guanghan_register_collision_rect.bottom
    assert not game.guanghan_register_rect.colliderect(game.guanghan_records_rect)
    assert game.guanghan_register_rect.colliderect(game.guanghan_register_side_rect)
    assert game.guanghan_records_rect.colliderect(game.guanghan_records_side_rect)
    assert any(rect.bottom == game.guanghan_register_desk_rect.bottom for rect in game._guanghan_collision_rects())


def test_guanghan_records_open_from_separate_front_position():
    game = Game()
    game.mode = game.MODE_GUANGHAN
    game.player.rect.center = game.guanghan_records_rect.center
    game.player.position.xy = game.player.rect.topleft
    game.input_manager._pressed_once.add(config.ACTION_INTERACT)

    game._update_guanghan(0.016)

    assert game.envoy_register.active is True
    assert game.envoy_register.mode == game.envoy_register.MODE_READ


def test_guanghan_register_and_records_are_reachable_from_opposite_desk_sides():
    game = Game()
    game.mode = game.MODE_GUANGHAN

    game.player.rect.center = game.guanghan_records_side_rect.center
    game.player.position.xy = game.player.rect.topleft
    game.input_manager._pressed_once.add(config.ACTION_INTERACT)
    game._update_guanghan(0.016)
    assert game.envoy_register.mode == game.envoy_register.MODE_READ

    game.envoy_register.close()
    game.input_manager._pressed_once.clear()
    game.player.rect.center = game.guanghan_register_side_rect.center
    game.player.position.xy = game.player.rect.topleft
    game.input_manager._pressed_once.add(config.ACTION_INTERACT)
    game._update_guanghan(0.016)
    assert game.envoy_register.mode == game.envoy_register.MODE_REGISTER

def test_guanghan_normal_report_starts_countdown_without_pollution():
    game = Game()
    game.save_manager = MemorySaveManager()
    game.current_slot_id = 1
    game.current_save_data = game.save_manager.default_save(1)
    game._apply_save_data(game.current_save_data)
    game.mode = game.MODE_PLAYING
    game.mainline["wugang_checked"] = True
    game.mainline["yutu_checked"] = True
    game.mainline["wugang_polluted"] = False
    game.mainline["yutu_polluted"] = False
    game.envoy_register.apply_save_data({"name": "来使", "registered": True})
    game.player.rect.center = game.palace_entry_rect.center
    game.player.position.xy = game.player.rect.topleft
    game.input_manager._pressed_once.add(config.ACTION_INTERACT)

    game._update_playing(0.016)

    finish_scene_transition(game)
    assert game.mode == game.MODE_GUANGHAN
    assert game.mainline["report_completed"] is False
    assert game.report_staging_active is False

    game.player.rect.center = game.guanghan_report_rect.center
    game.player.position.xy = game.player.rect.topleft
    game._update_guanghan(0.016)

    assert game.mainline["report_completed"] is True
    assert game.mainline["return_countdown_active"] is True
    assert game.mainline["return_countdown_remaining"] == 60.0
    assert game.save_manager.saved_payloads[-1]["mainline"]["report_completed"] is True
    assert game.report_staging_active is True
    assert game.dialog_box.active is False

    game._finish_report_staging()

    assert game.dialog_box.active is True
    assert any("复命既毕" in line for line in game.dialog_box.lines)
    assert any("候月" in line for line in game.dialog_box.lines)


def test_guanghan_report_does_not_require_personal_name_or_registration():
    game = Game()
    game.mode = game.MODE_GUANGHAN
    game.mainline["wugang_checked"] = True
    game.mainline["yutu_checked"] = True
    game.player.rect.center = game.guanghan_report_rect.center
    game.player.position.xy = game.player.rect.topleft
    game.input_manager._pressed_once.add(config.ACTION_INTERACT)

    game._update_guanghan(0.016)

    assert game.envoy_register.registered is False
    assert game.report_started is True
    assert game.mainline["report_completed"] is True
    assert game.report_staging_active is True
    assert game.dialog_box.active is False


def test_guanghan_countdown_decreases_while_active():
    game = Game()
    game.save_manager = MemorySaveManager()
    game.current_slot_id = 1
    game.current_save_data = game.save_manager.default_save(1)
    game._apply_save_data(game.current_save_data)
    game.mode = game.MODE_GUANGHAN
    game.mainline["return_countdown_active"] = True
    game.mainline["return_countdown_remaining"] = 60.0

    game._update_guanghan(5.5)

    assert game.mainline["return_countdown_remaining"] == 54.5


def test_guanghan_player_keeps_updating_after_report(monkeypatch):
    game = Game()
    game.mode = game.MODE_GUANGHAN
    game.report_started = True
    game.mainline["report_completed"] = True
    updated = []
    monkeypatch.setattr(game.player, "update", lambda *args: updated.append(args))

    game._update_guanghan(0.016)

    assert updated


def test_guanghan_player_keeps_drawing_after_report(monkeypatch):
    game = Game()
    game.mode = game.MODE_GUANGHAN
    game.report_started = True
    drawn = []
    monkeypatch.setattr(game.player, "draw", lambda *args, **kwargs: drawn.append((args, kwargs)))

    game._draw_guanghan()

    assert drawn


def test_guanghan_draws_return_countdown_hud(monkeypatch):
    import core.game as game_module

    game = Game()
    game.save_manager = MemorySaveManager()
    game.current_slot_id = 1
    game.current_save_data = game.save_manager.default_save(1)
    game._apply_save_data(game.current_save_data)
    game.mode = game.MODE_GUANGHAN
    game.mainline["return_countdown_active"] = True
    game.mainline["return_countdown_remaining"] = 30.0
    rendered = []
    monkeypatch.setattr(game_module, "render_text", lambda surface, text, *args: rendered.append(text) or True)

    game._draw_guanghan()

    assert "候月 00:30" in rendered


def test_courtyard_draws_return_countdown_hud(monkeypatch):
    import core.game as game_module

    game = Game()
    game.save_manager = MemorySaveManager()
    game.current_slot_id = 1
    game.current_save_data = game.save_manager.default_save(1)
    game._apply_save_data(game.current_save_data)
    game.mode = game.MODE_PLAYING
    game.mainline["return_countdown_active"] = True
    game.mainline["return_countdown_remaining"] = 30.0
    rendered = []
    monkeypatch.setattr(game_module, "render_text", lambda surface, text, *args: rendered.append(text) or True)

    game._draw_playing()

    assert "候月 00:30" in rendered


def test_home_draws_return_countdown_hud(monkeypatch):
    import core.game as game_module

    game = Game()
    game.save_manager = MemorySaveManager()
    game.current_slot_id = 1
    game.current_save_data = game.save_manager.default_save(1)
    game._apply_save_data(game.current_save_data)
    game.mode = game.MODE_HOME
    game.mainline["return_countdown_active"] = True
    game.mainline["return_countdown_remaining"] = 30.0
    rendered = []
    monkeypatch.setattr(game_module, "render_text", lambda surface, text, *args: rendered.append(text) or True)

    game._draw_home()

    assert "候月 00:30" not in rendered


def test_guanghan_countdown_zero_triggers_change_ending():
    game = Game()
    game.save_manager = MemorySaveManager()
    game.current_slot_id = 1
    game.current_save_data = game.save_manager.default_save(1)
    game._apply_save_data(game.current_save_data)
    game.mode = game.MODE_GUANGHAN
    game.mainline["report_completed"] = True
    game.mainline["return_countdown_active"] = True
    game.mainline["return_countdown_remaining"] = 0.5

    game._update_guanghan(0.75)

    assert game.mainline["return_countdown_active"] is False
    assert game.mainline["return_countdown_remaining"] == 0.0
    assert game.mainline["ending"] == "be_change"
    assert game.save_manager.saved_payloads[-1]["mainline"]["ending"] == "be_change"
    assert game.mode == game.MODE_ENDING_CG
    assert game.ending_cg.active is True
    assert game.ending_cg.ending_id == "be_change"
    assert game.dialog_box.active is False

def test_guanghan_interact_after_normal_report_returns_via_courtyard_to_moon_valley():
    game = Game()
    game.save_manager = MemorySaveManager()
    game.current_slot_id = 1
    game.current_save_data = game.save_manager.default_save(1)
    game._apply_save_data(game.current_save_data)
    game.mode = game.MODE_GUANGHAN
    game.mainline["report_completed"] = True
    game.mainline["return_countdown_active"] = True
    game.mainline["return_countdown_remaining"] = 30.0
    game.player.rect.center = game.guanghan_exit_rect.center
    game.player.position.xy = game.player.rect.topleft
    game.input_manager._pressed_once.add(config.ACTION_INTERACT)

    game._update_guanghan(0.016)

    finish_scene_transition(game)
    assert game.mode == game.MODE_PLAYING
    assert game.mainline["return_countdown_active"] is True
    assert game.mainline["return_departed_on_time"] is False
    assert 0.0 < game.mainline["return_countdown_remaining"] < 30.0
    assert game.mainline["ending"] == ""
    assert game.player.rect.midbottom == config.COURTYARD_NORTH_SPAWN

    game.player.rect.center = game.courtyard_south_exit_rect.center
    game.player.position.xy = game.player.rect.topleft
    game.input_manager._pressed_once.add(config.ACTION_INTERACT)
    game._update_playing(0.016)

    finish_scene_transition(game)
    assert game.mode == game.MODE_HOME
    assert game.player.rect.top >= game.home_tutorial.gate_trigger_rect.bottom
    assert game.save_manager.saved_payloads[-1]["mainline"]["return_countdown_active"] is False
    assert game.save_manager.saved_payloads[-1]["mainline"]["return_departed_on_time"] is True


def test_home_altar_before_countdown_zero_triggers_he():
    game = Game()
    game.save_manager = MemorySaveManager()
    game.current_slot_id = 1
    game.current_save_data = game.save_manager.default_save(1)
    game._apply_save_data(game.current_save_data)
    game.mode = game.MODE_HOME
    game.mainline["report_completed"] = True
    game.mainline["return_departed_on_time"] = True
    game.mainline["return_countdown_active"] = False
    game.mainline["return_countdown_remaining"] = 0.0
    game.player.rect.center = game.home_tutorial.altar_rect.center
    game.player.position.xy = game.player.rect.topleft

    game._update_home(0.016)

    assert game.mainline["return_countdown_active"] is False
    assert game.mainline["ending"] == "he_return_earth"
    assert game.save_manager.saved_payloads[-1]["mainline"]["ending"] == "he_return_earth"
    assert game.mode == game.MODE_ENDING_CG
    assert game.ending_cg.active is True
    assert game.ending_cg.ending_id == "he_return_earth"
    assert game.dialog_box.active is False


def test_home_countdown_zero_triggers_change_ending():
    game = Game()
    game.save_manager = MemorySaveManager()
    game.current_slot_id = 1
    game.current_save_data = game.save_manager.default_save(1)
    game._apply_save_data(game.current_save_data)
    game.mode = game.MODE_HOME
    game.mainline["report_completed"] = True
    game.mainline["return_countdown_active"] = True
    game.mainline["return_countdown_remaining"] = 0.5
    game.player.rect.topleft = (80, 80)
    game.player.position.xy = game.player.rect.topleft

    game._update_home(0.75)

    assert game.mainline["return_countdown_active"] is True
    assert game.mainline["return_countdown_remaining"] == 0.5
    assert game.mainline["ending"] == ""
    assert game.mode == game.MODE_HOME


def test_clean_route_reports_without_name_leaves_once_and_returns_to_altar_he():
    game = Game()
    game.save_manager = MemorySaveManager()
    game.current_slot_id = 1
    game.current_save_data = game.save_manager.default_save(1)
    game._apply_save_data(game.current_save_data)
    game.mode = game.MODE_PLAYING
    game.mainline["wugang_checked"] = True
    game.mainline["yutu_checked"] = True

    game.player.rect.center = game.palace_entry_rect.center
    game.player.position.xy = game.player.rect.topleft
    game.input_manager._pressed_once.add(config.ACTION_INTERACT)
    game._update_playing(0.016)
    finish_scene_transition(game)
    assert game.mode == game.MODE_GUANGHAN

    game.player.rect.center = game.guanghan_report_rect.center
    game.player.position.xy = game.player.rect.topleft
    game.input_manager._pressed_once.clear()
    game.input_manager._pressed_once.add(config.ACTION_INTERACT)
    game._update_guanghan(0.016)

    assert game.envoy_register.registered is False
    assert game.mainline["report_completed"] is True
    assert game.mainline["return_countdown_active"] is True
    game._finish_report_staging()
    game.dialog_box.close()

    game.player.rect.center = game.guanghan_exit_rect.center
    game.player.position.xy = game.player.rect.topleft
    game.input_manager._pressed_once.clear()
    game.input_manager._pressed_once.add(config.ACTION_INTERACT)
    game._update_guanghan(0.016)

    finish_scene_transition(game)
    assert game.mode == game.MODE_PLAYING
    assert game.mainline["return_departed_on_time"] is False
    assert game.mainline["return_countdown_active"] is True
    assert game.mainline["return_countdown_remaining"] > 0.0

    game.player.rect.topleft = (100, 300)
    game.player.position.xy = game.player.rect.topleft
    game._update_playing(1.0)
    assert game.mainline["ending"] == ""
    assert game.mainline["return_countdown_active"] is True

    game.player.rect.center = game.courtyard_south_exit_rect.center
    game.player.position.xy = game.player.rect.topleft
    game.input_manager._pressed_once.clear()
    game.input_manager._pressed_once.add(config.ACTION_INTERACT)
    game._update_playing(0.016)
    finish_scene_transition(game)
    assert game.mode == game.MODE_HOME

    game.player.rect.center = game.home_tutorial.altar_rect.center
    game.player.position.xy = game.player.rect.topleft
    game._update_home(0.016)

    assert game.mainline["ending"] == "he_return_earth"
    assert game.mode == game.MODE_ENDING_CG


def test_timely_departure_blocks_returning_to_guanghan_wait():
    game = Game()
    game.mode = game.MODE_PLAYING
    game.mainline["wugang_checked"] = True
    game.mainline["yutu_checked"] = True
    game.mainline["report_completed"] = True
    game.mainline["return_departed_on_time"] = True
    game.player.rect.center = game.palace_entry_rect.center
    game.player.position.xy = game.player.rect.topleft
    game.input_manager._pressed_once.add(config.ACTION_INTERACT)

    game._update_playing(0.016)

    assert game.mode == game.MODE_PLAYING
    assert game.dialog_box.active is True
    assert any("不得重入" in line for line in game.dialog_box.lines)


def test_polluted_report_blocks_courtyard_south_gate_until_pool_verdict():
    game = Game()
    game.mode = game.MODE_PLAYING
    game.mainline["pending_pool_ending"] = "be_wugang"
    game.player.rect.center = game.courtyard_south_exit_rect.center
    game.player.position.xy = game.player.rect.topleft
    game.input_manager._pressed_once.add(config.ACTION_INTERACT)

    game._update_playing(0.016)

    assert game.mode == game.MODE_PLAYING
    assert game.mainline["ending"] == ""
    assert game.dialog_box.active is True
    assert any("月池" in line and "不得返月谷" in line for line in game.dialog_box.lines)
    assert any(rect.collidepoint(game.courtyard_south_exit_rect.centerx, 500) for rect in game._get_collision_rects())


def test_guanghan_wugang_pollution_starts_pool_fake_report():
    game = Game()
    game.save_manager = MemorySaveManager()
    game.current_slot_id = 1
    game.current_save_data = game.save_manager.default_save(1)
    game._apply_save_data(game.current_save_data)
    game.mode = game.MODE_PLAYING
    game.mainline["wugang_checked"] = True
    game.mainline["yutu_checked"] = True
    game.mainline["wugang_polluted"] = True
    game.mainline["yutu_polluted"] = False
    game.envoy_register.apply_save_data({"name": "来使", "registered": True})
    game.player.rect.center = game.palace_entry_rect.center
    game.player.position.xy = game.player.rect.topleft
    game.input_manager._pressed_once.add(config.ACTION_INTERACT)

    game._update_playing(0.016)

    finish_scene_transition(game)
    assert game.mode == game.MODE_GUANGHAN
    game.player.rect.center = game.guanghan_report_rect.center
    game.player.position.xy = game.player.rect.topleft
    game._update_guanghan(0.016)

    assert game.mainline["report_completed"] is False
    assert game.mainline["return_countdown_active"] is False
    assert game.mainline["pending_pool_ending"] == "be_wugang"
    assert game.save_manager.saved_payloads[-1]["mainline"]["pending_pool_ending"] == "be_wugang"
    assert game.report_staging_active is True
    assert game.dialog_box.active is False

    game._finish_report_staging()

    assert game.dialog_box.active is True
    assert any("池边照一照" in line for line in game.dialog_box.lines)


def test_guanghan_yutu_pollution_starts_pool_fake_report():
    game = Game()
    game.save_manager = MemorySaveManager()
    game.current_slot_id = 1
    game.current_save_data = game.save_manager.default_save(1)
    game._apply_save_data(game.current_save_data)
    game.mode = game.MODE_PLAYING
    game.mainline["wugang_checked"] = True
    game.mainline["yutu_checked"] = True
    game.mainline["wugang_polluted"] = False
    game.mainline["yutu_polluted"] = True
    game.envoy_register.apply_save_data({"name": "来使", "registered": True})
    game.player.rect.center = game.palace_entry_rect.center
    game.player.position.xy = game.player.rect.topleft
    game.input_manager._pressed_once.add(config.ACTION_INTERACT)

    game._update_playing(0.016)

    finish_scene_transition(game)
    assert game.mode == game.MODE_GUANGHAN
    game.player.rect.center = game.guanghan_report_rect.center
    game.player.position.xy = game.player.rect.topleft
    game._update_guanghan(0.016)

    assert game.mainline["report_completed"] is False
    assert game.mainline["return_countdown_active"] is False
    assert game.mainline["pending_pool_ending"] == "be_yutu"
    assert game.save_manager.saved_payloads[-1]["mainline"]["pending_pool_ending"] == "be_yutu"
    assert game.report_staging_active is True
    assert game.dialog_box.active is False

    game._finish_report_staging()

    assert game.dialog_box.active is True
    assert any("池边照一照" in line for line in game.dialog_box.lines)


def test_guanghan_double_pollution_sets_laurel_pool_ending():
    game = Game()
    game.save_manager = MemorySaveManager()
    game.current_slot_id = 1
    game.current_save_data = game.save_manager.default_save(1)
    game._apply_save_data(game.current_save_data)
    game.mode = game.MODE_PLAYING
    game.mainline["wugang_checked"] = True
    game.mainline["yutu_checked"] = True
    game.mainline["wugang_polluted"] = True
    game.mainline["yutu_polluted"] = True
    game.envoy_register.apply_save_data({"name": "来使", "registered": True})
    game.player.rect.center = game.palace_entry_rect.center
    game.player.position.xy = game.player.rect.topleft
    game.input_manager._pressed_once.add(config.ACTION_INTERACT)

    game._update_playing(0.016)

    finish_scene_transition(game)
    assert game.mode == game.MODE_GUANGHAN
    game.player.rect.center = game.guanghan_report_rect.center
    game.player.position.xy = game.player.rect.topleft
    game._update_guanghan(0.016)

    assert game.mainline["report_completed"] is False
    assert game.mainline["return_countdown_active"] is False
    assert game.mainline["pending_pool_ending"] == "be_double"
    assert game.save_manager.saved_payloads[-1]["mainline"]["pending_pool_ending"] == "be_double"
    assert game.report_staging_active is True
    assert game.dialog_box.active is False

    game._finish_report_staging()

    assert game.dialog_box.active is True
    assert any("皆已验毕" in line for line in game.dialog_box.lines)


def test_guanghan_pending_wugang_pool_ending_waits_for_leave_input():
    game = Game()
    game.save_manager = MemorySaveManager()
    game.current_slot_id = 1
    game.current_save_data = game.save_manager.default_save(1)
    game._apply_save_data(game.current_save_data)
    game.mode = game.MODE_GUANGHAN
    game.mainline["pending_pool_ending"] = "be_wugang"
    game.dialog_box.active = False

    game._update_guanghan(0.016)

    assert game.mainline["pending_pool_ending"] == "be_wugang"
    assert game.mode == game.MODE_GUANGHAN

    game.player.rect.center = game.guanghan_exit_rect.center
    game.player.position.xy = game.player.rect.topleft
    game.input_manager._pressed_once.add(config.ACTION_INTERACT)
    game._update_guanghan(0.016)

    finish_scene_transition(game)
    assert game.mode == game.MODE_PLAYING
    assert game.mainline["pending_pool_ending"] == "be_wugang"
    assert game.mainline["ending"] == ""

    game.player.rect.center = game.moon_pool.rect.center
    game.player.position.xy = game.player.rect.topleft
    game.input_manager._pressed_once.add(config.ACTION_INTERACT)
    game._update_playing(0.016)

    assert game.mainline["pending_pool_ending"] == ""
    assert game.mainline["ending"] == "be_wugang"
    assert game.save_manager.saved_payloads[-1]["mainline"]["ending"] == "be_wugang"
    assert game.mode == game.MODE_ENDING_CG
    assert game.ending_cg.active is True
    assert game.ending_cg.ending_id == "be_wugang"
    assert game.dialog_box.active is False


def test_guanghan_pending_yutu_pool_ending_triggers_at_courtyard_pool():
    game = Game()
    game.save_manager = MemorySaveManager()
    game.current_slot_id = 1
    game.current_save_data = game.save_manager.default_save(1)
    game._apply_save_data(game.current_save_data)
    game.mode = game.MODE_GUANGHAN
    game.mainline["pending_pool_ending"] = "be_yutu"
    game.dialog_box.active = False
    game.player.rect.center = game.guanghan_exit_rect.center
    game.player.position.xy = game.player.rect.topleft
    game.input_manager._pressed_once.add(config.ACTION_INTERACT)

    game._update_guanghan(0.016)

    finish_scene_transition(game)
    assert game.mode == game.MODE_PLAYING
    assert game.mainline["pending_pool_ending"] == "be_yutu"

    game.player.rect.center = game.moon_pool.rect.center
    game.player.position.xy = game.player.rect.topleft
    game.input_manager._pressed_once.add(config.ACTION_INTERACT)
    game._update_playing(0.016)

    assert game.mainline["pending_pool_ending"] == ""
    assert game.mainline["ending"] == "be_yutu"
    assert game.save_manager.saved_payloads[-1]["mainline"]["ending"] == "be_yutu"
    assert game.mode == game.MODE_ENDING_CG
    assert game.ending_cg.active is True
    assert game.ending_cg.ending_id == "be_yutu"
    assert game.dialog_box.active is False


def test_guanghan_pending_double_pool_ending_triggers_laurel_consumption_at_pool():
    game = Game()
    game.save_manager = MemorySaveManager()
    game.current_slot_id = 1
    game.current_save_data = game.save_manager.default_save(1)
    game._apply_save_data(game.current_save_data)
    game.mode = game.MODE_GUANGHAN
    game.mainline["pending_pool_ending"] = "be_double"
    game.dialog_box.active = False
    game.player.rect.center = game.guanghan_exit_rect.center
    game.player.position.xy = game.player.rect.topleft
    game.input_manager._pressed_once.add(config.ACTION_INTERACT)

    game._update_guanghan(0.016)

    finish_scene_transition(game)
    assert game.mode == game.MODE_PLAYING
    assert game.mainline["pending_pool_ending"] == "be_double"

    game.player.rect.center = game.moon_pool.rect.center
    game.player.position.xy = game.player.rect.topleft
    game.input_manager._pressed_once.add(config.ACTION_INTERACT)
    game._update_playing(0.016)

    assert game.mainline["pending_pool_ending"] == ""
    assert game.mainline["ending"] == "be_double"
    assert game.save_manager.saved_payloads[-1]["mainline"]["ending"] == "be_double"
    assert game.mode == game.MODE_ENDING_CG
    assert game.ending_cg.active is True
    assert game.ending_cg.ending_id == "be_double"
    assert game.dialog_box.active is False


def test_escape_opens_save_exit_confirmation_and_autosaves():
    game = Game()
    game.save_manager = MemorySaveManager()
    game.current_slot_id = 1
    game.current_save_data = game.save_manager.default_save(1)
    game._apply_save_data(game.current_save_data)
    game.mode = game.MODE_PLAYING
    game.player.rect.topleft = (222, 333)
    game.player.position.xy = game.player.rect.topleft
    game.input_manager._pressed_once.add(config.ACTION_QUIT)

    game._update_playing(0.016)

    assert game.exit_confirm_open
    assert game.running is True
    assert game.save_manager.saved_payloads[-1]["player"]["x"] == 222
    assert game.save_manager.saved_payloads[-1]["player"]["y"] == 333


def test_loading_dead_save_restores_death_screen_and_horror_state():
    save_data = MemorySaveManager().default_save(1)
    save_data["violation_count"] = 3
    save_data["known_rules"] = {"rule": "已经读过的规条"}
    game = Game()

    game._apply_save_data(save_data)

    assert game.death_screen.active is True
    assert game.palace_wall.horror_level == 3
    assert game.distortion.horror_intensity == 0.8


def test_death_restart_keeps_rules_and_saves_clean_violation_count():
    game = Game()
    game.save_manager = MemorySaveManager()
    game.current_slot_id = 1
    game.current_save_data = game.save_manager.default_save(1)
    game.current_save_data["known_rules"] = {"rule": "已经读过的规条"}
    game.current_save_data["violation_count"] = 3
    game._apply_save_data(game.current_save_data)
    game.mode = game.MODE_PLAYING
    game.input_manager._pressed_once.add(config.ACTION_RESTART)

    game._update_playing(0.016)

    assert game.game_state.violation_count == 0
    assert game.game_state.known_rules == {"rule": "已经读过的规条"}
    assert game.save_manager.saved_payloads[-1]["violation_count"] == 0
    assert game.save_manager.saved_payloads[-1]["known_rules"] == {"rule": "已经读过的规条"}


def test_death_restart_returns_to_the_courtyard_south_spawn_outside_the_wall():
    game = Game()
    game.save_manager = MemorySaveManager()
    game.current_slot_id = 1
    game.current_save_data = game.save_manager.default_save(1)
    game._apply_save_data(game.current_save_data)
    game.mode = game.MODE_PLAYING
    game.death_screen.active = True

    game._reset_after_death()

    spawn_x, spawn_y = config.COURTYARD_SOUTH_SPAWN
    assert game.player.rect.midbottom == (spawn_x, spawn_y)
    assert not any(game.player.rect.colliderect(rect) for rect in game._get_collision_rects())
    assert game.save_manager.saved_payloads[-1]["player"] == {
        "x": spawn_x - config.PLAYER_SIZE[0] // 2,
        "y": spawn_y - config.PLAYER_SIZE[1],
        "facing": "down",
    }


def test_death_restart_can_pause_briefly_without_retriggering_pool_gaze():
    game = Game()
    game.save_manager = MemorySaveManager()
    game.current_slot_id = 1
    game.current_save_data = game.save_manager.default_save(1)
    game._apply_save_data(game.current_save_data)
    game.mode = game.MODE_PLAYING
    game.game_state.violation_count = game.game_state.MAX_VIOLATIONS
    game.death_screen.active = True
    game.input_manager._pressed_once.add(config.ACTION_RESTART)

    game._update_playing(0.016)
    game.input_manager._pressed_once.clear()
    game._update_playing(2.51)

    assert game.game_state.violation_count == 0
    assert game.death_screen.active is False


def test_guanghan_rule_book_keeps_return_countdown_running():
    game = Game()
    game.mode = game.MODE_GUANGHAN
    game.mainline["report_completed"] = True
    game.mainline["return_countdown_active"] = True
    game.mainline["return_countdown_remaining"] = 10.0
    game.rule_book.is_open = True

    game._update_guanghan(1.0)

    assert game.mainline["return_countdown_remaining"] == 9.0


def test_courtyard_rule_book_keeps_return_countdown_running():
    game = Game()
    game.mode = game.MODE_PLAYING
    game.mainline["report_completed"] = True
    game.mainline["return_countdown_active"] = True
    game.mainline["return_countdown_remaining"] = 10.0
    game.rule_book.is_open = True

    game._update_playing(1.0)

    assert game.mainline["return_countdown_remaining"] == 9.0


def test_guanghan_rule_book_blocks_leave_interaction_until_closed():
    game = Game()
    game.mode = game.MODE_GUANGHAN
    game.mainline["report_completed"] = True
    game.mainline["return_countdown_active"] = True
    game.mainline["return_countdown_remaining"] = 10.0
    game.rule_book.is_open = True
    game.input_manager._pressed_once.add(config.ACTION_INTERACT)

    game._update_guanghan(0.016)

    assert game.mode == game.MODE_GUANGHAN
    assert game.rule_book.is_open is True


def test_guanghan_mode_draws_fixed_walkable_hall_background_even_after_verification():
    game = Game()
    game.game_surface.fill(palette.BLACK)
    game.envoy_register.registered = True

    assert game._draw_guanghan_background() is True
    assert game.guanghan_walkable_background.endswith("guanghan_hall_curtain.png")
    assert game.guanghan_cg_background.endswith("guanghan_hall.png")

    colors = {
        game.game_surface.get_at((x, y))[:3]
        for x in range(0, config.SCREEN_WIDTH, 24)
        for y in range(0, config.SCREEN_HEIGHT, 24)
    }
    assert len(colors) > 1
    assert any(color != palette.BLACK for color in colors)


def test_guanghan_draws_existing_transparent_chang_e_world_sprite():
    game = Game()
    game.game_surface.fill(palette.BLACK)

    game._draw_guanghan_chang_e((-240, 0))

    assert game._chang_e_frames
    assert game._chang_e_frames[0].get_at((0, 0)).a == 0
    assert game.game_surface.get_bounding_rect().width > 0


def test_guanghan_chang_e_world_sprite_stays_on_a_fixed_frame():
    game = Game()
    game.game_surface.fill(palette.BLACK)

    game._chang_e_time = 99.0
    game._draw_guanghan_chang_e((0, 0))
    first = game.game_surface.copy()
    game._chang_e_time = 0.0
    game.game_surface.fill(palette.BLACK)
    game._draw_guanghan_chang_e((0, 0))

    assert game.game_surface.get_bounding_rect() == first.get_bounding_rect()
    assert pygame.image.tostring(game.game_surface, "RGBA") == pygame.image.tostring(first, "RGBA")


def test_home_rules_dialog_close_autosaves_briefing_progress():
    game = Game()
    game.save_manager = MemorySaveManager()
    game.current_slot_id = 1
    game.current_save_data = game.save_manager.default_save(1)
    game._apply_save_data(game.current_save_data)
    game.mode = game.MODE_HOME
    game.home_tutorial.sign_read = True
    game.dialog_box.speaker_id = "home_sign"
    game.dialog_box.lines = ["最后一条规条。"]
    game.dialog_box.current_index = 0
    game.dialog_box.active = True
    game.input_manager._pressed_once.add(config.ACTION_INTERACT)

    game._update_home(0.016)

    assert game.home_tutorial.rules_briefing_complete is True
    assert game.save_manager.saved_payloads[-1]["home_tutorial"]["rules_briefing_complete"] is True


def test_escape_confirmation_works_in_home_and_transition():
    game = Game()
    game.save_manager = MemorySaveManager()
    game.current_slot_id = 1
    game.current_save_data = game.save_manager.default_save(1)
    game._apply_save_data(game.current_save_data)
    game.mode = game.MODE_HOME
    game.input_manager._pressed_once.add(config.ACTION_QUIT)

    game._update_home(0.016)

    assert game.exit_confirm_open
    assert game.running is True

    game.exit_confirm_open = False
    game.mode = game.MODE_TRANSITION
    game.input_manager._pressed_once.add(config.ACTION_QUIT)
    game._update_transition(0.016)

    assert game.exit_confirm_open
    assert game.running is True


def test_save_exit_confirmation_can_cancel_or_save_and_exit():
    game = Game()
    game.save_manager = MemorySaveManager()
    game.current_slot_id = 1
    game.current_save_data = game.save_manager.default_save(1)
    game._apply_save_data(game.current_save_data)
    game.mode = game.MODE_PLAYING
    game.exit_confirm_open = True
    game.input_manager._pressed_once.add(config.ACTION_INTERACT)

    game._update_playing(0.016)

    assert not game.exit_confirm_open
    assert game.running is True

    game.exit_confirm_open = True
    game.input_manager._pressed_once.add(config.ACTION_QUIT)
    game._update_playing(0.016)

    assert game.running is False
    assert game.save_manager.saved_payloads[-1]["slot_id"] == 1


def test_save_exit_confirmation_accepts_restart_key_as_save_exit():
    game = Game()
    game.save_manager = MemorySaveManager()
    game.current_slot_id = 1
    game.current_save_data = game.save_manager.default_save(1)
    game._apply_save_data(game.current_save_data)
    game.mode = game.MODE_PLAYING
    game.exit_confirm_open = True
    game.input_manager._pressed_once.add(config.ACTION_RESTART)

    game._update_playing(0.016)

    assert game.running is False
    assert game.save_manager.saved_payloads[-1]["slot_id"] == 1



def test_formal_courtyard_has_no_sign_board_object():
    game = Game()

    assert not hasattr(game, "sign_board")
    assert all(obj.__class__.__name__ != "SignBoard" for obj in game.world_objects)


def test_pool_rule_triggers_only_when_player_stares_at_reflection():
    game = Game()
    game.save_manager = MemorySaveManager()
    game.current_slot_id = 1
    game.current_save_data = game.save_manager.default_save(1)
    game._apply_save_data(game.current_save_data)
    game.mode = game.MODE_PLAYING
    game.player.rect.center = (game.moon_pool.rect.centerx, game.moon_pool.visual_rect.bottom + 8)
    game.player.position.xy = game.player.rect.topleft
    game.player.velocity.xy = (0, 0)
    game.player.facing = "down"

    game._update_rule_checks(1.0)

    assert game.game_state.violation_count == 0
    assert game.moon_pool.reflection_flash_timer == 0.0

    game.player.facing = "up"
    game._update_rule_checks(2.49)

    assert game.game_state.violation_count == 0
    assert game.mainline["broken_jade_obtained"] is False

    game._update_rule_checks(0.02)

    assert game.game_state.violation_count == 1
    assert game.save_manager.saved_payloads[-1]["violation_count"] == 1
    assert game.moon_pool.reflection_flash_timer > 0.0
    assert game.mainline["broken_jade_obtained"] is True
    assert game.broken_jade_view.active is True
    assert game.rule_book._rule_lines()[-2:] == [
        "1. 留名者，名归月籍。",
        "2. 命既毕，速离月宫。",
    ]


def test_third_ordinary_violation_enters_death_without_completing_npc_tasks():
    game = Game()
    game.save_manager = MemorySaveManager()
    game.current_slot_id = 1
    game.current_save_data = game.save_manager.default_save(1)
    game._apply_save_data(game.current_save_data)
    game.mode = game.MODE_PLAYING
    game.game_state.violation_count = 2
    game.player.rect.center = (game.yutu.interaction_rect.left + 5, game.yutu.rect.centery)
    game.player.position.xy = game.player.rect.topleft
    game.input_manager._pressed_once.add(config.ACTION_INTERACT)

    game._update_playing(0.016)

    assert game.game_state.violation_count == 3
    assert game.death_screen.active is True
    assert game.dialog_box.active is False
    assert game.mainline["wugang_checked"] is False
    assert game.mainline["yutu_checked"] is False
    saved = game.save_manager.saved_payloads[-1]
    assert saved["violation_count"] == 3
    assert saved["mainline"]["wugang_checked"] is False
    assert saved["mainline"]["yutu_checked"] is False


def test_countdown_zero_clears_report_staging_before_change_ending():
    game = Game()
    game.save_manager = MemorySaveManager()
    game.current_slot_id = 1
    game.current_save_data = game.save_manager.default_save(1)
    game._apply_save_data(game.current_save_data)
    game.mode = game.MODE_GUANGHAN
    game.mainline["report_completed"] = True
    game.mainline["return_countdown_active"] = True
    game.mainline["return_countdown_remaining"] = 0.5
    game._start_report_staging("change", ["复命尚未结束。"], "复命")

    game._update_guanghan(0.75)

    assert game.mode == game.MODE_ENDING_CG
    assert game.mainline["ending"] == "be_change"
    assert game.report_staging_active is False
    assert game.pending_report_dialog is None
    assert game.envoy_register.active is False
    assert game.dialog_box.active is False


def test_pending_pool_ending_triggers_from_reachable_pool_shore_without_entering_water():
    game = Game()
    game.save_manager = MemorySaveManager()
    game.current_slot_id = 1
    game.current_save_data = game.save_manager.default_save(1)
    game._apply_save_data(game.current_save_data)
    game.mode = game.MODE_PLAYING
    game.mainline["pending_pool_ending"] = "be_wugang"
    game.player.rect.midbottom = (game.moon_pool.rect.centerx, game.moon_pool.rect.top)
    game.player.position.xy = game.player.rect.topleft
    game.input_manager._pressed_once.add(config.ACTION_INTERACT)

    assert not any(game.player.rect.colliderect(rect) for rect in game._get_collision_rects())
    assert game.moon_pool_interaction_rect.colliderect(game.player.rect)

    game._update_playing(0.016)

    assert game.mainline["pending_pool_ending"] == ""
    assert game.mainline["ending"] == "be_wugang"
    assert game.mode == game.MODE_ENDING_CG


def test_death_blocks_late_npc_choice_and_repeated_interaction():
    game = Game()
    game.current_save_data = game.save_manager.default_save(1)
    game._apply_save_data(game.current_save_data)
    game.mode = game.MODE_PLAYING
    game.game_state.violation_count = game.game_state.MAX_VIOLATIONS
    game.death_screen.active = True

    game._on_dialog_choice_selected("wugang", "wugang_record")
    game._on_dialog_choice_selected("yutu", "yutu_record")
    game.player.rect.center = game.wugang.interaction_rect.center
    game.player.position.xy = game.player.rect.topleft
    game.input_manager._pressed_once.add(config.ACTION_INTERACT)

    game._update_playing(0.016)

    assert game.mainline["wugang_checked"] is False
    assert game.mainline["yutu_checked"] is False
    assert game.dialog_box.active is False


def test_death_does_not_open_downstream_gate_even_if_prior_tasks_were_complete():
    game = Game()
    game.current_save_data = game.save_manager.default_save(1)
    game._apply_save_data(game.current_save_data)
    game.mode = game.MODE_PLAYING
    game.mainline["wugang_checked"] = True
    game.mainline["yutu_checked"] = True
    game.game_state.violation_count = game.game_state.MAX_VIOLATIONS
    game.death_screen.active = True

    assert game._office_checks_complete() is False


def test_pool_gaze_commits_broken_jade_before_third_violation_death():
    game = Game()
    game.save_manager = MemorySaveManager()
    game.current_slot_id = 1
    game.current_save_data = game.save_manager.default_save(1)
    game._apply_save_data(game.current_save_data)
    game.mode = game.MODE_PLAYING
    game.game_state.violation_count = 2
    game.player.rect.center = (game.moon_pool.rect.centerx, game.moon_pool.visual_rect.bottom + 8)
    game.player.position.xy = game.player.rect.topleft
    game.player.velocity.xy = (0, 0)
    game.player.facing = "up"

    game._update_rule_checks(2.51)

    assert game.game_state.violation_count == 3
    assert game.death_screen.active is True
    assert game.mainline["broken_jade_obtained"] is True
    assert game.broken_jade_view.acquired is True
    assert game.broken_jade_view.active is True
    saved = game.save_manager.saved_payloads[-1]
    assert saved["violation_count"] == 3
    assert saved["mainline"]["broken_jade_obtained"] is True
    assert saved["mainline"]["wugang_checked"] is False
    assert saved["mainline"]["yutu_checked"] is False


def test_loaded_broken_jade_keeps_clues_without_reopening_pickup():
    save_data = MemorySaveManager().default_save(1)
    save_data["mainline"] = {"broken_jade_obtained": True}
    game = Game()

    game._apply_save_data(save_data)

    assert game.broken_jade_view.acquired is True
    assert game.broken_jade_view.active is False
    assert game.rule_book._rule_lines()[-2:] == [
        "1. 留名者，名归月籍。",
        "2. 命既毕，速离月宫。",
    ]


def test_continuing_pool_reflection_requires_a_fresh_full_gaze_timer():
    game = Game()
    game.mainline["broken_jade_obtained"] = True
    game.player.rect.center = (game.moon_pool.rect.centerx, game.moon_pool.visual_rect.bottom + 8)
    game.player.position.xy = game.player.rect.topleft
    game.player.velocity.xy = (0, 0)
    game.player.facing = "up"

    game._update_rule_checks(2.51)
    assert game.game_state.violation_count == 1

    game.player.facing = "down"
    game._update_rule_checks(0.1)
    game.player.facing = "up"
    game._update_rule_checks(2.49)
    assert game.game_state.violation_count == 1

    game._update_rule_checks(0.02)
    assert game.game_state.violation_count == 2


def test_palace_interaction_hint_is_horizontally_centered_on_door():
    game = Game()
    game.mode = game.MODE_PLAYING
    game.player.rect.center = game.palace_entry_rect.center
    game.player.position.xy = game.player.rect.topleft

    hint_rect = game._interaction_hint_rect()
    door_rect = game.palace_entry_rect.move(game._camera_offset())

    assert hint_rect is not None
    assert hint_rect.centerx == door_rect.centerx
    assert hint_rect.bottom == door_rect.top - 3


def test_scene_specific_camera_reaches_expanded_bottom_edges():
    game = Game()
    game.mode = game.MODE_PLAYING
    game.player.rect.bottom = config.COURTYARD_HEIGHT
    game.player.position.xy = game.player.rect.topleft
    assert game._camera_offset()[1] == -(config.COURTYARD_HEIGHT - config.SCREEN_HEIGHT)

    game.mode = game.MODE_GUANGHAN
    game.player.rect.bottom = config.GUANGHAN_HEIGHT
    game.player.position.xy = game.player.rect.topleft
    assert game._camera_offset()[1] == -(config.GUANGHAN_HEIGHT - config.SCREEN_HEIGHT)


def test_expanded_scene_interactions_and_collisions_stay_inside_world_bounds():
    game = Game()

    assert pygame.Rect(0, 0, config.COURTYARD_WIDTH, config.COURTYARD_HEIGHT).contains(
        game.courtyard_south_exit_rect
    )
    assert pygame.Rect(0, 0, config.GUANGHAN_WIDTH, config.GUANGHAN_HEIGHT).contains(
        game.guanghan_register_desk_rect
    )
    assert game.guanghan_register_rect.size == (64, 26)
    assert game.guanghan_records_rect.size == (64, 26)
    assert game.guanghan_records_side_rect.right >= game.guanghan_register_collision_rect.left
    assert game.guanghan_register_side_rect.left <= game.guanghan_register_collision_rect.right
    assert game.guanghan_register_collision_rect.colliderect(game.guanghan_register_desk_rect)
    assert game.guanghan_exit_rect.bottom <= config.GUANGHAN_HEIGHT

    courtyard_spawn = pygame.Rect(0, 0, *config.PLAYER_SIZE)
    courtyard_spawn.midbottom = config.COURTYARD_NORTH_SPAWN
    hall_spawn = pygame.Rect(0, 0, *config.PLAYER_SIZE)
    hall_spawn.midbottom = config.GUANGHAN_SOUTH_SPAWN
    assert not courtyard_spawn.colliderect(game.palace_entry_rect)
    assert not hall_spawn.colliderect(game.guanghan_exit_rect)
    assert not any(hall_spawn.colliderect(rect) for rect in game._guanghan_collision_rects())


def test_guanghan_south_spawn_reaches_records_register_report_and_exit():
    game = Game()

    targets = (
        game.guanghan_records_rect.center,
        game.guanghan_register_rect.center,
        game.guanghan_report_rect.center,
        game.guanghan_exit_rect.center,
    )

    assert all(_guanghan_target_is_reachable(game, target) for target in targets)


def test_courtyard_south_wall_keeps_interaction_zone_open_and_gate_facade_blocked():
    game = Game()
    collisions = game._get_collision_rects()

    assert not any(rect.collidepoint(game.courtyard_south_exit_rect.center) for rect in collisions)
    assert any(rect.collidepoint(game.courtyard_south_exit_rect.centerx, 500) for rect in collisions)
    assert any(rect.collidepoint(100, 560) for rect in collisions)
    assert any(rect.collidepoint(860, 560) for rect in collisions)
    assert any(rect.collidepoint(100, 620) for rect in collisions)
    assert any(rect.collidepoint(860, 620) for rect in collisions)
    assert any(rect.collidepoint(100, 500) for rect in collisions)
    assert any(rect.collidepoint(860, 500) for rect in collisions)


def test_guanghan_walls_block_sides_but_keep_south_doorway_open():
    game = Game()
    collisions = game._guanghan_collision_rects()

    assert any(rect.collidepoint(100, 620) for rect in collisions)
    assert any(rect.collidepoint(860, 620) for rect in collisions)
    assert not any(rect.collidepoint(game.guanghan_exit_rect.center) for rect in collisions)
    assert not any(rect.collidepoint(game.guanghan_report_rect.center) for rect in collisions)


def test_guanghan_records_open_from_desk_left_side():
    game = Game()
    game.mode = game.MODE_GUANGHAN
    game.player.rect.center = game.guanghan_records_side_rect.center
    game.player.position.xy = game.player.rect.topleft
    game.input_manager._pressed_once.add(config.ACTION_INTERACT)

    game._update_guanghan(0.016)

    assert game.envoy_register.active is True
    assert game.envoy_register.mode == game.envoy_register.MODE_READ


def test_pool_reflection_visibility_uses_same_facing_condition_as_rule():
    game = Game()
    game.player.rect.center = (game.moon_pool.rect.centerx, game.moon_pool.visual_rect.bottom + 8)

    game.player.facing = "up"
    assert game._player_faces_pool() is True

    game.player.facing = "down"
    assert game._player_faces_pool() is False


def test_tree_bleeding_event_starts_repair_window_without_violation():
    game = Game()
    game.save_manager = MemorySaveManager()
    game.current_slot_id = 1
    game.current_save_data = game.save_manager.default_save(1)
    game._apply_save_data(game.current_save_data)
    game.player.rect.center = game.laurel_tree.rect.center
    game.player.position.xy = game.player.rect.topleft

    game._on_tree_bleeding(source="wugang")
    game._check_tree_bleeding_rule(10.0)

    assert game.laurel_tree.bleeding is True
    assert game.wugang.is_resting is True
    assert game.game_state.violation_count == 0
    assert game.save_manager.saved_payloads[-1]["laurel_tree"]["bleeding"] is True


def test_unbleeding_laurel_violates_once_per_entry_with_two_second_cooldown():
    game = Game()
    game.player.rect.center = game.laurel_tree.get_rule_rect().center
    game.player.position.xy = game.player.rect.topleft

    game._update_rule_checks(0.016)
    game._update_rule_checks(2.1)

    assert game.game_state.violation_count == 1

    game.player.rect.center = (500, 500)
    game.player.position.xy = game.player.rect.topleft
    game._update_rule_checks(0.1)
    game.player.rect.center = game.laurel_tree.get_rule_rect().center
    game.player.position.xy = game.player.rect.topleft
    game._update_rule_checks(2.0)

    assert game.game_state.violation_count == 2


def test_bleeding_laurel_is_safe_and_grants_exit_grace_when_bleeding_ends():
    game = Game()
    game.player.rect.center = game.laurel_tree.get_rule_rect().center
    game.player.position.xy = game.player.rect.topleft
    game.laurel_tree.set_bleeding(True)

    game._update_rule_checks(0.1)
    game.laurel_tree.set_bleeding(False)
    game._update_rule_checks(0.1)
    game._update_rule_checks(1.0)

    assert game.game_state.violation_count == 0

    game._update_rule_checks(0.016)

    assert game.game_state.violation_count == 1


def test_report_staging_uses_fixed_shot_boundaries_and_eight_point_four_seconds():
    game = Game()

    assert game.report_staging_duration == 8.4
    assert [Game.report_shot_index_at(timer) for timer in (0.0, 1.199, 1.2, 2.399, 2.4, 7.2, 8.4)] == [0, 0, 1, 1, 2, 6, 6]

    game._start_report_staging("change", ["line"], "caption")
    game._update_report_staging(8.399)
    assert game.report_staging_active is True

    game._update_report_staging(0.001)
    assert game.report_staging_active is False
    assert game.dialog_box.active is True


def test_report_staging_can_be_skipped_with_e():
    game = Game()
    game._start_report_staging("change", ["line"], "caption")
    game.input_manager._pressed_once.add(config.ACTION_INTERACT)

    game._update_report_staging(0.0)

    assert game.report_staging_active is False
    assert game.dialog_box.active is True
