"""Moon repair mainline and event checkpoints, exercised through real game state."""

from copy import deepcopy

import pygame
import pytest

from core.audio import AudioManager, select_bgm_for_state
from core.game import Game
from core.save_manager import SaveManager
from world.sign_board import BASIC_RULES


@pytest.fixture
def game(tmp_path, monkeypatch):
    monkeypatch.setattr(AudioManager, "_load_sounds", lambda self: None)
    instance = Game()
    instance.save_manager = SaveManager(tmp_path)
    instance.current_slot_id = 1
    payload = instance.save_manager.default_save(1)
    payload.update(opening_seen=True, home_tutorial_done=True, scene="playing")
    payload["player"] = {"x": 470, "y": 385, "facing": "down"}
    instance._apply_save_data(payload)
    instance.mode = instance.MODE_PLAYING
    instance._save_current_slot()
    yield instance
    pygame.quit()


def finish_dialog(game):
    while game.dialog_box.active:
        game.dialog_box.advance()
    game.input_manager.begin_frame()


def enter_trial(game):
    game._enter_repair_hall()
    game._begin_repair_trial()
    finish_dialog(game)
    game.update(0.0)
    return game.repair_hall.trial


def reveal_crack(trial):
    trial.in_light = True
    trial.set_orientation(trial.LIGHT_YAW, trial.LIGHT_PITCH)
    assert trial.resonating
    trial.record_observation()


def test_palace_requires_all_three_checks(game):
    for wugang in (False, True):
        for yutu in (False, True):
            for repair in (False, True):
                game.mainline.update(wugang_checked=wugang, yutu_checked=yutu, repair_checked=repair)
                assert game._office_checks_complete() is (wugang and yutu and repair)


def test_sign_explains_repair_task_and_limit():
    text = "".join(BASIC_RULES.values())
    assert "修月" in text
    assert "西墙" in text
    assert "右蟾定向" in text
    assert "左蟾可转" in text
    assert "北墙" not in text
    assert "六十息" in text


def test_scene_change_and_violations_do_not_overwrite_checkpoint(game):
    before = deepcopy(game.save_manager.load(1))
    game._on_tree_bleeding()
    game.game_state.add_violation("test")
    game._start_scene_transition(game.MODE_GUANGHAN, game._enter_guanghan, "入殿")
    assert game.save_manager.load(1) == before


def test_entry_briefing_and_examination_do_not_save(game):
    before = deepcopy(game.save_manager.load(1))
    trial = enter_trial(game)
    assert trial.remaining == 60
    assert trial.phase == "active"
    trial.pick_up(0)
    trial.rotate(1)
    trial.flip()
    game.update(7.0)
    assert trial.remaining == 53
    assert game.save_manager.load(1) == before


def test_briefing_does_not_spend_trial_time(game):
    game._enter_repair_hall()
    game._begin_repair_trial()
    game.update(30.0)
    assert game.repair_hall.trial.remaining == 60
    assert game.repair_hall.trial.phase == "briefing"


def test_internal_crack_requires_the_narrow_window_light_alignment(game):
    trial = enter_trial(game)
    trial.pick_up(2)
    trial.inspecting = True
    trial.in_light = True

    assert not trial.resonating
    assert trial.reveal_strength == 0
    trial.set_orientation(trial.LIGHT_YAW, trial.LIGHT_PITCH)
    assert trial.resonating
    assert trial.reveal_strength == 1
    trial.set_orientation(trial.LIGHT_YAW + 22, trial.LIGHT_PITCH)
    assert not trial.resonating


def test_fragment_slots_refresh_on_every_hall_entry(game):
    hall = game.repair_hall
    previous = tuple(hall.piece_order)
    for _ in range(12):
        game._enter_repair_hall()
        current = tuple(hall.piece_order)
        assert sorted(current) == [0, 1, 2]
        assert current != previous
        assert current[hall.cracked_slot] == hall.trial.CRACKED_PIECE
        previous = current


