"""Game audio playback bound to event-bus signals."""

from __future__ import annotations

import math
from collections.abc import Mapping

import pygame

from core.event_bus import (
    DIALOG_ACTIVE_CHANGED,
    EventBus,
    PLAYER_DIED,
    RULE_DISCOVERED,
    TREE_BLEEDING,
    VIOLATION_CHANGED,
)
from utils.assets import asset_path


BGM_FILES = {
    "main_menu": "audio/bgm_main_menu.wav",
    "home": "audio/bgm_home_dream_2_ambience.mp3",
    "guanghan_square": "audio/bgm_guanghan_square_the_surreal_truth.mp3",
    "guanghan_palace": "audio/bgm_guanghan_palace_space_ambient.mp3",
    "ending_he": "audio/bgm_ending_he_somnium.mp3",
    "ending_be": "audio/bgm_ending_be_insistent.ogg",
}

MENU_MODES = ("main_menu", "save_menu")
PLAYABLE_MODES = ("home", "playing", "guanghan", "repair_hall")


def select_bgm_for_state(mode: str, mainline: dict | None = None) -> str | None:
    """Map the real game state to one BGM key without importing Game."""
    if mode in MENU_MODES:
        return "main_menu"
    if mode == "opening":
        return "home"

    mainline = mainline or {}
    if mode == "ending_cg":
        ending = mainline.get("ending", "")
        if ending == "he_return_earth":
            return "ending_he"
        if ending in ("be_wugang", "be_yutu", "be_double", "be_laurel_mixed", "be_change"):
            return "ending_be"
        return None

    if mode not in PLAYABLE_MODES:
        return None
    if mainline.get("ending"):
        return None

    # After Chang'e has completed the handoff, the player remains under the
    # same restrained BE/tension bed until leaving the moon palace.  A clean
    # route changes to the HE bed only after the player reaches Moon Valley.
    if mainline.get("handoff_completed") and mode in ("playing", "guanghan"):
        return "ending_be"
    if (
        mode == "home"
        and mainline.get("handoff_completed")
        and mainline.get("return_departed_on_time")
        and not mainline.get("wugang_polluted")
        and not mainline.get("yutu_polluted")
        and not mainline.get("pending_pool_ending")
    ):
        return "ending_he"

    return {
        "home": "home",
        "playing": "guanghan_square",
        "guanghan": "guanghan_palace",
        "repair_hall": "guanghan_square",
    }[mode]


AUDIO_FILES = {
    "rule_discovered": "audio/rule_discovered.wav",
    "violation": "audio/violation.wav",
    "player_died": "audio/player_died.wav",
    "tree_bleeding": "audio/tree_bleeding.wav",
    "dialog_open": "audio/dialog_open.wav",
    "transition_found": "audio/transition_found.wav",
    "ambient_moon_palace": "audio/ambient_moon_palace.wav",
    **BGM_FILES,
    # CG one-shots stay in this single audio layer so every sequence can stop
    # its temporary sounds on skip or scene change.
    "cg_download_start": "audio/cg_download_start.wav",
    "cg_download_complete": "audio/cg_download_complete.wav",
    "cg_blood_moon": "audio/cg_blood_moon.wav",
    "cg_screen_crack": "audio/cg_screen_crack.wav",
    "cg_palace_transition": "audio/cg_palace_transition.wav",
    "cg_wugang_axe": "audio/cg_wugang_axe.wav",
    "cg_yutu_pestle": "audio/cg_yutu_pestle.wav",
    "cg_moon_pool": "audio/cg_moon_pool.wav",
    "cg_laurel_roots": "audio/cg_laurel_roots.wav",
    "cg_earth_arrival": "audio/cg_earth_arrival.wav",
    "repair_drip": "audio/repair_drip.wav",
    "repair_chisel": "audio/repair_chisel.wav",
    "repair_scare": "audio/repair_scare.wav",
}

