"""死亡画面测试。"""

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