def test_selection_preview_keeps_all_three_fragments_visually_sound(game, monkeypatch):
    hall = game.repair_hall
    rendered_piece_types = []

    def capture_piece(_surface, _center, index, _angle, _back, _light, _scale=1.0):
        rendered_piece_types.append(index)

    monkeypatch.setattr(hall, "draw_piece", capture_piece)
    hall._draw_piece_selection(game.game_surface)
    assert rendered_piece_types == [-1, -1, -1]
    assert hall.PIECE_NAMES == ("第壹片", "第贰片", "第叁片")
    assert hall.CLOTH_MARKS == ("元", "仲", "叔")


@pytest.mark.parametrize("index", [0, 1])
def test_wrong_piece_kills_without_overwriting_checkpoint(game, index):
    before = deepcopy(game.save_manager.load(1))
    trial = enter_trial(game)
    trial.pick_up(index)
    game._submit_repair_piece()
    assert trial.phase == "death"
    assert not game.mainline["repair_checked"]
    assert game.save_manager.load(1) == before
    game.update(2.5)
    assert game.mode == game.MODE_PLAYING
    assert game.player.rect.topleft == (470, 385)
    assert game.save_manager.load(1) == before


def test_timeout_wins_over_input_on_expiry_frame(game):
    trial = enter_trial(game)
    trial.pick_up(2)
    trial.remaining = 0.01
    game.player.rect.center = game.repair_hall.tray_zone.center
    game.player.position.xy = game.player.rect.topleft
    game.input_manager._pressed_once.add("interact")
    game.update(0.02)
    assert trial.phase == "death"
    assert not game.mainline["repair_checked"]


def test_correct_piece_freezes_timer_then_saves_once_after_sealing(game):
    before = deepcopy(game.save_manager.load(1))
    trial = enter_trial(game)
    game.update(20.0)
    trial.pick_up(2)
    reveal_crack(trial)
    game._submit_repair_piece()
    assert trial.phase == "sealing"
    assert trial.remaining == 40
    assert game.save_manager.load(1) == before
    game.update(6.0)
    assert game.mainline["repair_checked"]
    saved = deepcopy(game.save_manager.load(1))
    assert saved["checkpoint_id"] == "repair_completed"
    assert saved["scene"] == "repair_hall"
    game.update(20.0)
    assert game.save_manager.load(1) == saved
    game._start_slot(1)
    assert game.mode == "repair_hall"
    assert game.repair_hall.trial.phase == "complete"


def test_death_rolls_back_to_latest_completed_task(game):
    game._complete_yutu_check(False)
    finish_dialog(game)
    saved = deepcopy(game.save_manager.load(1))
    game.mainline["wugang_checked"] = True  # uncommitted runtime changes
    game.game_state.violation_count = 3
    game._reset_after_death()
    assert game.mainline["yutu_checked"]
    assert not game.mainline["wugang_checked"]
    assert game.game_state.violation_count == saved["violation_count"]
    assert game.save_manager.load(1) == saved


def test_closing_window_or_returning_to_menu_does_not_save_trial(game):
    before = deepcopy(game.save_manager.load(1))
    enter_trial(game)
    game._return_to_main_menu_from_pause()
    assert game.save_manager.load(1) == before


def test_manual_save_copies_checkpoint_not_trial_progress(game):
    before = deepcopy(game.save_manager.load(1))
    enter_trial(game)
    game._save_game_to_slot(2)
    saved = game.save_manager.load(2)
    assert saved["scene"] == before["scene"]
    assert saved["mainline"] == before["mainline"]
    assert saved["player"] == before["player"]


def test_repair_room_uses_same_square_music():
    assert select_bgm_for_state("repair_hall", {}) == select_bgm_for_state("playing", {})


def test_pre_report_legacy_save_still_requires_repair(game):
    payload = game.save_manager.default_save(1)
    payload["mainline"].pop("repair_checked", None)
    payload["mainline"].update(wugang_checked=True, yutu_checked=True)
    game._apply_save_data(payload)
    assert not game._office_checks_complete()


def test_legacy_post_report_save_can_finish_without_new_task_deadlock(game):
    payload = game.save_manager.default_save(1)
    payload["mainline"].pop("repair_checked", None)
    payload["mainline"].update(wugang_checked=True, yutu_checked=True, report_completed=True)
    game._apply_save_data(payload)
    assert game.mainline["repair_checked"]


