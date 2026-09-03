"""Game audio event tests."""

from pathlib import Path
import wave
import struct
import os

import pytest

os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
import pygame

from core.audio import (
    AUDIO_FILES,
    BGM_FILES,
    CG_AUDIO_KEYS,
    AudioManager,
    select_bgm_for_state,
)
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
        if path.suffix.lower() != ".wav":
            continue
        with wave.open(str(path), "rb") as wav:
            frames = wav.readframes(wav.getnframes())
        samples = struct.unpack(f"<{len(frames) // 2}h", frames)
        peak = max(abs(sample) for sample in samples) / 32767

        assert peak < 0.72


def test_selected_scene_bgms_are_mp3_and_decodable_by_pygame():
    expected_min_lengths = {
        "home": 120.0,
        "guanghan_square": 50.0,
        "guanghan_palace": 590.0,
    }
    mixer_was_initialized = pygame.mixer.get_init()
    if mixer_was_initialized:
        pygame.mixer.quit()
    try:
        pygame.mixer.init()
    except pygame.error as exc:
        pytest.skip(f"audio mixer unavailable: {exc}")

    try:
        for key, minimum_length in expected_min_lengths.items():
            path = asset_path(BGM_FILES[key])
            assert path.suffix.lower() == ".mp3"
            sound = pygame.mixer.Sound(str(path))
            assert sound.get_length() >= minimum_length
    finally:
        pygame.mixer.quit()


def test_selected_ending_bgms_are_decodable_and_cover_the_full_cg():
    expected_min_lengths = {
        "ending_he": 8.0,
        "ending_be": 8.0,
    }
    mixer_was_initialized = pygame.mixer.get_init()
    if mixer_was_initialized:
        pygame.mixer.quit()
    try:
        pygame.mixer.init()
    except pygame.error as exc:
        pytest.skip(f"audio mixer unavailable: {exc}")

    try:
        for key, minimum_length in expected_min_lengths.items():
            path = asset_path(BGM_FILES[key])
            assert path.suffix.lower() in {".mp3", ".ogg"}
            sound = pygame.mixer.Sound(str(path))
            assert sound.get_length() >= minimum_length
    finally:
        pygame.mixer.quit()


def test_main_menu_bgm_is_the_approved_72_second_stereo_loop():
    path = asset_path(BGM_FILES["main_menu"])
    with wave.open(str(path), "rb") as wav:
        channels = wav.getnchannels()
        sample_rate = wav.getframerate()
        frame_count = wav.getnframes()
        frames = wav.readframes(frame_count)

    assert channels == 2
    assert sample_rate == 44_100
    assert frame_count == sample_rate * 72
    samples = struct.unpack(f"<{len(frames) // 2}h", frames)
    for channel in range(channels):
        first = samples[channel]
        last = samples[-channels + channel]
        assert abs(first - last) / 32767 < 0.01


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


def test_audio_manager_cg_cues_are_once_per_token_and_stop_as_a_group():
    FakeSound.played = []
    FakeSound.stopped = []
    audio = AudioManager(EventBus(), mixer=FakeMixer())

    audio.begin_cg_cycle()
    audio.play_cg_cue("cg_wugang_axe", token="report:4.8")
    audio.play_cg_cue("cg_wugang_axe", token="report:4.8")

    assert FakeSound.played.count("cg_wugang_axe.wav") == 1
    audio.stop_cg_sounds()
    assert "cg_wugang_axe.wav" in FakeSound.stopped
    assert set(audio._cg_played_tokens) == set()


def test_audio_manager_declares_all_cg_cues_in_the_same_audio_registry():
    assert set(CG_AUDIO_KEYS).issubset(AUDIO_FILES)


def test_real_game_states_select_menu_and_scene_bgms():
    assert select_bgm_for_state("main_menu", {}) == "main_menu"
    assert select_bgm_for_state("save_menu", {}) == "main_menu"
    assert select_bgm_for_state("home", {}) == "home"
    assert select_bgm_for_state("playing", {}) == "guanghan_square"
    assert select_bgm_for_state("guanghan", {}) == "guanghan_palace"
    assert select_bgm_for_state("playing", {"wugang_polluted": True}) == "guanghan_square"
    assert select_bgm_for_state("guanghan", {"yutu_polluted": True}) == "guanghan_palace"
    assert select_bgm_for_state("playing", {"pending_pool_ending": "be_yutu"}) == "guanghan_square"
    assert select_bgm_for_state(
        "guanghan", {"handoff_completed": True, "return_countdown_active": True}
    ) == "ending_be"
    assert select_bgm_for_state(
        "playing", {"handoff_completed": True, "pending_pool_ending": "be_yutu"}
    ) == "ending_be"
    assert select_bgm_for_state(
        "home", {"handoff_completed": True, "return_departed_on_time": True}
    ) == "ending_he"
    assert select_bgm_for_state("ending_cg", {"ending": "he_return_earth"}) == "ending_he"
    assert select_bgm_for_state("ending_cg", {"ending": "be_yutu"}) == "ending_be"


def test_main_menu_bgm_continues_through_save_menu_and_stops_for_opening_cg():
    FakeSound.played = []
    FakeSound.stopped = []
    audio = AudioManager(EventBus(), mixer=FakeMixer())

    audio.sync_for_game_state("main_menu", {})
    audio.update(AudioManager.BGM_FADE_SECONDS)
    assert audio.bgm_status()["active"] == "main_menu"
    assert FakeSound.played.count("bgm_main_menu.wav") == 1

    audio.sync_for_game_state("save_menu", {})
    audio.update(AudioManager.BGM_FADE_SECONDS)
    assert audio.bgm_status()["active"] == "main_menu"
    assert FakeSound.played.count("bgm_main_menu.wav") == 1

    audio.sync_for_game_state("opening_cg", {})
    assert audio.bgm_status()["transitioning"] is True
    audio.update(AudioManager.BGM_FADE_SECONDS)
    assert audio.bgm_status()["active"] is None
    assert FakeSound.stopped.count("bgm_main_menu.wav") == 1


