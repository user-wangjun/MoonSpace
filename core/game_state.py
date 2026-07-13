"""游戏状态：违规、已发现规则和死亡判定。"""

from __future__ import annotations

from core.event_bus import EventBus, PLAYER_DIED, RULE_DISCOVERED, VIOLATION_CHANGED


class GameState:
    """集中管理游戏状态，避免实体或 UI 各自维护违规次数。"""

    MAX_VIOLATIONS = 3

    def __init__(self, event_bus: EventBus) -> None:
        self.event_bus = event_bus
        self.violation_count = 0
        self.known_rules: dict[str, str] = {}

    def add_violation(self, rule_id: str = "") -> None:
        """增加一次违规，并在达到上限时发出死亡事件。"""
        if self.is_dead():
            return

        self.violation_count += 1
        self.event_bus.emit(
            VIOLATION_CHANGED,
            count=self.violation_count,
            rule_id=rule_id,
        )

        if self.is_dead():
            self.event_bus.emit(
                PLAYER_DIED,
                count=self.violation_count,
                rule_id=rule_id,
            )

    def add_known_rule(self, rule_id: str, rule_text: str) -> None:
        """记录玩家已知规则，并通知 UI 刷新规则手册。"""
        if self.known_rules.get(rule_id) == rule_text:
            return
        self.known_rules[rule_id] = rule_text
        self.event_bus.emit(
            RULE_DISCOVERED,
            rule_id=rule_id,
            rule_text=rule_text,
        )

    def is_dead(self) -> bool:
        """判断玩家是否已经因违规过多死亡。"""
        return self.violation_count >= self.MAX_VIOLATIONS

    def reset(self) -> None:
        """重置状态，用于重新开始游戏。"""
        self.violation_count = 0
        self.known_rules.clear()

    def reset_violations(self) -> None:
        """仅清除违规次数，保留玩家已经学会的规则。"""
        if self.violation_count == 0:
            return
        self.violation_count = 0
        self.event_bus.emit(VIOLATION_CHANGED, count=0, rule_id="death_restart", reason="reset")
