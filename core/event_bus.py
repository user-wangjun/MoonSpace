"""轻量事件总线，用于替代 Godot Signal。"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable
from typing import Any


VIOLATION_CHANGED = "violation_changed"
PLAYER_DIED = "player_died"
RULE_DISCOVERED = "rule_discovered"
SHOW_DIALOG = "show_dialog"
DIALOG_CHOICE_SELECTED = "dialog_choice_selected"
TREE_BLEEDING = "tree_bleeding"
YUTU_POUNDING_CHANGED = "yutu_pounding_changed"
DIALOG_ACTIVE_CHANGED = "dialog_active_changed"
HORROR_INTENSITY_CHANGED = "horror_intensity_changed"


class EventBus:
    """基于回调列表的事件总线，降低系统间直接耦合。"""

    def __init__(self) -> None:
        self._subscribers: dict[str, list[Callable[..., None]]] = defaultdict(list)

    def subscribe(self, event_name: str, callback: Callable[..., None]) -> None:
        """注册事件监听，同一回调不会重复注册。"""
        if callback not in self._subscribers[event_name]:
            self._subscribers[event_name].append(callback)

    def unsubscribe(self, event_name: str, callback: Callable[..., None]) -> None:
        """移除事件监听；不存在时静默忽略。"""
        if callback in self._subscribers[event_name]:
            self._subscribers[event_name].remove(callback)

    def emit(self, event_name: str, **payload: Any) -> None:
        """广播事件；复制监听列表以允许回调内修改订阅关系。"""
        for callback in list(self._subscribers.get(event_name, [])):
            callback(**payload)

    def clear(self) -> None:
        """清空所有事件监听，主要用于测试和重启流程。"""
        self._subscribers.clear()


GLOBAL_EVENT_BUS = EventBus()