def test_bgm_sync_does_not_restart_same_scene_track_and_fades_between_scenes():
    FakeSound.played = []
    FakeSound.stopped = []
    audio = AudioManager(EventBus(), mixer=FakeMixer())

    audio.sync_for_game_state("home", {})
    audio.sync_for_game_state("home", {})
    audio.update(AudioManager.BGM_FADE_SECONDS)
    assert FakeSound.played.count("bgm_home_dream_2_ambience.mp3") == 1
    assert audio.bgm_status()["target"] == "home"

    audio.sync_for_game_state("playing", {})
    audio.sync_for_game_state("playing", {})
    assert audio.bgm_status()["transitioning"] is True
    assert FakeSound.played.count("bgm_guanghan_square_the_surreal_truth.mp3") == 0

    audio.update(AudioManager.BGM_FADE_SECONDS)
    assert FakeSound.played.count("bgm_guanghan_square_the_surreal_truth.mp3") == 1
    assert FakeSound.stopped.index("bgm_home_dream_2_ambience.mp3") < len(FakeSound.played) - 1
    assert audio.bgm_status()["transitioning"] is True
    audio.update(AudioManager.BGM_FADE_SECONDS)
    status = audio.bgm_status()
    assert status["active"] == "guanghan_square"
    assert status["transitioning"] is False
    assert FakeSound.stopped.count("bgm_home_dream_2_ambience.mp3") == 1


def test_bgm_ducks_for_dialogue_and_cg_without_restarting():
    FakeSound.played = []
    audio = AudioManager(EventBus(), mixer=FakeMixer())
    audio.sync_for_game_state("home", {})
    audio.update(AudioManager.BGM_FADE_SECONDS)

    bus = audio.event_bus
    bus.emit(DIALOG_ACTIVE_CHANGED, active=True, speaker_id="change")
    assert audio.sounds["home"].volume < AudioManager.VOLUMES["home"]
    played_before_cg = list(FakeSound.played)
    audio.begin_cg_cycle()
    assert FakeSound.played == played_before_cg
    assert audio.sounds["home"].volume < AudioManager.VOLUMES["home"]
    audio.stop_cg_sounds()
    bus.emit(DIALOG_ACTIVE_CHANGED, active=False, speaker_id="change")
    assert audio.sounds["home"].volume == AudioManager.VOLUMES["home"]


def test_missing_requested_bgm_stops_stale_route_safely():
    FakeSound.stopped = []
    audio = AudioManager(EventBus(), mixer=FakeMixer())
    audio.sync_for_game_state("home", {})
    audio.update(AudioManager.BGM_FADE_SECONDS)
    audio.sounds.pop("guanghan_square")

    audio.sync_for_game_state("playing", {})

    assert audio.bgm_status()["active"] is None
    assert "bgm_home_dream_2_ambience.mp3" in FakeSound.stopped
    assert audio.bgm_status()["target"] == "guanghan_square"


def test_bgm_sound_load_failure_is_nonfatal_and_clears_stale_scene_track():
    class MissingSquareBgmMixer(FakeMixer):
        def Sound(self, path):
            if Path(path).name == "bgm_guanghan_square_the_surreal_truth.mp3":
                raise FileNotFoundError(path)
            return FakeSound(path)

    audio = AudioManager(EventBus(), mixer=MissingSquareBgmMixer())
    audio.sync_for_game_state("home", {})
    audio.update(AudioManager.BGM_FADE_SECONDS)
    assert audio.bgm_status()["active"] == "home"

    audio.sync_for_game_state("playing", {})

    assert audio.bgm_status()["active"] is None
    assert audio.bgm_status()["target"] == "guanghan_square"


def test_build_script_collects_the_audio_directory_for_bgm_assets():
    build_text = Path("build.py").read_text(encoding="utf-8")
    assert 'for asset_group in ("audio", "sprites")' in build_text
    assert set(BGM_FILES).issubset(AUDIO_FILES)


def test_main_menu_bgm_provenance_records_the_cc0_source_and_output_hash():
    provenance = Path("assets/audio/BGM_SOURCES.md").read_text(encoding="utf-8")

    assert "https://opengameart.org/content/lost-in-a-bad-place-horror-ambience-loop" in provenance
    assert "CC0 1.0" in provenance
    assert "ad9a9f39240ef5862d3a6dc5220893926c6873aa0e08a641dadf3f1c0acc2cd4" in provenance
    assert "5aef2daebccf822f62d99584b6789ff88b89997ed7f0d0a9c4e66520f7492b49" in provenance


def test_selected_scene_bgm_provenance_records_the_user_choices():
    provenance = Path("assets/audio/BGM_SOURCES.md").read_text(encoding="utf-8")

    assert "Dream 2 Ambience" in provenance
    assert "The Surreal Truth" in provenance
    assert "Space ambient" in provenance
    assert "Somnium" in provenance
    assert "Insistent" in provenance
    assert "https://opengameart.org/content/dream-2-ambience" in provenance
    assert "https://opengameart.org/content/ambience-pack-1-sci-fi-horror" in provenance
    assert "https://opengameart.org/content/space-ambient" in provenance
    assert "https://opengameart.org/content/somnium" in provenance
    assert "https://opengameart.org/content/insistent-background-loop" in provenance
