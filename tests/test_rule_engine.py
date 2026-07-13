"""规则引擎测试。"""

from core.event_bus import EventBus
from core.game_state import GameState
from core.rule_engine import RuleEngine


def test_register_and_check_true_rule_passes_when_callback_true():
    state = GameState(EventBus())
    engine = RuleEngine(state)
    engine.register_rule("rule", "desc", lambda context: True)

    assert engine.check_rule("rule", {}) is True
    assert state.violation_count == 0


def test_true_rule_adds_violation_when_callback_false():
    state = GameState(EventBus())
    engine = RuleEngine(state)
    engine.register_rule("rule", "desc", lambda context: False)

    assert engine.check_rule("rule", {}) is False
    assert state.violation_count == 1


def test_pseudo_rule_adds_violation_when_callback_true():
    state = GameState(EventBus())
    engine = RuleEngine(state)
    engine.register_pseudo_rule("pseudo", "desc", lambda context: True)

    assert engine.check_pseudo_rule("pseudo", {}) is False
    assert state.violation_count == 1


def test_pseudo_rule_passes_when_callback_false():
    state = GameState(EventBus())
    engine = RuleEngine(state)
    engine.register_pseudo_rule("pseudo", "desc", lambda context: False)

    assert engine.check_pseudo_rule("pseudo", {}) is True
    assert state.violation_count == 0


def test_unknown_rule_defaults_to_pass():
    state = GameState(EventBus())
    engine = RuleEngine(state)

    assert engine.check_rule("missing", {}) is True
    assert engine.check_pseudo_rule("missing", {}) is True


def test_get_all_rules_returns_true_rule_descriptions():
    state = GameState(EventBus())
    engine = RuleEngine(state)
    engine.register_rule("rule", "真规则", lambda context: True)
    engine.register_pseudo_rule("pseudo", "伪规则", lambda context: False)

    assert engine.get_all_rules() == {"rule": "真规则"}


def test_clear_removes_rules():
    state = GameState(EventBus())
    engine = RuleEngine(state)
    engine.register_rule("rule", "desc", lambda context: False)
    engine.clear()

    assert not engine.has_rule("rule")
    assert engine.check_rule("rule", {}) is True
