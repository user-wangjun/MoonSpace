"""规则引擎：真规则和伪规则的注册与判定。"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from core.game_state import GameState


RuleCallback = Callable[[dict[str, Any]], bool]


@dataclass(frozen=True)
class Rule:
    """规则定义，callback 返回值由规则类型决定如何解释。"""

    rule_id: str
    description: str
    callback: RuleCallback


class RuleEngine:
    """集中处理规则判定，避免玩法规则散落在实体和 UI 中。"""

    def __init__(self, game_state: GameState) -> None:
        self.game_state = game_state
        self._rules: dict[str, Rule] = {}
        self._pseudo_rules: dict[str, Rule] = {}

    def register_rule(
        self,
        rule_id: str,
        description: str,
        check_callback: RuleCallback,
    ) -> None:
        """注册真规则；callback 返回 False 表示玩家违规。"""
        self._rules[rule_id] = Rule(rule_id, description, check_callback)

    def register_pseudo_rule(
        self,
        rule_id: str,
        description: str,
        check_callback: RuleCallback,
    ) -> None:
        """注册伪规则；callback 返回 True 表示玩家踩中陷阱。"""
        self._pseudo_rules[rule_id] = Rule(rule_id, description, check_callback)

    def check_rule(self, rule_id: str, context: dict[str, Any] | None = None) -> bool:
        """检查真规则；未知规则默认放过，降低触发区接线风险。"""
        rule = self._rules.get(rule_id)
        if rule is None:
            return True

        passed = rule.callback(context or {})
        if not passed:
            self.game_state.add_violation(rule_id)
        return passed

    def check_pseudo_rule(
        self,
        rule_id: str,
        context: dict[str, Any] | None = None,
    ) -> bool:
        """检查伪规则；踩中陷阱时返回 False 并增加违规。"""
        rule = self._pseudo_rules.get(rule_id)
        if rule is None:
            return True

        triggered = rule.callback(context or {})
        if triggered:
            self.game_state.add_violation(rule_id)
            return False
        return True

    def has_rule(self, rule_id: str) -> bool:
        """判断真规则是否已注册。"""
        return rule_id in self._rules

    def has_pseudo_rule(self, rule_id: str) -> bool:
        """判断伪规则是否已注册。"""
        return rule_id in self._pseudo_rules

    def get_all_rules(self) -> dict[str, str]:
        """返回所有真规则文案，供规则手册展示。"""
        return {rule_id: rule.description for rule_id, rule in self._rules.items()}

    def clear(self) -> None:
        """清空规则，主要用于测试或重新装载 Demo 规则。"""
        self._rules.clear()
        self._pseudo_rules.clear()
