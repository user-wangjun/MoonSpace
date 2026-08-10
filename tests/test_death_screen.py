"""死亡画面测试。"""

import pygame

import config
from core.event_bus import EventBus, PLAYER_DIED
from core.game_state import GameState
from ui.death_screen import DeathScreen


class FakeInput:
    def __init__(self, restart=False):
        self.restart = restart

    def was_pressed(self, action):
        return self.restart and action == "restart"


def test_death_screen_opens_on_player_died():
    bus = EventBus()
    state = GameState(bus)
    screen = DeathScreen(bus, state)

    bus.emit(PLAYER_DIED, count=3, rule_id="rule")

    assert screen.active


def test_death_screen_restart_resets_state():
    bus = EventBus()
    state = GameState(bus)
    screen = DeathScreen(bus, state)
    state.add_violation("a")
    bus.emit(PLAYER_DIED, count=3, rule_id="rule")

    restarted = screen.update(0.1, FakeInput(True))

    assert restarted
    assert not screen.active
    assert state.violation_count == 0


def test_death_screen_restart_preserves_discovered_rules():
    bus = EventBus()
    state = GameState(bus)
    screen = DeathScreen(bus, state)
    state.add_known_rule("rule", "已经读过的规条")
    state.violation_count = state.MAX_VIOLATIONS
    bus.emit(PLAYER_DIED, count=3, rule_id="rule")

    screen.update(0.1, FakeInput(True))

    assert state.known_rules == {"rule": "已经读过的规条"}


def test_death_screen_declares_three_formal_violation_shots():
    assert len(DeathScreen.SHOT_ASSETS) == 3
    assert all(path.startswith("sprites/moonspace/cg/death_violation_") for path in DeathScreen.SHOT_ASSETS)


def test_death_screen_uses_independent_1_2_second_shot_clock():
    screen = DeathScreen(EventBus(), GameState(EventBus()))
    screen.active = True

    screen.update(1.2, FakeInput())
    assert screen.current_shot_index(screen.fade_timer) == 1
    assert screen.show_messages is False

    screen.update(1.2, FakeInput())
    assert screen.current_shot_index(screen.fade_timer) == 2
    assert screen.show_messages is True
    assert screen.blackout_alpha == 0


def test_death_screen_d3_persists_and_blackout_reaches_old_max_at_four_seconds():
    screen = DeathScreen(EventBus(), GameState(EventBus()))
    screen.active = True

    finished = screen.update(10.0, FakeInput())

    assert finished is False
    assert screen.fade_timer == DeathScreen.BLACKOUT_MAX_AT
    assert screen.current_shot_index(screen.fade_timer) == 2
    assert screen.blackout_alpha == DeathScreen.BLACKOUT_ALPHA


def test_death_screen_missing_shot_is_safe(monkeypatch):
    screen = DeathScreen(EventBus(), GameState(EventBus()))
    screen.active = True
    screen.fade_timer = 1.2
    monkeypatch.setattr("ui.death_screen.load_image", lambda *_args, **_kwargs: (_ for _ in ()).throw(FileNotFoundError()))

    surface = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT), pygame.SRCALPHA)
    screen.draw(surface)

    assert surface.get_at((0, 0)).a == 255


def test_death_screen_restart_clears_shot_and_blackout_timers():
    bus = EventBus()
    state = GameState(bus)
    screen = DeathScreen(bus, state)
    bus.emit(PLAYER_DIED, count=3, rule_id="rule")
    screen.fade_timer = 3.6

    assert screen.update(0.1, FakeInput(True)) is True
    assert screen.fade_timer == 0.0
    assert screen.active is False
