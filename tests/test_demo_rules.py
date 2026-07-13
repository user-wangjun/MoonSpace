"""Demo 规则测试。"""

import pygame

from core.demo_rules import (
    RULE_BOW_TO_TREE,
    RULE_NO_EYE_CONTACT,
    RULE_POOL_REFLECTION,
    RULE_TEXTS,
    is_facing_rect,
    register_demo_rules,
)
from core.event_bus import EventBus
from core.game_state import GameState
from core.rule_engine import RuleEngine


def test_register_demo_rules_adds_expected_rules():
    state = GameState(EventBus())
    engine = RuleEngine(state)

    register_demo_rules(engine)

    assert engine.has_rule(RULE_BOW_TO_TREE)
    assert len(engine.get_all_rules()) == 4


def test_rule_board_copy_matches_confirmed_laurel_and_yutu_wording():
    assert RULE_TEXTS[RULE_BOW_TO_TREE] == "月桂未见血时，来使不得近。异像现时，方可查验。"
    assert RULE_TEXTS[RULE_NO_EYE_CONTACT] == "玉兔捣药时，不可与之对视。行走于前，恐被其噬。"
    assert RULE_TEXTS[RULE_POOL_REFLECTION] == "月池之水面，不可见使者的影子。凝视月池之久，陟罚自有分晓。"


def test_laurel_proximity_rule_violates_when_too_close():
    state = GameState(EventBus())
    engine = RuleEngine(state)
    register_demo_rules(engine)

    assert engine.check_rule(RULE_BOW_TO_TREE, {"too_close": True}) is False
    assert state.violation_count == 1


def test_is_facing_rect_detects_main_direction():
    source = pygame.Rect(10, 10, 10, 10)
    target_right = pygame.Rect(40, 10, 10, 10)
    target_up = pygame.Rect(10, -30, 10, 10)

    assert is_facing_rect(source, "right", target_right)
    assert is_facing_rect(source, "up", target_up)
    assert not is_facing_rect(source, "left", target_right)
