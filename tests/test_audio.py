"""Game audio event tests."""

from pathlib import Path
import wave
import struct

import pygame

from core.audio import AUDIO_FILES, AudioManager
from core.event_bus import (
    DIALOG_ACTIVE_CHANGED,
    EventBus,
    PLAYER_DIED,
    RULE_DISCOVERED,
    TREE_BLEEDING,
    VIOLATION_CHANGED,
)
from utils.assets import asset_path


class FakeSound:
    played: list[str] = []
    stopped: list[str] = []

    def __init__(self, path):
        self.path = str(path)

    def set_volume(self, volume):
        self.volume = volume

    def play(self, *args, **kwargs):
        _ = args, kwargs
        self.played.append(Path(self.path).name)

    def stop(self):
        self.stopped.append(Path(self.path).name)


class FakeMixer:
    Sound = FakeSound

    def __init__(self):
        self.initialized = False

    def get_init(self):
        return self.initialized

    def init(self):
        self.initialized = True


def test_audio_assets_exist_and_are_non_empty():
    for relative_path in AUDIO_FILES.values():
        path = asset_path(relative_path)

        assert path.exists()
        assert path.stat().st_size > 512


def test_audio_assets_are_quiet_enough_for_background_horror():
    for relative_path in AUDIO_FILES.values():
        path = asset_path(relative_path)
        with wave.open(str(path), "rb") as wav:
            frames = wav.readframes(wav.getnframes())
        samples = struct.unpack(f"<{len(frames) // 2}h", frames)
        peak = max(abs(sample) for sample in samples) / 32767

        assert peak < 0.72


def test_audio_manager_subscribes_to_game_events():
    FakeSound.played = []
    bus = EventBus()
    mixer = FakeMixer()

    AudioManager(bus, mixer=mixer)
    bus.emit(RULE_DISCOVERED, rule_id="rule", rule_text="text")
    bus.emit(VIOLATION_CHANGED, count=1, rule_id="rule")
    bus.emit(TREE_BLEEDING, source="wugang")
    bus.emit(DIALOG_ACTIVE_CHANGED, active=True, speaker_id="sign_board")
    bus.emit(PLAYER_DIED, count=3, rule_id="rule")

    assert "rule_discovered.wav" in FakeSound.played
    assert "violation.wav" in FakeSound.played
    assert "tree_bleeding.wav" in FakeSound.played
    assert "dialog_open.wav" in FakeSound.played
    assert "player_died.wav" in FakeSound.played


def test_audio_manager_can_play_transition_found_sting():
    FakeSound.played = []
    bus = EventBus()
    mixer = FakeMixer()
    audio = AudioManager(bus, mixer=mixer)

    audio.play_transition_found()

    assert FakeSound.played[-1] == "transition_found.wav"


def test_audio_manager_can_stop_and_restart_ambient_loop():
    FakeSound.played = []
    FakeSound.stopped = []
    audio = AudioManager(EventBus(), mixer=FakeMixer())

    audio.play_ambient()
    audio.stop_ambient()
    audio.play_ambient()

    assert FakeSound.played.count("ambient_moon_palace.wav") == 2
    assert FakeSound.stopped == ["ambient_moon_palace.wav"]


def test_audio_manager_handles_mixer_init_failure_without_crashing():
    class FailingMixer(FakeMixer):
        def init(self):
            raise pygame.error("no device")

    bus = EventBus()
    audio = AudioManager(bus, mixer=FailingMixer())

    bus.emit(RULE_DISCOVERED, rule_id="rule", rule_text="text")
    bus.emit(VIOLATION_CHANGED, count=1, rule_id="rule")
    audio.play_transition_found()

    assert audio.enabled is False