def test_legacy_inside_hall_before_report_returns_to_courtyard_for_repair(game):
    payload = game.save_manager.default_save(1)
    payload.update(opening_seen=True, home_tutorial_done=True, scene="guanghan")
    payload["mainline"].pop("repair_checked", None)
    payload["mainline"].update(wugang_checked=True, yutu_checked=True)
    game.save_manager.save(1, payload)
    game._start_slot(1)
    assert game.mode == game.MODE_PLAYING
    assert not game.mainline["repair_checked"]


def test_rule_book_and_statue_dialogue_do_not_freeze_trial(game):
    trial = enter_trial(game)
    game.rule_book.is_open = True
    game.update(4)
    assert trial.remaining == 56
    game.rule_book.close()
    game.event_bus.emit("show_dialog", speaker_id="toad_statue", lines=["石像渗血。"])
    game.update(3)
    assert trial.remaining == 53


def test_active_trial_exit_cannot_reset_clock(game):
    trial = enter_trial(game)
    trial.remaining = 10
    game.player.rect.center = game.repair_hall.exit_zone.center
    game.player.position.xy = game.player.rect.topleft
    game.input_manager._pressed_once.add("interact")
    game.update(.1)
    assert game.mode == game.MODE_REPAIR
    assert trial.remaining == 9.9


def test_keyboard_selection_mouse_rotation_and_submit(game):
    trial = enter_trial(game)

    def at(zone):
        game.player.rect.midbottom = (zone.centerx, zone.centery)
        game.player.position.xy = game.player.rect.topleft

    def press(key):
        game.input_manager.begin_frame()
        game.input_manager.process_event(pygame.event.Event(pygame.KEYDOWN, key=key))
        game.update(.016)

    def display_point(game_point):
        target = game._scaled_game_rect(game.display_surface.get_size())
        return (
            target.x + round(game_point[0] * target.width / 480),
            target.y + round(game_point[1] * target.height / 270),
        )

    def drag_fragment(dx, dy):
        target = game._scaled_game_rect(game.display_surface.get_size())
        start = display_point(game.repair_hall.INSPECTION_DRAG_ZONE.center)
        rel = (
            round(dx * target.width / 480),
            round(dy * target.height / 270),
        )
        end = (start[0] + rel[0], start[1] + rel[1])
        game.input_manager.begin_frame()
        game.input_manager.process_event(
            pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=start)
        )
        game.update(.016)
        game.input_manager.begin_frame()
        game.input_manager.process_event(
            pygame.event.Event(pygame.MOUSEMOTION, pos=end, rel=rel, buttons=(1, 0, 0))
        )
        game.update(.016)
        game.input_manager.begin_frame()
        game.input_manager.process_event(
            pygame.event.Event(pygame.MOUSEBUTTONUP, button=1, pos=end)
        )
        game.update(.016)

    at(game.repair_hall.table_zone)
    press(pygame.K_e)
    for _ in range(game.repair_hall.cracked_slot):
        press(pygame.K_d)
    press(pygame.K_e)
    assert trial.selected == 2
    at(game.repair_hall.light_zone)
    press(pygame.K_e)
    orientation = (trial.yaw, trial.pitch)
    press(pygame.K_q)
    press(pygame.K_d)
    assert (trial.yaw, trial.pitch) == orientation
    drag_fragment(
        trial.LIGHT_YAW / trial.DRAG_DEGREES_PER_PIXEL,
        trial.LIGHT_PITCH / trial.DRAG_DEGREES_PER_PIXEL,
    )
    assert trial.inspecting and not trial.back and trial.resonating
    assert trial.crack_revealed
    press(pygame.K_e)
    at(game.repair_hall.tray_zone)
    press(pygame.K_e)
    assert trial.phase == "sealing"


