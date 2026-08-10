"""Game audio playback bound to event-bus signals."""

from __future__ import annotations

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


AUDIO_FILES = {
    "rule_discovered": "audio/rule_discovered.wav",
    "violation": "audio/violation.wav",
    "player_died": "audio/player_died.wav",
    "tree_bleeding": "audio/tree_bleeding.wav",
    "dialog_open": "audio/dialog_open.wav",
    "transition_found": "audio/transition_found.wav",
    "ambient_moon_palace": "audio/ambient_moon_palace.wav",
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
    """Small resilient audio layer; silently disables itself if mixer is unavailable."""

    VOLUMES = {
        "rule_discovered": 0.18,
        "violation": 0.24,
        "player_died": 0.28,
        "tree_bleeding": 0.22,
        "dialog_open": 0.12,
        "transition_found": 0.26,
        "ambient_moon_palace": 0.10,
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
    }

    def __init__(self, event_bus: EventBus, mixer=None) -> None:
        self.event_bus = event_bus
        self.mixer = mixer or pygame.mixer
        self.enabled = False
        self.sounds = {}
        self._ambient_playing = False
        self._cg_played_tokens: set[str] = set()
        self._init_mixer()
        self._load_sounds()
        self._subscribe()

    def play_transition_found(self) -> None:
        """Play the sting used when the transition figure turns around."""
        self.play("transition_found")

    def play_ambient(self) -> None:
        """Start a quiet looping moon-palace bed if audio is available."""
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
        """停止循环环境音，并允许下次进入场景时重新播放。"""
        sound = self.sounds.get("ambient_moon_palace")
        if sound is not None:
            try:
                sound.stop()
            except pygame.error:
                self.enabled = False
        self._ambient_playing = False

    def begin_cg_cycle(self) -> None:
        """Clear one-shot bookkeeping and silence any previous CG audio."""
        self.stop_cg_sounds()

    def play_cg_cue(self, key: str, *, token: str | None = None) -> None:
        """Play a CG cue once for a sequence boundary."""
        cue_token = token or key
        if cue_token in self._cg_played_tokens:
            return
        self._cg_played_tokens.add(cue_token)
        self.play(key)

    def stop_cg_sounds(self) -> None:
        """Stop all temporary CG one-shots without affecting the ambient bed."""
        for key in CG_AUDIO_KEYS:
            sound = self.sounds.get(key)
            if sound is None:
                continue
            try:
                sound.stop()
            except pygame.error:
                self.enabled = False
        self._cg_played_tokens.clear()

    def play(self, key: str) -> None:
        """Play a named sound effect when available."""
        sound = self.sounds.get(key)
        if sound is None:
            return
        try:
            sound.play()
        except pygame.error:
            self.enabled = False

    def _init_mixer(self) -> None:
        try:
            if not self.mixer.get_init():
                self.mixer.init()
            self.enabled = True
        except pygame.error:
            self.enabled = False

    def _load_sounds(self) -> None:
        if not self.enabled:
            return

        for key, relative_path in AUDIO_FILES.items():
            try:
                sound = self.mixer.Sound(str(asset_path(relative_path)))
                sound.set_volume(self.VOLUMES.get(key, 0.4))
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
        if active:
            self.play("dialog_open")
