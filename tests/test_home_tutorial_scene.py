"""Home/tutorial 场景测试。"""

import pygame

import config
from core.event_bus import DIALOG_ACTIVE_CHANGED, EventBus, SHOW_DIALOG
from core.game_state import GameState
from core.demo_rules import RULE_NO_EYE_CONTACT
from utils import palette
from utils.assets import load_image
from world.home_tutorial_scene import HomeTutorialScene


def test_home_tutorial_starts_with_locked_gate():
    scene = HomeTutorialScene(EventBus())
    player_rect = scene.gate_trigger_rect.copy()

    assert scene.sign_read is False
    assert scene.practice_done is True
    assert scene.gate_open is False
    assert scene.is_gate_entered(player_rect) is False


def test_home_tutorial_sign_adds_rules_and_shows_operation_dialog():
    bus = EventBus()
    state = GameState(bus)
    scene = HomeTutorialScene(bus)
    dialogs = []
    bus.subscribe(SHOW_DIALOG, lambda **payload: dialogs.append(payload))

    first_read = scene.read_sign(state)

    assert first_read is True
    assert scene.sign_read is True
    assert RULE_NO_EYE_CONTACT in state.known_rules
    assert dialogs
    assert any("不要让角色正面朝向" in line for line in dialogs[-1]["lines"])
    assert not any("没有安装完成" in line for line in dialogs[-1]["lines"])
    assert any("回到地球" in line for line in dialogs[-1]["lines"])
    assert any("六条规条" in line for line in dialogs[-1]["lines"])


def test_home_tutorial_sign_dialog_no_longer_requires_shadow_practice():
    scene = HomeTutorialScene(EventBus())
    text = "\n".join(scene.SIGN_DIALOG_LINES)

    assert "右侧影像" not in text
    assert "练习一次" not in text
    assert "月宫大门便会开启" in text


def test_home_tutorial_gate_opens_after_full_sign_dialog_closes():
    scene = HomeTutorialScene(EventBus())
    state = GameState(EventBus())

    scene.read_sign(state)
    assert scene.gate_open is False

    scene.event_bus.emit(DIALOG_ACTIVE_CHANGED, active=False, speaker_id="home_sign")
    assert scene.gate_open is True


def test_home_tutorial_sign_dialog_mentions_every_basic_rule_before_practice():
    scene = HomeTutorialScene(EventBus())
    text = "\n".join(scene.SIGN_DIALOG_LINES)

    for rule_text in scene.basic_rule_lines():
        assert rule_text in text


def test_home_tutorial_gate_opens_after_sign_without_practice():
    scene = HomeTutorialScene(EventBus())
    state = GameState(EventBus())
    player_rect = scene.gate_trigger_rect.copy()

    assert scene.is_gate_entered(player_rect) is False

    scene.read_sign(state)
    scene.event_bus.emit(DIALOG_ACTIVE_CHANGED, active=False, speaker_id="home_sign")
    assert scene.is_gate_entered(player_rect) is True


def test_home_tutorial_save_roundtrip_keeps_partial_progress():
    scene = HomeTutorialScene(EventBus())
    state = GameState(EventBus())
    scene.read_sign(state)
    scene.event_bus.emit(DIALOG_ACTIVE_CHANGED, active=False, speaker_id="home_sign")

    data = scene.collect_save_data()
    restored = HomeTutorialScene(EventBus())
    restored.apply_save_data(data)

    assert restored.sign_read is True
    assert restored.practice_done is True
    assert restored.rules_briefing_complete is True
    assert restored.gate_open is True


def test_home_tutorial_old_save_with_read_sign_keeps_briefing_complete():
    restored = HomeTutorialScene(EventBus())

    restored.apply_save_data({"sign_read": True, "practice_done": False})

    assert restored.sign_read is True
    assert restored.rules_briefing_complete is True
    assert restored.practice_done is True
    assert restored.gate_open is True


def test_home_tutorial_north_facade_blocks_roof_and_only_opens_gate_corridor():
    scene = HomeTutorialScene(EventBus())
    closed = scene.get_collision_rects()

    assert any(rect.collidepoint(480, 120) for rect in closed)
    assert any(rect.collidepoint(200, 120) for rect in closed)

    scene.sign_read = True
    scene.rules_briefing_complete = True
    opened = scene.get_collision_rects()

    assert not any(rect.collidepoint(scene.gate_trigger_rect.center) for rect in opened)
    assert any(rect.collidepoint(200, 120) for rect in opened)
    assert any(rect.collidepoint(480, 60) for rect in opened)


def test_home_tutorial_collision_rects_stay_inside_map():
    scene = HomeTutorialScene(EventBus())

    rects = scene.get_collision_rects()

    assert rects
    for rect in rects:
        assert isinstance(rect, pygame.Rect)
        assert rect.width > 0
        assert rect.height > 0
        assert rect.left >= 0
        assert rect.top >= 0
        assert rect.right <= config.MAP_WIDTH
        assert rect.bottom <= config.MAP_HEIGHT


def test_home_tutorial_props_block_statue_cliffs_and_lanterns():
    scene = HomeTutorialScene(EventBus())
    rects = scene.get_collision_rects()

    for point in (
        scene.rabbit_enclosure_rect.center,
        scene.left_cliff_rect.center,
        scene.right_cliff_rect.center,
        scene.left_lantern_rect.center,
        scene.right_lantern_rect.center,
    ):
        assert any(rect.collidepoint(point) for rect in rects)


def test_home_tutorial_draw_uses_preview_background_and_scene_markers():
    scene = HomeTutorialScene(EventBus())
    surface = pygame.Surface((config.MAP_WIDTH, config.MAP_HEIGHT), pygame.SRCALPHA)

    scene.draw(surface)

    colors = {
        surface.get_at((x, y))[:3]
        for x in range(0, config.MAP_WIDTH, 12)
        for y in range(0, config.MAP_HEIGHT, 12)
    }
    assert len(colors) > 200


def test_home_tutorial_background_asset_matches_large_map_size():
    background = load_image("sprites/moonspace/home_tutorial_bg.png")
    open_background = load_image("sprites/moonspace/home_tutorial_bg_open.png")

    assert background.get_size() == (config.MAP_WIDTH, config.MAP_HEIGHT)
    assert open_background.get_size() == (config.MAP_WIDTH, config.MAP_HEIGHT)


def test_home_tutorial_draw_switches_to_open_gate_art_after_briefing():
    scene = HomeTutorialScene(EventBus())
    closed = pygame.Surface((config.MAP_WIDTH, config.MAP_HEIGHT), pygame.SRCALPHA)
    opened = pygame.Surface((config.MAP_WIDTH, config.MAP_HEIGHT), pygame.SRCALPHA)

    scene.draw(closed)
    scene.sign_read = True
    scene.rules_briefing_complete = True
    scene.draw(opened)

    gate_sample = pygame.Rect(390, 70, 180, 100)
    assert closed.subsurface(gate_sample).copy().get_buffer().raw != opened.subsurface(gate_sample).copy().get_buffer().raw
