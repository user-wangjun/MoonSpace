"""暂停、全局设置与显式保存进度的流程测试。"""

from __future__ import annotations

import os

os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

import config
from core.audio import AudioManager
from core.event_bus import EventBus, PLAYER_DIED, RULE_DISCOVERED, VIOLATION_CHANGED
from core.game import Game
from core.save_manager import SaveManager
from core.settings_manager import SettingsManager
from core.vibration import (
    VIBRATION_TRANSITION_FOUND,
    VIBRATION_VIOLATION,
    VibrationManager,
)
from effects.distortion import DistortionEffect
from ui.main_menu import MENU_SETTINGS
from ui.settings_menu import SettingsMenu


class KeyInput:
    def __init__(self, *, keys=(), actions=()):
        self.keys = set(keys)
        self.actions = set(actions)

    def was_pressed(self, action):
        return action in self.actions

    def was_key_pressed(self, key):
        return key in self.keys


class FakeSound:
    played: list[str] = []
    stopped: list[str] = []

    def __init__(self, path):
        self.path = str(path)
        self.volume = 0.0

    def set_volume(self, volume):
        self.volume = volume

    def play(self, *args, **kwargs):
        _ = args, kwargs
        self.played.append(os.path.basename(self.path))

    def stop(self):
        self.stopped.append(os.path.basename(self.path))


class FakeMixer:
    Sound = FakeSound

    def __init__(self):
        self.initialized = False

    def get_init(self):
        return self.initialized

    def init(self):
        self.initialized = True


class FakeJoystick:
    def __init__(self):
        self.rumbles = []
        self.stopped = 0

    def rumble(self, low_frequency, high_frequency, duration):
        self.rumbles.append((low_frequency, high_frequency, duration))
        return True

    def stop_rumble(self):
        self.stopped += 1


def make_game(tmp_path):
    game = Game()
    manager = SaveManager(tmp_path)
    game.save_manager = manager
    game.save_menu.save_manager = manager
    game.current_slot_id = 1
    data = manager.default_save(1)
    data.update({"opening_seen": True, "home_tutorial_done": True, "scene": Game.MODE_PLAYING})
    data["mainline"]["wugang_checked"] = True
    game.current_save_data = data
    game._apply_save_data(data)
    game.mode = game.MODE_PLAYING
    game.overlay_audio_mode = game.MODE_PLAYING
    game.pause_return_mode = game.MODE_PLAYING
    return game, manager


def test_settings_manager_is_global_and_survives_reload(tmp_path):
    path = tmp_path / "settings.json"
    manager = SettingsManager(path)

    manager.set_volume("bgm_volume", 0.4)
    manager.set_volume("sfx_volume", 0.7)

    reloaded = SettingsManager(path)

    assert reloaded.values == {
        "bgm_volume": 0.4,
        "sfx_volume": 0.7,
        "vibration_enabled": True,
    }
    assert not (tmp_path / "slot_1.json").exists()


def test_settings_menu_applies_bgm_sfx_and_mute_immediately(tmp_path):
    manager = SettingsManager(tmp_path / "settings.json")
    manager.set_volumes(bgm_volume=0.4, sfx_volume=0.7)
    FakeSound.played = []
    FakeSound.stopped = []
    audio = AudioManager(EventBus(), mixer=FakeMixer())
    menu = SettingsMenu(manager, audio)
    menu.open()

    menu.update(0.0, KeyInput(keys=(pygame.K_RIGHT,)))
    menu.selected_index = 1
    menu.update(0.0, KeyInput(keys=(pygame.K_LEFT,)))

    assert manager.values == {
        "bgm_volume": 0.5,
        "sfx_volume": 0.6,
        "vibration_enabled": True,
    }
    assert audio.volume_status() == {"bgm_volume": 0.5, "sfx_volume": 0.6}
    assert FakeSound.played == []
    assert FakeSound.stopped == []

    menu.selected_index = 3
    menu.update(0.0, KeyInput(keys=(pygame.K_RETURN,)))
    assert manager.values == {
        "bgm_volume": 0.0,
        "sfx_volume": 0.0,
        "vibration_enabled": True,
    }
    menu.selected_index = 4
    menu.update(0.0, KeyInput(keys=(pygame.K_RETURN,)))
    assert manager.values == {
        "bgm_volume": 1.0,
        "sfx_volume": 1.0,
        "vibration_enabled": True,
    }