def test_correct_piece_without_crack_observation_is_failure_at_open_door(game):
    solve_lamp(game)
    opened_save = deepcopy(game.save_manager.load(1))
    trial = enter_trial(game)
    trial.pick_up(2)
    game._submit_repair_piece()
    assert trial.phase == "death"
    assert trial.death_reason == "未验"
    game.update(2.5)
    assert game.mode == game.MODE_PLAYING
    assert game.repair_door.unlocked
    assert game.mainline["repair_door_open"]
    assert game.player.rect.topleft == (opened_save["player"]["x"], opened_save["player"]["y"])


def test_all_repair_targets_are_reachable_with_player_footprint(game):
    from collections import deque
    hall = game.repair_hall
    start = hall.SPAWN
    points = deque([start])
    visited = {start}
    reached = set()
    targets = {name: getattr(hall, name + "_zone") for name in ("table", "tray", "statue", "light", "exit")}
    while points:
        x, y = points.popleft()
        footprint = pygame.Rect(x - 8, y - 10, 16, 10)
        for name, zone in targets.items():
            if footprint.colliderect(zone):
                reached.add(name)
        for dx, dy in ((8,0),(-8,0),(0,8),(0,-8)):
            nxt = (x+dx, y+dy)
            rect = footprint.move(dx, dy)
            if nxt not in visited and pygame.Rect(0,0,*hall.SIZE).contains(rect) and not any(rect.colliderect(wall) for wall in hall.collisions()):
                visited.add(nxt)
                points.append(nxt)
    assert reached == set(targets)


def test_flat_legacy_report_is_migrated_before_repair_prerequisite(game):
    payload = game.save_manager.default_save(1)
    payload["mainline"] = {"wugang_checked": True, "yutu_checked": True}
    payload.update(scene="guanghan", report_completed=True, opening_seen=True, home_tutorial_done=True)
    game._apply_save_data(payload)
    assert game.mainline["repair_checked"]
    assert game.current_save_data["scene"] == "guanghan"


def test_completed_tasks_advance_checkpoint_once_in_played_order(game):
    game._complete_yutu_check(False)
    game._complete_wugang_check(False)
    trial = enter_trial(game)
    trial.pick_up(2)
    reveal_crack(trial)
    game._submit_repair_piece()
    game.update(6)
    saved = deepcopy(game.save_manager.load(1))
    assert saved["checkpoint_events"] == ["yutu_completed", "wugang_completed", "repair_completed"]
    game._complete_yutu_check(False)
    assert game.save_manager.load(1) == saved


def test_courtyard_repair_door_reachable_by_real_movement_and_key(game, monkeypatch):
    from collections import defaultdict
    held = defaultdict(bool)
    monkeypatch.setattr(pygame.key, "get_pressed", lambda: held)
    game.player.rect.midbottom = (210, 236)
    game.player.position.xy = game.player.rect.topleft
    for key, frames in ((pygame.K_LEFT, 100), (pygame.K_DOWN, 30)):
        held[key] = True
        game.input_manager.process_event(pygame.event.Event(pygame.KEYDOWN, key=key))
        for _ in range(frames):
            game.update(1 / 60)
        held.clear()
        game.input_manager.process_event(pygame.event.Event(pygame.KEYUP, key=key))
    assert game.repair_door.LEFT_ZONE.colliderect(game.player.rect)
    game.input_manager.process_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_e))
    game.update(1 / 60)
    assert game.mode == game.MODE_PLAYING
    assert game.repair_door.active


def lamp_key(game, key, dt=1 / 60):
    game.input_manager.begin_frame()
    game.input_manager.process_event(pygame.event.Event(pygame.KEYDOWN, key=key))
    game.update(dt)
    game.input_manager.begin_frame()


def open_lamp(game):
    game.player.rect.midbottom = game.repair_door.LEFT_ZONE.center
    game.player.position.xy = game.player.rect.topleft
    # This helper places the player directly inside the zone instead of
    # walking there. Seed the enter-zone state so the test does not invent a
    # Laurel violation that normal movement would already have recorded.
    game.tree_bow_zone.update(0.0, game.player.rect)
    lamp_key(game, pygame.K_e)
    assert game.mode == game.MODE_PLAYING
    assert game.repair_door.active