CG_AUDIO_KEYS = (
    "cg_download_start",
    "cg_download_complete",
    "cg_blood_moon",
    "cg_screen_crack",
    "cg_palace_transition",
    "cg_wugang_axe",
    "cg_yutu_pestle",
    "cg_moon_pool",
    "cg_laurel_roots",
    "cg_earth_arrival",
)


class AudioManager:
    """Small resilient audio layer with one-shot, CG and scene BGM support."""

    BGM_FADE_SECONDS = 0.9
    DEFAULT_BGM_BASE_VOLUME = 0.23
    DEFAULT_BGM_VOLUME_MULTIPLIER = 1.0
    DEFAULT_SFX_VOLUME_MULTIPLIER = 1.0
    # One reserved channel is enough because route switches fade through
    # silence.  Keeping a single physical channel makes overlap impossible,
    # including while sound effects are being emitted.
    BGM_CHANNEL_IDS = (0,)
    VOLUMES = {
        "rule_discovered": 0.18,
        "violation": 0.24,
        "player_died": 0.28,
        "tree_bleeding": 0.22,
        "dialog_open": 0.12,
        "transition_found": 0.26,
        "ambient_moon_palace": 0.10,
        # Route BGM is intentionally stronger than the old 0.16–0.18 values;
        # the user multiplier below still allows it to be reduced or muted.
        "main_menu": DEFAULT_BGM_BASE_VOLUME,
        "home": DEFAULT_BGM_BASE_VOLUME,
        "guanghan_square": DEFAULT_BGM_BASE_VOLUME,
        "guanghan_palace": DEFAULT_BGM_BASE_VOLUME,
        "ending_he": DEFAULT_BGM_BASE_VOLUME,
        "ending_be": DEFAULT_BGM_BASE_VOLUME,
        "cg_download_start": 0.07,
        "cg_download_complete": 0.08,
        "cg_blood_moon": 0.08,
        "cg_screen_crack": 0.09,
        "cg_palace_transition": 0.08,
        "cg_wugang_axe": 0.08,
        "cg_yutu_pestle": 0.07,
        "cg_moon_pool": 0.06,
        "cg_laurel_roots": 0.07,
        "cg_earth_arrival": 0.08,
        "repair_drip": 0.32,
        "repair_chisel": 0.18,
        "repair_scare": 0.84,
    }

    def __init__(self, event_bus: EventBus, mixer=None, settings: Mapping[str, float] | None = None) -> None:
        self.event_bus = event_bus
        self.mixer = mixer or pygame.mixer
        self.enabled = False
        self.sounds = {}
        self.bgm_volume_multiplier = self.DEFAULT_BGM_VOLUME_MULTIPLIER
        self.sfx_volume_multiplier = self.DEFAULT_SFX_VOLUME_MULTIPLIER
        self._ambient_playing = False  # Legacy 5-second ambient compatibility.
        self._bgm_channels = []
        self._bgm_slots = []
        self._bgm_current_slot: int | None = None
        self._bgm_target_key: str | None = None
        self._bgm_transition: dict | None = None
        self._dialog_active = False
        self._cg_active = False
        self._cg_played_tokens: set[str] = set()
        self.set_volume_preferences(
            bgm_volume=(settings or {}).get("bgm_volume", self.DEFAULT_BGM_VOLUME_MULTIPLIER),
            sfx_volume=(settings or {}).get("sfx_volume", self.DEFAULT_SFX_VOLUME_MULTIPLIER),
        )
        self._init_mixer()
        self._load_sounds()
        self._init_bgm_channels()
        self._subscribe()

    def play_transition_found(self) -> None:
        """Play the sting used when the transition figure turns around."""
        self.play("transition_found")

    def play_ambient(self) -> None:
        """Start the legacy ambient bed for older callers and tests.

        The live game uses :meth:`set_bgm` instead; keeping this method avoids
        breaking existing integrations that still request the old 5-second
        ambient file.
        """
        if self._ambient_playing:
            return
        sound = self.sounds.get("ambient_moon_palace")
        if sound is None:
            return
        try:
            sound.play(loops=-1)
            self._ambient_playing = True
        except pygame.error:
            self.enabled = False

    def stop_ambient(self) -> None:
        """Stop legacy ambient and every BGM immediately for reset/menu cleanup."""
        self.stop_legacy_ambient()
        self.stop_bgm(immediate=True)

    def stop_legacy_ambient(self) -> None:
        """Stop only the legacy ambient bed while preserving the selected BGM."""
        sound = self.sounds.get("ambient_moon_palace")
        if sound is not None:
            try:
                sound.stop()
            except pygame.error:
                self.enabled = False
        self._ambient_playing = False

    def sync_for_game_state(self, mode: str, mainline: dict | None = None) -> None:
        """Keep the live BGM aligned with the actual scene and route state."""
        self.set_bgm(select_bgm_for_state(mode, mainline))

    def set_bgm(self, key: str | None, *, fade_seconds: float | None = None) -> None:
        """Start, fade-through-silence, or stop a named BGM without duplicate restarts."""
        if key is not None and key not in BGM_FILES:
            key = None

        if key is not None and key not in self.sounds:
            # A missing requested BGM must never leave a stale route playing.
            self.stop_bgm(immediate=True)
            self._bgm_target_key = key
            return

        if key == self._bgm_target_key:
            return

        self._bgm_target_key = key
        duration = self.BGM_FADE_SECONDS if fade_seconds is None else max(0.0, fade_seconds)
        if self._bgm_current_slot is None:
            if key is None:
                return
            slot = 0
            self._stop_bgm_slot(slot)
            if not self._start_bgm_slot(slot, key):
                self._bgm_target_key = None
                return
            self._bgm_current_slot = slot
            if duration <= 0.0:
                self._set_slot_volume(slot, self._ducked_bgm_volume(key))
                self._bgm_transition = None
            else:
                self._bgm_transition = {
                    "phase": "in",
                    "incoming_key": key,
                    "elapsed": 0.0,
                    "duration": duration,
                }
            return

        if self._bgm_transition is not None and self._bgm_transition["phase"] == "out":
            # Keep the existing fade-out progress, but replace the pending
            # target.  No second sound has started, so repeated route changes
            # cannot create an overlapping stack.
            self._bgm_transition["incoming_key"] = key
            return

        if self._bgm_transition is not None and self._bgm_transition["phase"] == "in":
            # The currently audible track is the only active slot.  Reverse
            # into a new fade-out before any new sound is started.
            self._bgm_transition = {
                "phase": "out",
                "incoming_key": key,
                "elapsed": 0.0,
                "duration": duration,
            }
            return

        if duration <= 0.0:
            self._stop_bgm_slot(self._bgm_current_slot)
            self._bgm_current_slot = None
            if key is not None:
                self.set_bgm(key, fade_seconds=0.0)
            return

        self._bgm_transition = {
            "phase": "out",
            "incoming_key": key,
            "elapsed": 0.0,
            "duration": duration,
        }

    def stop_bgm(self, *, immediate: bool = False) -> None:
        """Stop the current BGM, optionally allowing a short fade-out."""
        if immediate or self._bgm_current_slot is None:
            self._bgm_target_key = None
            self._stop_bgm_slots()
            return
        self._bgm_target_key = None
        if self._bgm_transition is not None and self._bgm_transition["phase"] == "out":
            self._bgm_transition["incoming_key"] = None
            return
        self._bgm_transition = {
            "phase": "out",
            "incoming_key": None,
            "elapsed": 0.0,
            "duration": self.BGM_FADE_SECONDS,
        }

    def update(self, dt: float) -> None:
        """Advance BGM fades while keeping interaction music continuous."""
        transition = self._bgm_transition
        if transition is None:
            if self._bgm_current_slot is not None:
                slot = self._bgm_slots[self._bgm_current_slot]
                if slot["key"] is not None:
                    self._set_slot_volume(
                        self._bgm_current_slot,
                        self._ducked_bgm_volume(slot["key"]),
                    )
            return

        transition["elapsed"] += max(0.0, dt)
        duration = max(1e-6, float(transition["duration"]))
        progress = min(1.0, transition["elapsed"] / duration)
        duck = self._duck_multiplier()
        current = self._bgm_current_slot
        if current is None:
            self._bgm_transition = None
            return

        current_key = self._bgm_slots[current]["key"]
        if current_key is not None:
            if transition["phase"] == "out":
                self._set_slot_volume(current, self._base_bgm_volume(current_key) * (1.0 - progress) * duck)
            else:
                self._set_slot_volume(current, self._base_bgm_volume(current_key) * progress * duck)

        if progress < 1.0:
            return

        if transition["phase"] == "in":
            self._set_slot_volume(current, self._ducked_bgm_volume(current_key))
            self._bgm_transition = None
            return

        # Fade-through-silence: stop before loading the next route.  This is
        # intentionally sequential rather than a crossfade so two BGM files
        # can never play together during a route change.
        self._stop_bgm_slot(current)
        self._bgm_current_slot = None
        next_key = transition.get("incoming_key")
        self._bgm_transition = None
        if next_key is not None:
            # The target was recorded before the fade-out began for
            # de-duplication. Clear it before the actual start so the new
            # single active slot is still created.
            self._bgm_target_key = None
            self.set_bgm(next_key, fade_seconds=duration)

    def bgm_status(self) -> dict:
        """Return observable BGM state for tests and runtime verification."""
        active_key = None
        if self._bgm_current_slot is not None:
            active_key = self._bgm_slots[self._bgm_current_slot]["key"]
        return {
            "enabled": self.enabled,
            "target": self._bgm_target_key,
            "active": active_key,
            "transitioning": self._bgm_transition is not None,
            "bgm_volume": self.bgm_volume_multiplier,
            "sfx_volume": self.sfx_volume_multiplier,
            "loaded": tuple(key for key in BGM_FILES if key in self.sounds),
        }

    def begin_cg_cycle(self) -> None:
        """Clear one-shot bookkeeping and silence any previous CG audio."""
        self.stop_cg_sounds()
        self._cg_active = True
        self._refresh_bgm_ducking()

    def play_cg_cue(self, key: str, *, token: str | None = None) -> None:
        """Play a CG cue once for a sequence boundary."""
        cue_token = token or key
        if cue_token in self._cg_played_tokens:
            return
        self._cg_played_tokens.add(cue_token)
        self.play(key)

    def stop_cg_sounds(self) -> None:
        """Stop all temporary CG one-shots without stopping the BGM."""
        for key in CG_AUDIO_KEYS:
            sound = self.sounds.get(key)
            if sound is None:
                continue
            try:
                sound.stop()
            except pygame.error:
                self.enabled = False
        self._cg_played_tokens.clear()
        self._cg_active = False
        self._refresh_bgm_ducking()

    def play(self, key: str) -> None:
        """Play a named sound effect when available."""
        sound = self.sounds.get(key)
        if sound is None:
            return
        try:
            if key not in BGM_FILES:
                sound.set_volume(self._effective_sound_volume(key))
            sound.play()
        except pygame.error:
            self.enabled = False

    def play_spatial(self, key: str, *, gain: float = 1.0, pan: float = 0.0) -> None:
        """Local one-shots use distance/pan without restarting or ducking the square BGM."""
        sound = self.sounds.get(key)
        if not self.enabled or sound is None:
            return
        try:
            sound.set_volume(self._effective_sound_volume(key))
            channel = sound.play()
            if channel is not None:
                volume = max(0.0, min(1.0, gain))
                pan = max(-1.0, min(1.0, pan))
                channel.set_volume(volume * min(1.0, 1 - pan), volume * min(1.0, 1 + pan))
        except pygame.error:
            self.enabled = False

    def stop_repair_sounds(self) -> None:
        """Stop workshop one-shots at exit, death or load; preserve the BGM channel."""
        for key in ("repair_drip", "repair_chisel", "repair_scare"):
            sound = self.sounds.get(key)
            if sound is not None:
                try:
                    sound.stop()
                except pygame.error:
                    pass

    def set_volume_preferences(
        self,
        *,
        bgm_volume: float | None = None,
        sfx_volume: float | None = None,
    ) -> None:
        """立即应用全局 BGM/SFX 倍率，不重启任何正在播放的声音。"""
        if bgm_volume is not None:
            self.bgm_volume_multiplier = self._clamp_volume(bgm_volume)
        if sfx_volume is not None:
            self.sfx_volume_multiplier = self._clamp_volume(sfx_volume)

        for key, sound in self.sounds.items():
            if key in BGM_FILES:
                continue
            try:
                sound.set_volume(self._effective_sound_volume(key))
            except pygame.error:
                self.enabled = False
        self._refresh_bgm_ducking()

    def set_bgm_volume(self, volume: float) -> None:
        """设置 BGM 用户倍率的便捷接口。"""
        self.set_volume_preferences(bgm_volume=volume)

    def set_sfx_volume(self, volume: float) -> None:
        """设置音效用户倍率的便捷接口。"""
        self.set_volume_preferences(sfx_volume=volume)

    def volume_status(self) -> dict[str, float]:
        """返回当前全局倍率，便于设置菜单和测试观察。"""
        return {
            "bgm_volume": self.bgm_volume_multiplier,
            "sfx_volume": self.sfx_volume_multiplier,
        }

    def _effective_sound_volume(self, key: str) -> float:
        if key in BGM_FILES:
            return self.VOLUMES.get(key, self.DEFAULT_BGM_BASE_VOLUME) * self.bgm_volume_multiplier
        return self.VOLUMES.get(key, 0.4) * self.sfx_volume_multiplier

    @staticmethod
    def _clamp_volume(value: float) -> float:
        if isinstance(value, bool):
            return 1.0
        try:
            value = float(value)
        except (TypeError, ValueError):
            return 1.0
        if not math.isfinite(value):
            return 1.0
        return max(0.0, min(1.0, value))

    def _init_mixer(self) -> None:
        try:
            if not self.mixer.get_init():
                self.mixer.init()
            self.enabled = True
        except pygame.error:
            self.enabled = False

    def _init_bgm_channels(self) -> None:
        """Reserve one mixer channel so BGM cannot overlap regular effects."""
        channel_factory = getattr(self.mixer, "Channel", None)
        if not self.enabled or not callable(channel_factory):
            self._bgm_slots = [
                {"channel": None, "key": None, "sound": None} for _ in self.BGM_CHANNEL_IDS
            ]
            return
        try:
            reserve = getattr(self.mixer, "set_reserved", None)
            if callable(reserve):
                reserve(len(self.BGM_CHANNEL_IDS))
            self._bgm_channels = [channel_factory(channel_id) for channel_id in self.BGM_CHANNEL_IDS]
            for channel in self._bgm_channels:
                channel.stop()
        except pygame.error:
            self._bgm_channels = []
        self._bgm_slots = [
            {
                "channel": self._bgm_channels[index] if index < len(self._bgm_channels) else None,
                "key": None,
                "sound": None,
            }
            for index in range(len(self.BGM_CHANNEL_IDS))
        ]

    def _start_bgm_slot(self, slot_index: int, key: str) -> bool:
        sound = self.sounds.get(key)
        if sound is None:
            return False
        slot = self._bgm_slots[slot_index]
        slot["key"] = key
        slot["sound"] = sound
        try:
            channel = slot["channel"]
            if channel is not None:
                channel.set_volume(0.0)
                channel.play(sound, loops=-1)
            else:
                sound.set_volume(0.0)
                sound.play(loops=-1)
        except pygame.error:
            slot["key"] = None
            slot["sound"] = None
            self.enabled = False
            return False
        return True

    def _stop_bgm_slot(self, slot_index: int) -> None:
        if slot_index >= len(self._bgm_slots):
            return
        slot = self._bgm_slots[slot_index]
        try:
            if slot["channel"] is not None:
                slot["channel"].stop()
            elif slot["sound"] is not None:
                slot["sound"].stop()
        except pygame.error:
            self.enabled = False
        slot["key"] = None
        slot["sound"] = None

    def _stop_bgm_slots(self) -> None:
        for index in range(len(self._bgm_slots)):
            self._stop_bgm_slot(index)
        self._bgm_current_slot = None
        self._bgm_transition = None

    def _base_bgm_volume(self, key: str) -> float:
        return self.VOLUMES.get(key, self.DEFAULT_BGM_BASE_VOLUME) * self.bgm_volume_multiplier

    def _duck_multiplier(self) -> float:
        if self._cg_active:
            return 0.24
        # Dialogue is text-based and has no voice track to protect.  Keep the
        # selected BGM at its normal level instead of making an interaction
        # sound like the music stopped.  The same reserved channel and sound
        # instance continue playing, so neither the track nor its position is
        # restarted when a dialog opens or closes.
        return 1.0

    def _ducked_bgm_volume(self, key: str) -> float:
        return self._base_bgm_volume(key) * self._duck_multiplier()

    def _set_slot_volume(self, slot_index: int, volume: float) -> None:
        if slot_index >= len(self._bgm_slots):
            return
        slot = self._bgm_slots[slot_index]
        if slot["key"] is None:
            return
        try:
            if slot["channel"] is not None:
                slot["channel"].set_volume(max(0.0, min(1.0, volume)))
            elif slot["sound"] is not None:
                slot["sound"].set_volume(max(0.0, min(1.0, volume)))
        except pygame.error:
            self.enabled = False

    def _refresh_bgm_ducking(self) -> None:
        if self._bgm_transition is None:
            if self._bgm_current_slot is not None:
                key = self._bgm_slots[self._bgm_current_slot]["key"]
                if key is not None:
                    self._set_slot_volume(self._bgm_current_slot, self._ducked_bgm_volume(key))
            return
        # update() owns fade ratios; this call only ensures the next frame
        # applies the new ducking state without restarting either sound.

    def _load_sounds(self) -> None:
        if not self.enabled:
            return

        for key, relative_path in AUDIO_FILES.items():
            try:
                sound = self.mixer.Sound(str(asset_path(relative_path)))
                sound.set_volume(self._effective_sound_volume(key))
            except (FileNotFoundError, pygame.error):
                continue
            self.sounds[key] = sound

    def _subscribe(self) -> None:
        self.event_bus.subscribe(RULE_DISCOVERED, self._on_rule_discovered)
        self.event_bus.subscribe(VIOLATION_CHANGED, self._on_violation_changed)
        self.event_bus.subscribe(PLAYER_DIED, self._on_player_died)
        self.event_bus.subscribe(TREE_BLEEDING, self._on_tree_bleeding)
        self.event_bus.subscribe(DIALOG_ACTIVE_CHANGED, self._on_dialog_active_changed)

    def _on_rule_discovered(self, **payload) -> None:
        _ = payload
        self.play("rule_discovered")

    def _on_violation_changed(self, **payload) -> None:
        _ = payload
        self.play("violation")

    def _on_player_died(self, **payload) -> None:
        _ = payload
        self.play("player_died")

    def _on_tree_bleeding(self, **payload) -> None:
        _ = payload
        self.play("tree_bleeding")

    def _on_dialog_active_changed(self, active: bool, **payload) -> None:
        _ = payload
        self._dialog_active = bool(active)
        if active:
            self.play("dialog_open")
        # Do not stop, restart, or fade the BGM for a text interaction.  Keep
        # this refresh for callers using a custom mixer so a prior CG duck is
        # restored immediately when dialogue state changes.
        self._refresh_bgm_ducking()
