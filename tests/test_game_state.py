"""游戏状态测试。"""

from core.event_bus import EventBus, PLAYER_DIED, RULE_DISCOVERED, VIOLATION_CHANGED
from core.game_state import GameState


def test_initial_state_is_clean():
    state = GameState(EventBus())

    assert state.violation_count == 0
    assert state.known_rules == {}
    assert not state.is_dead()


def test_add_violation_increases_count_and_emits_event():
    bus = EventBus()
    state = GameState(bus)
    received = []
    bus.subscribe(VIOLATION_CHANGED, lambda **payload: received.append(payload))

    state.add_violation("rule_bow_to_tree")

    assert state.violation_count == 1
    assert received == [{"count": 1, "rule_id": "rule_bow_to_tree"}]


def test_third_violation_emits_player_died():
    bus = EventBus()
    state = GameState(bus)
    received = []
    bus.subscribe(PLAYER_DIED, lambda **payload: received.append(payload))

    state.add_violation("one")
    state.add_violation("two")
    state.add_violation("three")

    assert state.is_dead()
    assert received == [{"count": 3, "rule_id": "three"}]


def test_add_known_rule_records_rule_and_emits_event():
    bus = EventBus()
    state = GameState(bus)
    received = []
    bus.subscribe(RULE_DISCOVERED, lambda **payload: received.append(payload))

    state.add_known_rule("rule_1", "见树需稽首")

    assert state.known_rules == {"rule_1": "见树需稽首"}
    assert received == [{"rule_id": "rule_1", "rule_text": "见树需稽首"}]


def test_add_known_rule_does_not_emit_when_rule_is_unchanged():
    bus = EventBus()
    state = GameState(bus)
    received = []
    bus.subscribe(RULE_DISCOVERED, lambda **payload: received.append(payload))

    state.add_known_rule("rule_1", "见树需稽首")
    state.add_known_rule("rule_1", "见树需稽首")

    assert received == [{"rule_id": "rule_1", "rule_text": "见树需稽首"}]


def test_reset_clears_state():
    state = GameState(EventBus())
    state.add_violation("rule")
    state.add_known_rule("rule", "text")

    state.reset()

    assert state.violation_count == 0
    assert state.known_rules == {}
    assert not state.is_dead()


def test_reset_violations_preserves_discovered_rules():
    state = GameState(EventBus())
    state.add_violation("rule")
    state.add_known_rule("rule", "text")

    state.reset_violations()

    assert state.violation_count == 0
    assert state.known_rules == {"rule": "text"}
    assert not state.is_dead()


def test_reset_violations_emits_zero_count_for_all_observers():
    bus = EventBus()
    state = GameState(bus)
    received = []
    bus.subscribe(VIOLATION_CHANGED, lambda **payload: received.append(payload))
    state.violation_count = 3

    state.reset_violations()

    assert received == [{"count": 0, "rule_id": "death_restart", "reason": "reset"}]