def test_settings_menu_toggles_vibration_and_persists_it(tmp_path):
    manager = SettingsManager(tmp_path / "settings.json")
    joystick = FakeJoystick()
    vibration = VibrationManager(enabled=True, joysticks=[joystick])
    distortion = DistortionEffect(EventBus())
    distortion.start_shake(4.0, 0.2)
    menu = SettingsMenu(
        manager,
        AudioManager(EventBus(), mixer=FakeMixer()),
        vibration,
        distortion,
    )
    menu.open()

    menu.selected_index = 2
    menu.update(0.0, KeyInput(keys=(pygame.K_RETURN,)))

    assert manager.values["vibration_enabled"] is False
    assert vibration.enabled is False
    assert joystick.stopped == 1
    assert distortion.shake_enabled is False
    assert distortion.shake_timer == 0.0

    reloaded = SettingsManager(tmp_path / "settings.json")
    assert reloaded.values["vibration_enabled"] is False


def test_vibration_setting_persists_and_event_patterns_are_optional(tmp_path):
    manager = SettingsManager(tmp_path / "settings.json")
    joystick = FakeJoystick()
    bus = EventBus()
    vibration = VibrationManager(bus, enabled=True, joysticks=[joystick])

    bus.emit(RULE_DISCOVERED, rule_id="rule")
    bus.emit(VIOLATION_CHANGED, count=1)
    bus.emit(PLAYER_DIED, count=3)
    vibration.trigger(VIBRATION_TRANSITION_FOUND)

    assert len(joystick.rumbles) == 4
    assert vibration.last_event == VIBRATION_TRANSITION_FOUND

    manager.set_vibration_enabled(False)
    vibration.set_enabled(manager.values["vibration_enabled"])
    vibration.trigger(VIBRATION_VIOLATION)
    assert len(joystick.rumbles) == 4
    assert joystick.stopped == 1

    reloaded = SettingsManager(tmp_path / "settings.json")
    assert reloaded.values["vibration_enabled"] is False


def test_scene_transition_found_uses_the_same_optional_vibration_gate(tmp_path):
    game, _manager = make_game(tmp_path)
    calls = []
    game.audio.play_transition_found = lambda: calls.append("audio")
    game.vibration.trigger = lambda event: calls.append(event)

    game._play_transition_found()

    assert calls == ["audio", VIBRATION_TRANSITION_FOUND]
    assert game.distortion.shake_timer > 0.0


def test_audio_volume_multipliers_change_current_levels_without_restart():
    FakeSound.played = []
    FakeSound.stopped = []
    audio = AudioManager(EventBus(), mixer=FakeMixer())
    audio.sync_for_game_state("playing", {})
    audio.update(AudioManager.BGM_FADE_SECONDS)
    before = list(FakeSound.played)

    audio.set_volume_preferences(bgm_volume=0.4, sfx_volume=0.6)
    audio.play("dialog_open")

    assert AudioManager.DEFAULT_BGM_BASE_VOLUME == 0.23
    assert audio.sounds["guanghan_square"].volume == 0.23 * 0.4
    assert audio.sounds["dialog_open"].volume == AudioManager.VOLUMES["dialog_open"] * 0.6
    assert FakeSound.played[: len(before)] == before
    assert FakeSound.played[-1] == "dialog_open.wav"
    assert FakeSound.stopped == []


def test_game_main_menu_settings_opens_and_esc_returns(tmp_path):
    game, _manager = make_game(tmp_path)
    settings = SettingsManager(tmp_path / "settings.json")
    game.settings_manager = settings
    game.settings_menu = SettingsMenu(settings, game.audio)
    game.mode = game.MODE_MAIN_MENU

    game._handle_main_menu_action(MENU_SETTINGS)
    assert game.mode == game.MODE_SETTINGS
    assert game.settings_return_mode == game.MODE_MAIN_MENU

    game.input_manager._pressed_once.add(config.ACTION_QUIT)
    game.update(0.016)

    assert game.mode == game.MODE_MAIN_MENU


def test_escape_pauses_all_playable_logic_without_autosave(tmp_path):
    game, manager = make_game(tmp_path)
    game.mainline["return_countdown_active"] = True
    game.mainline["return_countdown_remaining"] = 12.0
    game.wugang._timer = 0.75
    game.yutu._timer = 0.22
    player_position = game.player.rect.topleft
    game.input_manager._pressed_once.add(config.ACTION_QUIT)

    game._update_playing(2.0)

    assert game.mode == game.MODE_PAUSE
    assert game.player.rect.topleft == player_position
    assert game.wugang._timer == 0.75
    assert game.yutu._timer == 0.22
    assert game.mainline["return_countdown_remaining"] == 12.0
    assert manager.load(1) is None