def test_active_lamp_stays_in_courtyard_and_draws_before_laurel_tree(game, monkeypatch):
    open_lamp(game)
    draw_order = []
    door_draw = game.repair_door.draw_world
    tree_draw = game.laurel_tree.draw

    def record_door(*args, **kwargs):
        draw_order.append("door")
        return door_draw(*args, **kwargs)

    def record_tree(*args, **kwargs):
        draw_order.append("tree")
        return tree_draw(*args, **kwargs)

    monkeypatch.setattr(game.repair_door, "draw_world", record_door)
    monkeypatch.setattr(game.laurel_tree, "draw", record_tree)
    game._draw_playing()

    assert game.mode == game.MODE_PLAYING
    assert draw_order.index("door") < draw_order.index("tree")
    assert hasattr(game.repair_door, "draw_active_hint")


def solve_lamp(game):
    open_lamp(game)
    # The existing rule only permits inspection during Laurel's anomaly.
    game.laurel_tree.set_bleeding(True)
    for _ in range(3):
        lamp_key(game, pygame.K_a)
    game.update(.75)
    game.update(1.5)
    game.update(1.5)


def test_lamp_wrong_angle_has_no_penalty_timer_or_checkpoint(game):
    before = deepcopy(game.save_manager.load(1))
    open_lamp(game)
    game.update(70)
    assert not game.repair_door.unlocked
    assert game.game_state.violation_count == 0
    assert game.repair_hall.trial.phase == "idle"
    assert game.repair_hall.trial.remaining == 60
    assert game.save_manager.load(1) == before


def test_lamp_alignment_waits_for_laurel_anomaly(game):
    open_lamp(game)
    for _ in range(3):
        lamp_key(game, pygame.K_a)
    game.update(1.0)
    assert game.repair_door.toads_aligned
    assert game.repair_door.phase == "closed"
    assert game.repair_door.waiting_for_anomaly

    game.laurel_tree.set_bleeding(True)
    game.update(game.repair_door.ALIGN_SECONDS)
    assert game.repair_door.phase == "opening"
    game.update(game.repair_door.OPEN_SECONDS)
    assert game.repair_door.unlocked


def test_active_lamp_keeps_courtyard_movement_and_tree_rule_live(game, monkeypatch):
    from collections import defaultdict

    open_lamp(game)
    game.player.rect.midbottom = (360, 360)
    game.player.position.xy = game.player.rect.topleft
    start_y = game.player.rect.y
    held = defaultdict(bool)
    monkeypatch.setattr(pygame.key, "get_pressed", lambda: held)
    held[pygame.K_w] = True
    for _ in range(30):
        game.update(1 / 60)
    held.clear()

    assert game.repair_door.active
    assert game.player.rect.y < start_y

    # Re-entering the existing forbidden circle while the live mechanism is
    # open still records the ordinary tree violation.
    game.laurel_tree.set_bleeding(False)
    game.tree_bow_zone.reset()
    game.player.rect.midbottom = game.repair_door.LEFT_ZONE.center
    game.player.position.xy = game.player.rect.topleft
    game.update(0.0)
    assert game.game_state.violation_count == 1


def test_leaving_left_toad_stops_lamp_alignment_until_return(game):
    open_lamp(game)
    game.laurel_tree.set_bleeding(True)
    game.repair_door.angle = game.repair_door.reference_angle
    game.player.rect.x += 100
    game.player.position.xy = game.player.rect.topleft
    game.update(game.repair_door.ALIGN_SECONDS + 0.1)
    assert game.repair_door.phase == "closed"
    assert game.repair_door.alignment == 0.0

    game.player.rect.x -= 100
    game.player.position.xy = game.player.rect.topleft
    game.update(game.repair_door.ALIGN_SECONDS)
    assert game.repair_door.phase == "opening"


def test_lamp_alignment_opens_and_persists_door_state_and_position(game):
    before = deepcopy(game.save_manager.load(1))
    solve_lamp(game)
    assert game.repair_door.unlocked
    assert game.mainline["repair_door_open"]
    saved = game.save_manager.load(1)
    assert saved != before
    assert saved["scene"] == game.MODE_PLAYING
    assert saved["mainline"]["repair_door_open"]
    assert saved["player"]["x"] == game.player.rect.x
    assert saved["player"]["y"] == game.player.rect.y
    angle = game.repair_door.angle
    lamp_key(game, pygame.K_d)
    assert game.repair_door.angle == angle
    assert game.save_manager.load(1) == saved
    lamp_key(game, pygame.K_e)
    assert game.mode == game.MODE_REPAIR
    assert game.repair_hall.trial.phase == "idle"
    assert game.repair_hall.trial.remaining == 60