def test_pause_continue_returns_to_the_original_playable_scene(tmp_path):
    game, _manager = make_game(tmp_path)
    game.mode = game.MODE_PAUSE
    game.pause_return_mode = game.MODE_GUANGHAN
    game.pause_menu.open()
    game.input_manager._keys_pressed_once.add(pygame.K_RETURN)

    game._update_pause(0.5)

    assert game.mode == game.MODE_GUANGHAN


def test_pause_and_settings_keep_one_bgm_instance_without_stop(tmp_path):
    game, _manager = make_game(tmp_path)
    FakeSound.played = []
    FakeSound.stopped = []
    audio = AudioManager(game.event_bus, mixer=FakeMixer())
    game.audio = audio
    game.settings_menu.audio = audio
    audio.sync_for_game_state("playing", {})
    audio.update(AudioManager.BGM_FADE_SECONDS)
    before = list(FakeSound.played)
    active = audio.bgm_status()["active"]

    game.input_manager._pressed_once.add(config.ACTION_QUIT)
    game._update_playing(0.016)
    game.input_manager._pressed_once.clear()
    game.update(1.0)
    assert game.mode == game.MODE_PAUSE
    assert audio.bgm_status()["active"] == active
    assert FakeSound.played == before
    assert FakeSound.stopped == []

    game.pause_menu.selected_index = 3
    game.input_manager._pressed_once.clear()
    game.input_manager._keys_pressed_once.add(pygame.K_RETURN)
    game._update_pause(0.016)
    assert game.mode == game.MODE_SETTINGS
    game.input_manager._keys_pressed_once.clear()
    game.update(1.0)

    assert audio.bgm_status()["active"] == active
    assert FakeSound.played == before
    assert FakeSound.stopped == []

    game.input_manager._pressed_once.add(config.ACTION_QUIT)
    game.update(0.016)
    assert game.mode == game.MODE_PAUSE
    assert audio.bgm_status()["active"] == active


def test_pause_save_copies_latest_checkpoint_to_selected_slot_not_new_game(tmp_path):
    game, manager = make_game(tmp_path)
    game.player.rect.topleft = (222, 333)
    game.player.position.xy = game.player.rect.topleft
    game.mode = game.MODE_PAUSE
    game.pause_return_mode = game.MODE_PLAYING
    game.overlay_audio_mode = game.MODE_PLAYING
    game.pause_menu.selected_index = 1
    game.input_manager._keys_pressed_once.add(pygame.K_RETURN)

    game.update(0.016)
    assert game.mode == game.MODE_SAVE_MENU
    assert game.pending_save_mode == "save"

    game.input_manager._keys_pressed_once.clear()
    game.input_manager._keys_pressed_once.add(pygame.K_2)
    game.update(0.016)
    saved = manager.load(2)

    assert game.mode == game.MODE_SAVE_MENU
    assert game.current_slot_id == 2
    assert saved["scene"] == game.MODE_PLAYING
    assert saved["player"] == {"x": config.PLAYER_START_X, "y": config.PLAYER_START_Y, "facing": "down"}
    assert saved["mainline"]["wugang_checked"] is True
    assert saved["opening_seen"] is True
    assert not game.opening_cg.active


def test_pause_load_escape_returns_without_overwriting_current_state(tmp_path):
    game, manager = make_game(tmp_path)
    original_position = game.player.rect.topleft
    game.mode = game.MODE_PAUSE
    game.pause_return_mode = game.MODE_PLAYING
    game.overlay_audio_mode = game.MODE_PLAYING
    game._open_save_menu_from_pause("load")
    game.input_manager._pressed_once.add(config.ACTION_QUIT)

    game.update(0.016)

    assert game.mode == game.MODE_PAUSE
    assert game.current_slot_id == 1
    assert game.player.rect.topleft == original_position
    assert manager.load(1) is None


def test_pause_return_to_main_menu_retains_checkpoint_without_overwriting(tmp_path):
    game, manager = make_game(tmp_path)
    game._save_checkpoint("task_done")
    previous = manager.load(1)
    game.player.rect.x += 30
    game.mode = game.MODE_PAUSE
    game.pause_return_mode = game.MODE_PLAYING
    game.overlay_audio_mode = game.MODE_PLAYING
    game.pause_menu.selected_index = 4
    game.input_manager._keys_pressed_once.add(pygame.K_RETURN)

    game.update(0.016)
    saved = manager.load(1)

    assert game.mode == game.MODE_MAIN_MENU
    assert saved["scene"] == game.MODE_PLAYING
    assert saved["slot_id"] == 1
    assert (tmp_path / "slot_1.json").exists()
    assert saved == previous