def test_lamp_escape_only_closes_examination(game):
    open_lamp(game)
    lamp_key(game, pygame.K_ESCAPE)
    assert game.mode == game.MODE_PLAYING
    assert not game.repair_door.active
    assert not game.repair_door.unlocked


def test_lamp_open_state_follows_existing_task_checkpoints(game):
    solve_lamp(game)
    lamp_key(game, pygame.K_ESCAPE)
    game._complete_yutu_check(False)
    game._reset_after_death()
    assert game.repair_door.unlocked
    assert not game.repair_door.active
    assert game.current_save_data["checkpoint_id"] == "yutu_completed"


def test_lamp_only_progress_is_rolled_back_on_death(game):
    solve_lamp(game)
    game._reset_after_death()
    assert game.repair_door.unlocked
    assert not game.repair_door.active
    assert game.mainline["repair_door_open"]
    assert game.mode == game.MODE_PLAYING


def test_completed_repair_saves_the_courtyard_exit_position(game):
    trial = enter_trial(game)
    trial.pick_up(2)
    reveal_crack(trial)
    game._submit_repair_piece()
    game.update(6.0)
    assert game.repair_hall.trial.phase == "complete"
    assert game.save_manager.load(1)["scene"] == game.MODE_REPAIR

    game.player.rect.center = game.repair_hall.exit_zone.center
    game.player.position.xy = game.player.rect.topleft
    lamp_key(game, pygame.K_e)

    saved = game.save_manager.load(1)
    assert game.mode == game.MODE_PLAYING
    assert saved["scene"] == game.MODE_PLAYING
    assert saved["mainline"]["repair_checked"]
    assert saved["mainline"]["repair_door_open"]
    assert saved["checkpoint_id"] == "repair_completed"
    assert saved["player"]["x"] == game.player.rect.x
    assert saved["player"]["y"] == game.player.rect.y


def test_completed_repair_legacy_save_keeps_door_open(game):
    payload = deepcopy(game.current_save_data)
    payload["mainline"].pop("repair_door_open", None)
    payload["mainline"]["repair_checked"] = True
    game._apply_save_data(payload)
    assert game.repair_door.unlocked


def test_right_toad_cannot_be_interacted_with(game):
    game.player.rect.midbottom = game.repair_door.RIGHT_ZONE.center
    game.player.position.xy = game.player.rect.topleft
    before = deepcopy(game.save_manager.load(1))
    lamp_key(game, pygame.K_e)
    assert not game.repair_door.active
    assert not game.dialog_box.active
    assert game.repair_door.reference_angle == 0
    assert game.save_manager.load(1) == before


def test_closed_door_points_to_statues_instead_of_rotating_lamp(game):
    game.player.rect.midbottom = game.repair_hall.COURTYARD_RETURN
    game.player.position.xy = game.player.rect.topleft
    lamp_key(game, pygame.K_e)
    assert not game.repair_door.active
    assert game.mode == game.MODE_PLAYING


def test_matching_toads_start_door_opening_and_success_light_is_red(game):
    open_lamp(game)
    game.laurel_tree.set_bleeding(True)
    reference = game.repair_door.reference_angle
    for _ in range(3):
        lamp_key(game, pygame.K_a)
    game.update(.75)
    door = game.repair_door
    assert door.phase == "opening"
    assert door.frame_index == 0
    assert not door.unlocked
    angle = door.angle
    lamp_key(game, pygame.K_d, .9)
    assert door.angle == angle
    assert door.reference_angle == reference
    game.update(.6)
    assert door.phase == "open"
    assert door.light_color[0] > door.light_color[1] * 2
    assert door.unlocked
    assert door.light_color[0] > door.light_color[2] * 2
